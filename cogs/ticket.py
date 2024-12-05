import discord
from discord.ext import commands
from discord import ui
import json
import asyncio
import os
from datetime import datetime
import logging
from typing import Dict, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TicketConfig:
    """티켓 시스템 설정을 관리하는 클래스"""
    category_id: int
    channel_id: int
    admin_role_ids: List[int]
    mention_roles: List[int]
    admin_channel_id: int
    max_tickets: int = 3
    auto_close_hours: int = 72
    require_reason: bool = True
    
    @classmethod
    def load_from_file(cls) -> 'TicketConfig':
        """config.json에서 설정을 로드합니다."""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                ticket_config = config.get('ticket', {})
                
                return cls(
                    category_id=ticket_config.get('category_id'),
                    channel_id=ticket_config.get('channel_id'),
                    admin_role_ids=config.get('roles', {}).get('admin', []),
                    mention_roles=config.get('roles', {}).get('admin', []),
                    admin_channel_id=config.get('channels', {}).get('admin'),
                    max_tickets=ticket_config.get('settings', {}).get('max_tickets_per_user', 3),
                    auto_close_hours=ticket_config.get('settings', {}).get('auto_close_after', 72),
                    require_reason=ticket_config.get('settings', {}).get('require_reason', True)
                )
        except Exception as e:
            logger.error(f"설정 파일 로드 중 오류 발생: {e}")
            return cls(0, 0, [], [], 0)

class TicketView(discord.ui.View):
    """티켓 생성 버튼을 포함한 View"""
    def __init__(self, config: TicketConfig):
        super().__init__(timeout=None)
        self.config = config

    @discord.ui.button(
        label="🎫 티켓 생성",
        style=discord.ButtonStyle.primary,
        custom_id="create_ticket_button"
    )
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            # 기존 티켓 확인
            existing_ticket = discord.utils.get(
                interaction.guild.channels,
                name=f"ticket-{interaction.user.id}"
            )
            
            if existing_ticket:
                await interaction.response.send_message("이미 생성된 티켓이 있습니다!", ephemeral=True)
                return

            # 티켓 채널 생성
            category = interaction.guild.get_channel(self.config.category_id)
            
            # 권한 설정
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }

            # 관리자 역할 권한 추가
            for role_id in self.config.admin_role_ids:
                role = interaction.guild.get_role(role_id)
                if role:
                    overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

            # 채널 생성
            channel = await interaction.guild.create_text_channel(
                name=f"ticket-{interaction.user.id}",
                category=category,
                overwrites=overwrites
            )

            await interaction.response.send_message(f"티켓이 생성되었습니다! {channel.mention}", ephemeral=True)
            
            # 초기 메시지 전송
            embed = discord.Embed(
                title="🎫 티켓 정보",
                description=(
                    "아래 버튼을 통해 원하시는 작업을 진행해주세요.\n\n"
                    "📜 **길드 규칙**: 길드 규칙을 확인하고 동의해주세요.\n"
                    "🗳️ **가입 신청**: 길드 가입 신청서를 작성합니다.\n"
                    "🔔 **관리자 호출**: 문의사항이 있으시다면 관리자를 호출해주세요.\n"
                    "🛡️ **APC 등록**: 관리자용 APC 등록 기능입니다."
                ),
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )

            embed.add_field(name="📋 티켓 정보", value=f"개설자: {interaction.user.mention}", inline=False)
            embed.add_field(
                name="⚠️ 주의사항",
                value=(
                    "• 하나의 티켓에서는 하나의 문의만 진행해주세요.\n"
                    "• 문의가 완료되면 티켓은 자동으로 닫힙니다.\n"
                    "• 불필요한 티켓 생성은 제재될 수 있습니다."
                ),
                inline=False
            )

            embed.set_thumbnail(url="https://i.imgur.com/ftS8Tc1.jpeg")
            embed.set_image(url="https://i.imgur.com/pLwAVhO.jpeg")
            embed.set_footer(text=f"티켓 ID: {interaction.user.id}")

            await channel.send(embed=embed, view=TicketControlView(self.config))

        except Exception as e:
            logger.error(f"티켓 생성 중 오류 발생: {e}")
            await interaction.response.send_message("티켓 생성 중 오류가 발생했습니다.", ephemeral=True)

