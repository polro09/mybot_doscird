from typing import Callable, Any, Optional, Union
import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import json
import os
from datetime import datetime

class PersistentView(View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

class TimeSelect(Select):
    def __init__(self) -> None:
        options = [
            discord.SelectOption(label=f"{hour:02d}:00", value=str(hour))
            for hour in range(24)
        ]
        
        super().__init__(
            placeholder="시작 시간을 선택하세요",
            min_values=1,
            max_values=1,
            options=options
        )

class CombatButtons:
    def __init__(self, combat: Any) -> None:
        self.combat = combat

    def create_buttons(self, host: Optional[Union[discord.Member, commands.Context]]) -> PersistentView:
        view = PersistentView()

        async def check_host(interaction: discord.Interaction) -> bool:
            if not host:
                return True
            if isinstance(host, commands.Context):
                return interaction.user.id == host.author.id
            return interaction.user.id == host.id

        # 시간 선택 드롭다운
        time_select = TimeSelect()
        time_select.custom_id = "time_select"
        
        async def time_select_callback(interaction: discord.Interaction):
            if not await check_host(interaction):
                await interaction.response.send_message("시간 설정은 개최자만 가능합니다.", ephemeral=True)
                return

            selected_hour = int(time_select.values[0])
            self.combat.start_time = datetime.now().replace(hour=selected_hour, minute=0, second=0, microsecond=0)
            await self.combat.update_status()
            await interaction.response.send_message(f"시작 시간이 {selected_hour:02d}:00으로 설정되었습니다.", ephemeral=True)
            await self.combat.logger.log_interaction(interaction, f"시작 시간을 {selected_hour:02d}:00로 설정")

        time_select.callback = time_select_callback
        view.add_item(time_select)

        # 참가 버튼
        join_button = Button(label="📥참가", style=discord.ButtonStyle.green, custom_id="join_button")
        
        async def join_callback(interaction: discord.Interaction):
            user_id = interaction.user.id
            
            select_view = PersistentView()
            select_menu = Select(
                placeholder="병종을 선택하세요",
                options=[
                    discord.SelectOption(label="🏹 궁병", value="궁병"),
                    discord.SelectOption(label="🛡️ 모루", value="모루"),
                    discord.SelectOption(label="⚔️ 망치", value="망치"),
                    discord.SelectOption(label="🐎 기병", value="기병"),
                    discord.SelectOption(label="🏇 궁기병", value="궁기병"),
                ],
                custom_id="class_select"
            )

            async def select_callback(interaction: discord.Interaction):
                selected_class = select_menu.values[0]
                # 먼저 이전 상태 제거
                self.combat.change_status(user_id, "참가자")
                # 새로운 상태 추가
                self.combat.participants["참가자"][user_id] = selected_class
                await interaction.response.edit_message(content=f"병종 선택 완료: {selected_class}", view=None)
                await self.combat.update_status()
                await self.combat.logger.log_interaction(interaction, f"참가 신청 - {selected_class} 선택")

            select_menu.callback = select_callback
            select_view.add_item(select_menu)
            await interaction.response.send_message("병종을 선택하세요:", view=select_view, ephemeral=True)

        join_button.callback = join_callback
        view.add_item(join_button)
# 대기 버튼
        wait_button = Button(label="⏳대기", style=discord.ButtonStyle.blurple, custom_id="wait_button")
        
        async def wait_callback(interaction: discord.Interaction):
            user_id = interaction.user.id
            self.combat.change_status(user_id, "대기자")
            self.combat.participants["대기자"].append(user_id)
            await self.combat.update_status()
            await interaction.response.send_message("대기자로 등록되었습니다.", ephemeral=True)
            await self.combat.logger.log_interaction(interaction, "대기 신청")

        wait_button.callback = wait_callback
        view.add_item(wait_button)

        # 불참 버튼
        absent_button = Button(label="🚫불참", style=discord.ButtonStyle.red, custom_id="absent_button")
        
        async def absent_callback(interaction: discord.Interaction):
            user_id = interaction.user.id
            self.combat.change_status(user_id, "불참자")
            self.combat.participants["불참자"].append(user_id)
            await self.combat.update_status()
            await interaction.response.send_message("불참자로 등록되었습니다.", ephemeral=True)
            await self.combat.logger.log_interaction(interaction, "불참 신청")

        absent_button.callback = absent_callback
        view.add_item(absent_button)

        # 팀 생성 버튼
        team_button = Button(label="👥팀생성", style=discord.ButtonStyle.primary, custom_id="team_button")
        
        async def team_callback(interaction: discord.Interaction):
            if not await check_host(interaction):
                await interaction.response.send_message("이 버튼은 개최자만 사용할 수 있습니다.", ephemeral=True)
                return

            if not self.combat.participants["참가자"]:
                await interaction.response.send_message("참가자가 없습니다.", ephemeral=True)
                return

            dropdown_view = PersistentView()
            dropdown_menu = Select(
                placeholder="팀에 추가할 참가자를 선택하세요",
                options=[
                    discord.SelectOption(
                        label=interaction.guild.get_member(user_id).display_name,
                        value=str(user_id)
                    ) for user_id in self.combat.participants["참가자"]
                ],
                custom_id="team_member_select"
            )

            async def dropdown_callback(interaction: discord.Interaction):
                selected_user_id = int(dropdown_menu.values[0])
                selected_user = interaction.guild.get_member(selected_user_id)

                team_select_view = PersistentView()
                team_menu = Select(
                    placeholder="팀을 선택하세요",
                    options=[
                        discord.SelectOption(label="팀 1", value="팀1"),
                        discord.SelectOption(label="팀 2", value="팀2"),
                    ],
                    custom_id="team_select"
                )

                async def team_select_callback(interaction: discord.Interaction):
                    selected_team = team_menu.values[0]

                    if selected_user_id in self.combat.participants["팀1"] and selected_team == "팀2":
                        self.combat.participants["팀1"].remove(selected_user_id)
                    elif selected_user_id in self.combat.participants["팀2"] and selected_team == "팀1":
                        self.combat.participants["팀2"].remove(selected_user_id)

                    if selected_user_id not in self.combat.participants[selected_team]:
                        self.combat.participants[selected_team].append(selected_user_id)
                    
                    await self.combat.update_status()
                    user_class = self.combat.participants["참가자"].get(selected_user_id, "알 수 없음")
                    emoji = self.combat.get_class_emoji(user_class)
                    await interaction.response.send_message(
                        f"{emoji} {selected_user.mention}님이 **{selected_team}**에 추가되었습니다.",
                        ephemeral=True
                    )
                    await self.combat.logger.log_interaction(interaction, f"{selected_user.display_name}님을 {selected_team}에 추가")

                team_menu.callback = team_select_callback
                team_select_view.add_item(team_menu)
                await interaction.response.send_message(
                    f"{selected_user.display_name}님을 어느 팀에 추가하시겠습니까?",
                    view=team_select_view,
                    ephemeral=True
                )

            dropdown_menu.callback = dropdown_callback
            dropdown_view.add_item(dropdown_menu)
            await interaction.response.send_message(
                "팀에 추가할 참가자를 선택하세요:",
                view=dropdown_view,
                ephemeral=True
            )

        team_button.callback = team_callback
        view.add_item(team_button)
        # 알림 버튼
        notify_button = Button(label="🔔알림", style=discord.ButtonStyle.gray, custom_id="notify_button")
        
        async def notify_callback(interaction: discord.Interaction):
            if not await check_host(interaction):
                await interaction.response.send_message("알림 전송은 개최자만 가능합니다.", ephemeral=True)
                return

            sent_count = 0
            for category in ["참가자", "대기자", "불참자"]:
                users = self.combat.participants[category]
                if isinstance(users, dict):
                    users = users.keys()
                
                for user_id in users:
                    user = interaction.guild.get_member(user_id)
                    if user:
                        try:
                            confirm_view = self.create_confirm_buttons()
                            embed = discord.Embed(
                                title="⚔️ 모의전 참가 상태 확인",
                                description=(
                                    "**모의전 참가 상태를 확인해주세요!**\n\n"
                                    "🔹 현재 모의전 참가 신청이 진행중입니다.\n"
                                    "🔹 아래 버튼을 클릭하여 최종 참가 상태를 결정해주세요.\n"
                                    "🔹 상태 변경 시 기존 선택은 자동으로 취소됩니다.\n\n"
                                    "✨ **버튼 설명**\n"
                                    "📥 **참가**: 모의전에 참여합니다.\n"
                                    "⏳ **대기**: 대기자 명단에 등록됩니다.\n"
                                    "🚫 **불참**: 불참 의사를 표시합니다.\n\n"
                                    "💡 **참고사항**\n"
                                    "• 선택하신 상태는 실시간으로 반영됩니다.\n"
                                    "• 상태 확정 시 초록색 확인 표시(🟢)가 나타납니다."
                                ),
                                color=discord.Color.blue(),
                                timestamp=datetime.utcnow()
                            )
                            
                            embed.set_thumbnail(url="https://i.imgur.com/ftS8Tc1.jpeg")
                            embed.set_image(url="https://i.imgur.com/pLwAVhO.jpeg")
                            
                            # 현재 상태 표시
                            current_status = "미정"
                            if user_id in self.combat.participants["참가자"]:
                                current_status = f"참가 ({self.combat.participants['참가자'][user_id]})"
                            elif user_id in self.combat.participants["대기자"]:
                                current_status = "대기"
                            elif user_id in self.combat.participants["불참자"]:
                                current_status = "불참"
                                
                            embed.add_field(
                                name="🎯 현재 상태",
                                value=f"**{current_status}**",
                                inline=False
                            )
                            
                            await user.send(embed=embed, view=confirm_view)
                            sent_count += 1
                        except discord.Forbidden:
                            continue

            await interaction.response.send_message(f"확인 메시지가 {sent_count}명에게 전송되었습니다.", ephemeral=True)
            await self.combat.logger.log_interaction(interaction, "참가 확인 알림 전송")

        notify_button.callback = notify_callback
        view.add_item(notify_button)

        # 정보 저장 버튼
        info_button = Button(label="💾정보", style=discord.ButtonStyle.gray, custom_id="info_button")
        
        async def info_callback(interaction: discord.Interaction):
            modal = CombatInfoModal(self.combat)
            await interaction.response.send_modal(modal)

        info_button.callback = info_callback
        view.add_item(info_button)

        # 종료 버튼
        end_button = Button(label="🔚종료", style=discord.ButtonStyle.danger, custom_id="end_button")
        
        async def end_callback(interaction: discord.Interaction):
            if not await check_host(interaction):
                await interaction.response.send_message("종료는 개최자만 가능합니다.", ephemeral=True)
                return
                
            self.combat.is_ended = True
            await self.combat.update_status()
            await interaction.response.send_message("모의전이 종료되었습니다.", ephemeral=True)
            await self.combat.logger.log_interaction(interaction, "모의전 종료")

        end_button.callback = end_callback
        view.add_item(end_button)

        return view

    def create_confirm_buttons(self):
        view = PersistentView()
        
        async def button_callback(interaction: discord.Interaction, status: str):
            user_id = interaction.user.id
            self.combat.change_status(user_id, status)
            
            if status == "참가자":
                select_view = PersistentView()
                select_menu = Select(
                    placeholder="병종을 선택하세요",
                    options=[
                        discord.SelectOption(label="🏹 궁병", value="궁병"),
                        discord.SelectOption(label="🛡️ 모루", value="모루"),
                        discord.SelectOption(label="⚔️ 망치", value="망치"),
                        discord.SelectOption(label="🐎 기병", value="기병"),
                        discord.SelectOption(label="🏇 궁기병", value="궁기병"),
                    ],
                    custom_id="class_select"
                )

                async def select_callback(interaction):
                    selected_class = select_menu.values[0]
                    self.combat.participants["참가자"][user_id] = selected_class
                    self.combat.confirmed_users.add(user_id)
                    await self.combat.update_status()
                    await interaction.response.edit_message(
                        content=f"✅ 참가가 확정되었습니다! 선택한 병종: {selected_class}",
                        view=None,
                        embed=None
                    )
                    await self.combat.logger.log_interaction(interaction, f"DM 확인 - 참가 확정 ({selected_class})")

                select_menu.callback = select_callback
                select_view.add_item(select_menu)
                await interaction.response.send_message("병종을 선택하세요:", view=select_view, ephemeral=True)
            else:
                if status == "대기자":
                    self.combat.participants["대기자"].append(user_id)
                else:  # 불참자
                    self.combat.participants["불참자"].append(user_id)
                    
                self.combat.confirmed_users.add(user_id)
                await self.combat.update_status()
                await interaction.response.edit_message(
                    content=f"✅ {status}로 확정되었습니다!",
                    view=None,
                    embed=None
                )
                await self.combat.logger.log_interaction(interaction, f"DM 확인 - {status} 확정")

        join_button = Button(label="📥참가", style=discord.ButtonStyle.green, custom_id="join_confirm")
        wait_button = Button(label="⏳대기", style=discord.ButtonStyle.blurple, custom_id="wait_confirm")
        absent_button = Button(label="🚫불참", style=discord.ButtonStyle.red, custom_id="absent_confirm")

        join_button.callback = lambda i: button_callback(i, "참가자")
        wait_button.callback = lambda i: button_callback(i, "대기자")
        absent_button.callback = lambda i: button_callback(i, "불참자")

        view.add_item(join_button)
        view.add_item(wait_button)
        view.add_item(absent_button)
        
        return view

class CombatInfoModal(discord.ui.Modal, title="전적 정보 입력"):
    def __init__(self, combat):
        super().__init__()
        self.combat = combat
        
        self.kills = discord.ui.TextInput(label="킬", placeholder="킬 수를 입력하세요")
        self.result = discord.ui.TextInput(label="승패", placeholder="승리/패배를 입력하세요")
        self.class_type = discord.ui.TextInput(label="병종", placeholder="사용한 병종을 입력하세요")
        
        self.add_item(self.kills)
        self.add_item(self.result)
        self.add_item(self.class_type)

    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        filename = f"db/user/{user_id}.txt"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        data = {}
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}
        
        if 'matches' not in data:
            data['matches'] = []
        
        match_info = {
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'kills': self.kills.value,
            'result': self.result.value,
            'class_type': self.class_type.value
        }
        
        data['matches'].append(match_info)
        data['total_matches'] = len(data['matches'])
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        await interaction.response.send_message("전적이 저장되었습니다!", ephemeral=True)
        await self.combat.logger.log_interaction(
            interaction, 
            f"전적 정보 저장 - 킬: {self.kills.value}, 결과: {self.result.value}, 병종: {self.class_type.value}"
        )