class TicketControlView(discord.ui.View):
    """티켓 컨트롤 버튼을 포함한 View"""
    def __init__(self, config: TicketConfig):
        super().__init__(timeout=None)
        self.config = config

    @discord.ui.button(
        label="📜 길드 규칙",
        style=discord.ButtonStyle.primary,
        custom_id="show_rules_button"
    )
    async def show_rules(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            embed = discord.Embed(
                title="📜 길드 규칙",
                description="아래 내용을 주의 깊게 읽어보시고 동의 버튼을 눌러주세요.",
                color=discord.Color.blue()
            )

            # 규칙 섹션 추가
            sections = {
                "1️⃣ 기본 규칙": [
                    "• BO Mod 기본 규칙을 읽어주세요.",
                    "ㄴ https://discordapp.com/channels/755719544990990376/756161552113074256",
                    "• 길드원간 상호 존중과 예의를 지켜주세요.",
                    "• 과도한 비하, 모욕, 차별적 발언은 금지됩니다.",
                    "• 다른 길드원의 게임 플레이를 방해하는 행위는 금지됩니다.",
                    "• 길드 채팅에서는 건전한 언어 사용을 해주세요."
                ],
                "2️⃣ 길드 활동": [
                    "• 주간 길드 활동 최대한 참여.",
                    "• 길드 공지사항은 반드시 확인해주세요.",
                    "• 길드 모의전/이벤트 불참 시 사전 통보 필수",
                    "• 장기간(7일 이상) 미접속 시 사전 공지 필요",
                    "• 불법프로그램 사용은 엄격히 금지됩니다."
                ],
                "3️⃣ 분배 규칙": [
                    "• 레이드 보상은 킬수에 따라 자동 분배",
                    "• 교역소 아이템은 길드 공지된 규칙에 따라 분배",
                    "• 사냥 과정에서 문제 발생 시 길드마스터/운영진 중재"
                ],
                "4️⃣ 징계 규정": [
                    "• 1차 위반: 경고",
                    "• 2차 위반: 길드 활동 1주일 정지",
                    "• 3차 위반: 길드 추방",
                    "• 심각한 규정 위반은 즉시 추방될 수 있음"
                ],
                "5️⃣ 보안 규정": [
                    "• 길드 내부 정보 유출 금지",
                    "• 길드원 개인정보 보호",
                    "• 길드 전략과 전술의 외부 유출 금지",
                    "• 타 길드와의 기밀 정보 교환 금지"
                ],
                "6️⃣ 탈퇴 규정": [
                    "• 탈퇴 시 최소 3일 전 운영진에게 통보",
                    "• 길드 자원 아이템 반환",
                    "• 무단 탈퇴 시 재가입 불가",
                    "• 탈퇴 후 길드 기밀 유지 의무"
                ],
                "⚠️ 주의사항": [
                    "위 규칙은 길드의 원활한 운영과 모든 길드원의 즐거운 게임 플레이를 위해 만들어졌습니다.",
                    "규칙 위반 시 경고없이 강퇴될 수 있으며, 규칙은 운영진의 판단에 따라 수정될 수 있습니다."
                ]
            }

            for title, rules in sections.items():
                embed.add_field(name=title, value="\n".join(rules), inline=False)

            embed.set_footer(text="규칙에 동의하시려면 아래 '동의' 버튼을 클릭해주세요.")
            await interaction.response.send_message(embed=embed, view=RuleConsentView(), ephemeral=True)
            
        except Exception as e:
            logger.error(f"규칙 표시 중 오류 발생: {e}")
            await interaction.response.send_message("규칙을 표시하는 중 오류가 발생했습니다.", ephemeral=True)

    @discord.ui.button(
        label="🗳️ 가입 신청",
        style=discord.ButtonStyle.primary,
        custom_id="application_form_button"
    )
    async def application_form(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplicationModal())

    @discord.ui.button(
        label="🔔 관리자 호출",
        style=discord.ButtonStyle.primary,
        custom_id="call_admin_button"
    )
    async def call_admin(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            admin_channel = interaction.guild.get_channel(self.config.admin_channel_id)
            if not admin_channel:
                raise ValueError("관리자 채널을 찾을 수 없습니다.")

            mentions = " ".join([f"<@&{role_id}>" for role_id in self.config.admin_role_ids])
            
            # 관리자 채널에 보내는 임베드
            admin_embed = discord.Embed(
                title="🔔 관리자 호출",
                description=f"{mentions}",  # 역할 멘션은 여기에만 포함
                color=discord.Color.yellow(),
                timestamp=datetime.now()
            )
            
            admin_embed.add_field(name="호출자", value=f"{interaction.user.mention}", inline=True)
            admin_embed.add_field(name="호출 채널", value=interaction.channel.mention, inline=True)
            
            admin_embed.set_thumbnail(url=interaction.user.display_avatar.url)
            admin_embed.set_footer(text=f"호출자 ID: {interaction.user.id}")

            # 임베드만 전송
            await admin_channel.send("@here", embed=admin_embed, allowed_mentions=discord.AllowedMentions(everyone=True, roles=True))

            # 호출자에게 보내는 임베드
            user_embed = discord.Embed(
                title="✅ 관리자 호출 완료",
                description="관리자 게시판에 멘션을 전송하였습니다.",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            user_embed.set_thumbnail(url="https://i.imgur.com/ftS8Tc1.jpeg")
            
            await interaction.response.send_message(embed=user_embed, ephemeral=True)

        except Exception as e:
            logger.error(f"관리자 호출 중 오류 발생: {e}")
            await interaction.response.send_message("관리자 호출 중 오류가 발생했습니다.", ephemeral=True)

    @discord.ui.button(
        label="🛡️ APC 등록",
        style=discord.ButtonStyle.secondary,
        custom_id="apc_register_button"
    )
    async def apc_register(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if not any(role.id in self.config.admin_role_ids for role in interaction.user.roles):
                await interaction.response.send_message("관리자만 사용할 수 있는 기능입니다.", ephemeral=True)
                return

            await interaction.response.send_modal(APCRegistrationModal())
        except Exception as e:
            logger.error(f"APC 등록 중 오류 발생: {e}")
            await interaction.response.send_message("APC 등록 중 오류가 발생했습니다.", ephemeral=True)

class RuleConsentView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="✅동의",
        style=discord.ButtonStyle.primary,
        custom_id="consent_rules_button"
    )
    async def consent_rules(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            embed = discord.Embed(
                title="✅규칙 동의 완료",
                description=f"{interaction.user.mention}님이 규칙에 동의하셨습니다.",
                color=discord.Color.green()
            )
            embed.set_thumbnail(url="https://imgur.com/xZCJWZR.gif")
            await interaction.channel.send(embed=embed)
            await interaction.response.defer(ephemeral=True)
        except Exception as e:
            logger.error(f"규칙 동의 처리 중 오류 발생: {e}")
            await interaction.response.send_message("규칙 동의 처리 중 오류가 발생했습니다.", ephemeral=True)

class ApplicationModal(ui.Modal, title="가입 신청서"):
    """가입 신청서 모달"""
    nickname = ui.TextInput(
        label="인게임 닉네임",
        placeholder="인게임 캐릭터 닉네임을 입력해주세요"
    )
    bannerlord_exp = ui.TextInput(
        label="배너로드 싱글/멀티 유경험 및 플레이타임",
        placeholder="배너로드 싱글/멀티 숙련도와 플레이타임을 적어주세요",
        style=discord.TextStyle.paragraph
    )
    online_exp = ui.TextInput(
        label="배너로드 온라인 유경험 및 플레이타임",
        placeholder="온라인 모드 숙련도와 플레이타임을 적어주세요",
        style=discord.TextStyle.paragraph
    )
    preference = ui.TextInput(
        label="PVE/PVP 선호도",
        placeholder="PVE 또는 PVP 중 선호하는 클랜을 입력해주세요"
    )
    character_id = ui.TextInput(
        label="메인 캐릭터 고유번호",
        placeholder="메인 캐릭터의 고유번호를 입력해주세요"
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # 제출 완료 메시지
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="✅ 신청서 제출 완료",
                    description="가입 신청서가 성공적으로 제출되었습니다.",
                    color=discord.Color.green()
                ),
                ephemeral=True
            )

            # 신청서 내용 임베드 생성
            application_embed = discord.Embed(
                title="📝가입 신청서",
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            # 신청자 정보 추가
            application_embed.add_field(name="신청자", value=f"{interaction.user.mention}", inline=True)
            
            # TextInput 필드들 추가
            fields = {
                self.nickname.label: self.nickname.value,
                self.bannerlord_exp.label: self.bannerlord_exp.value,
                self.online_exp.label: self.online_exp.value,
                self.preference.label: self.preference.value,
                self.character_id.label: self.character_id.value
            }
            
            for label, value in fields.items():
                application_embed.add_field(name=label, value=value, inline=False)
            
            # 디스코드 정보 추가
            application_embed.add_field(
                name="디스코드 정보",
                value=f"ID: {interaction.user.id}\n태그: {str(interaction.user)}",
                inline=False
            )
            
            application_embed.set_thumbnail(url=interaction.user.display_avatar.url)
            
            # 신청서 내용 채널에 전송
            await interaction.channel.send(embed=application_embed)

            # 신청서 파일로 저장
            await self.save_application(interaction, fields)

        except Exception as e:
            logger.error(f"신청서 제출 중 오류 발생: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "⚠️ 신청서 제출 중 오류가 발생했습니다. 다시 시도해주세요.",
                        ephemeral=True
                    )
            except:
                pass

    async def save_application(self, interaction: discord.Interaction, fields: Dict[str, str]):
        """신청서를 파일로 저장합니다."""
        if not os.path.exists('APC_info'):  # 'applications'에서 'APC_info'로 변경
            os.makedirs('APC_info')

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"APC_info/application_{interaction.user.id}_{timestamp}.txt"  # 경로 수정

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"가입 신청서 - {datetime.now()}\n\n")
            f.write(f"디스코드 ID: {interaction.user.id}\n")
            f.write(f"디스코드 태그: {interaction.user}\n\n")
            f.write("=== 신청서 내용 ===\n\n")
            for label, value in fields.items():
                f.write(f"{label}:\n{value}\n\n")

class APCRegistrationModal(ui.Modal):
    def __init__(self) -> None:
        super().__init__(title="APC 인증 등록")
        self.discord_id = ui.TextInput(
            label="디스코드 고유번호",
            placeholder="등록할 유저의 디스코드 ID를 입력하세요"
        )
        self.character_id = ui.TextInput(
            label="캐릭터 고유번호",
            placeholder="등록할 캐릭터의 고유번호를 입력하세요"
        )
        self.add_item(self.discord_id)
        self.add_item(self.character_id)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            discord_id = self.discord_id.value
            character_id = self.character_id.value

            # APC 정보를 개별 파일로 저장
            if not os.path.exists('apc_database'):
                os.makedirs('apc_database')

            # 현재 시간을 파일명에 포함
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"apc_database/apc_verification_{discord_id}_{timestamp}.txt"

            try:
                # 디스코드 ID로 멤버 찾기
                member = await interaction.guild.fetch_member(int(discord_id))
                if member:
                    # 지정된 역할 부여
                    verified_roles = [1305056915969015838, 1227130582665007135]
                    roles_added = []
                    
                    for role_id in verified_roles:
                        role = interaction.guild.get_role(role_id)
                        if role:
                            await member.add_roles(role)
                            roles_added.append(role.name)

                    # 파일에 상세 정보 저장
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"=== APC 인증 정보 ===\n\n")
                        f.write(f"인증 일시: {datetime.now()}\n")
                        f.write(f"인증 처리자: {interaction.user} ({interaction.user.id})\n\n")
                        f.write(f"=== 유저 정보 ===\n")
                        f.write(f"디스코드 ID: {discord_id}\n")
                        f.write(f"디스코드 태그: {member}\n")
                        f.write(f"캐릭터 ID: {character_id}\n\n")
                        f.write(f"=== 서버 정보 ===\n")
                        f.write(f"서버명: {interaction.guild.name}\n")
                        f.write(f"서버 ID: {interaction.guild.id}\n")
                        f.write(f"\n=== 부여된 역할 ===\n")
                        for role_name in roles_added:
                            f.write(f"- {role_name}\n")

                    embed = discord.Embed(
                        title="🛡️ APC 등록 완료",
                        description=(
                            f"디스코드 ID: {discord_id}\n"
                            f"캐릭터 ID: {character_id}\n"
                            f"부여된 역할: {', '.join(roles_added)}\n"
                            f"대상 유저: {member.mention}"
                        ),
                        color=discord.Color.green()
                    )

                    # 유저에게 DM 보내기
                    try:
                        user_embed = discord.Embed(
                            title="🛡️ APC 인증 완료",
                            description=f"APC 인증이 완료되어 다음 역할이 부여되었습니다:\n{', '.join(roles_added)}",
                            color=discord.Color.green()
                        )
                        await member.send(embed=user_embed)
                    except discord.Forbidden:
                        pass  # DM을 보낼 수 없는 경우 무시

                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    
                else:
                    raise ValueError("해당 유저를 찾을 수 없습니다.")
                    
            except ValueError as ve:
                await interaction.response.send_message(
                    f"⚠️ 오류: {str(ve)}",
                    ephemeral=True
                )
            except Exception as e:
                await interaction.response.send_message(
                    "⚠️ 역할 부여 중 오류가 발생했습니다.",
                    ephemeral=True
                )
                logger.error(f"역할 부여 중 오류: {e}")
                
        except Exception as e:
            logger.error(f"APC 등록 중 오류 발생: {e}")
            try:
                await interaction.response.send_message(
                    "⚠️ APC 등록 중 오류가 발생했습니다. 다시 시도해주세요.",
                    ephemeral=True
                )
            except:
                try:
                    await interaction.followup.send(
                        "⚠️ APC 등록 중 오류가 발생했습니다. 다시 시도해주세요.",
                        ephemeral=True
                    )
                except:
                    pass

class Ticket(commands.Cog):
    """티켓 시스템을 관리하는 Cog"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = TicketConfig.load_from_file()
        self.setup_views()
        
        # 로깅 설정
        if not os.path.exists('logs'):
            os.makedirs('logs')
        handler = logging.FileHandler('logs/ticket.log', encoding='utf-8', mode='a')
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    def setup_views(self):
        """영구적인 View들을 설정합니다."""
        self.bot.add_view(TicketView(self.config))
        self.bot.add_view(TicketControlView(self.config))
        self.bot.add_view(RuleConsentView())

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setup_ticket(self, ctx: commands.Context):
        """티켓 시스템을 설정합니다."""
        try:
            embed = discord.Embed(
                title="🎫 티켓 시스템",
                description=(
                    "가입 신청 및 문의사항을 처리할 수 있습니다.\n\n\n"
                    "**버튼을 클릭하면 아래 기능을 이용할 수 있습니다.**\n"
                    "• 📜길드 규칙 확인 및 동의\n"
                    "• 🗳️길드 가입 신청서 작성\n"
                    "• 🔔관리자 호출\n\n"
                    "**🎫티켓 생성** 버튼을 눌러 티켓을 생성하세요."
                ),
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="📌 안내사항",
                value=(
                    "• 각 유저당 하나의 티켓만 생성할 수 있습니다.\n"
                    "• 티켓은 문의 완료 후 자동으로 닫힙니다.\n"
                    "• 불필요한 **🎫티켓 생성**은 제재될 수 있습니다."
                ),
                inline=False
            )

            embed.set_thumbnail(url="https://i.imgur.com/ftS8Tc1.jpeg")
            embed.set_image(url="https://i.imgur.com/pLwAVhO.jpeg")
            embed.set_footer(text="🛡️APS-applied")

            await ctx.send(embed=embed, view=TicketView(self.config))
            await ctx.message.delete()

        except Exception as e:
            logger.error(f"티켓 시스템 설정 중 오류 발생: {e}")
            await ctx.send("⚠️ 티켓 시스템 설정 중 오류가 발생했습니다.", delete_after=5)

async def setup(bot: commands.Bot):
    await bot.add_cog(Ticket(bot))