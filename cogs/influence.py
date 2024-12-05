import discord
from discord.ext import commands
from discord import app_commands
import json
import datetime
from typing import Optional, List
import asyncio
import os

class 영향력뷰(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="영향력 기부", style=discord.ButtonStyle.primary, custom_id="기부_버튼")
    async def 기부_버튼(self, interaction: discord.Interaction, button: discord.ui.Button):
        임베드 = discord.Embed(
            title="영향력 기부",
            description="영향력을 입력하고 이미지 파일을 첨부해주세요 (최대 5개):",
            color=discord.Color.blue()
        )
        임베드.set_thumbnail(url="https://i.imgur.com/ftS8Tc1.jpeg")
        await interaction.response.send_message(embed=임베드, ephemeral=True)
        
        def 확인(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id
        
        try:
            메시지 = await interaction.client.wait_for('message', timeout=300.0, check=확인)
            
            try:
                금액 = int(메시지.content)
                if 금액 <= 0:
                    raise ValueError
                
                첨부파일 = []
                for 첨부 in 메시지.attachments:
                    if len(첨부파일) >= 5:
                        break
                    if 첨부.content_type.startswith('image/'):
                        첨부파일.append(await 첨부.to_file())
                
                사용자_id = str(interaction.user.id)
                
                try:
                    with open('영향력_데이터.json', 'r', encoding='utf-8') as f:
                        데이터 = json.load(f)
                except FileNotFoundError:
                    데이터 = {}
                
                if 사용자_id not in 데이터:
                    데이터[사용자_id] = {"총액": 0, "기부내역": []}
                
                데이터[사용자_id]["총액"] += 금액
                데이터[사용자_id]["기부내역"].append({
                    "금액": 금액,
                    "날짜": datetime.datetime.now().isoformat()
                })
                
                with open('영향력_데이터.json', 'w', encoding='utf-8') as f:
                    json.dump(데이터, f, indent=4, ensure_ascii=False)
                
                로그_임베드 = discord.Embed(
    title="영향력 기부",
    description=f"{interaction.user.mention}님이 {금액} 영향력을 기부하셨습니다!",
    color=discord.Color.green()
)

                로그_임베드.add_field(
    name="사용자 ID",
    value=f"`{interaction.user.id}`",
    inline=True
)

                로그_임베드.add_field(
    name="총 기부량",
    value=f"`{데이터[사용자_id]['총액']}`",
    inline=True
)

                로그_임베드.set_author(
    name="영향력 기부",
    icon_url="https://cdn3.emoji.gg/emojis/2122-approved-check-box.gif"
)

                로그_임베드.set_thumbnail(url=interaction.user.display_avatar.url)
                로그_임베드.set_footer(
                 text="정보가 DB에 저장되었습니다",
                 icon_url="https://cdn3.emoji.gg/emojis/62096-bot.png"
                    )
                
                로그채널 = interaction.guild.get_channel(interaction.client.config['channels']['influence_log'])
                await 로그채널.send(embed=로그_임베드, files=첨부파일)
                
                성공_임베드 = discord.Embed(
                    title="영향력 기부 완료",
                    description="영향력 기부가 완료되었습니다.",
                    color=discord.Color.green()
                )
                성공_임베드.set_thumbnail(url="https://i.imgur.com/ftS8Tc1.jpeg")
                await interaction.followup.send(embed=성공_임베드, ephemeral=True)
                
            except ValueError:
                실패_임베드 = discord.Embed(
                    title="오류",
                    description="올바른 숫자를 입력해주세요.",
                    color=discord.Color.red()
                )
                실패_임베드.set_thumbnail(url="https://i.imgur.com/ftS8Tc1.jpeg")
                await interaction.followup.send(embed=실패_임베드, ephemeral=True)
            
            await 메시지.delete()
            
        except asyncio.TimeoutError:
            시간초과_임베드 = discord.Embed(
                title="시간 초과",
                description="시간이 초과되었습니다. 다시 시도해주세요.",
                color=discord.Color.red()
            )
            시간초과_임베드.set_thumbnail(url="https://i.imgur.com/ftS8Tc1.jpeg")
            await interaction.followup.send(embed=시간초과_임베드, ephemeral=True)
    
    @discord.ui.button(label="영향력 순위", style=discord.ButtonStyle.primary, custom_id="순위_버튼")
    async def 순위_버튼(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        try:
            with open('영향력_데이터.json', 'r', encoding='utf-8') as f:
                데이터 = json.load(f)
        except FileNotFoundError:
            데이터없음_임베드 = discord.Embed(
                title="데이터 없음",
                description="아직 기부 내역이 없습니다.",
                color=discord.Color.red()
            )
            데이터없음_임베드.set_thumbnail(url="https://i.imgur.com/ftS8Tc1.jpeg")
            await interaction.followup.send(embed=데이터없음_임베드, ephemeral=True)
            return
        
        정렬된_사용자 = sorted(데이터.items(), key=lambda x: x[1]['총액'], reverse=True)
        검색자_순위 = next((idx + 1 for idx, (유저_id, _) in enumerate(정렬된_사용자) 
                if 유저_id == str(interaction.user.id)), 0)

        순위_임베드 = discord.Embed(
    title="영향력 순위",
    description=f"당신의 순위: {검색자_순위}위" if 검색자_순위 > 0 else "아직 기부 내역이 없습니다",
    color=discord.Color.blue()
)
        순위_임베드.set_thumbnail(url="https://i.imgur.com/ftS8Tc1.jpeg")
        
        for 순위, (사용자_id, 정보) in enumerate(정렬된_사용자, 1):
            사용자 = interaction.guild.get_member(int(사용자_id))
            if 사용자:
                순위_임베드.add_field(
                    name=f"{순위}위: {사용자.display_name}",
                    value=f"총 영향력: {정보['총액']}",
                    inline=False
                )
        
        try:
            await interaction.user.send(embed=순위_임베드)
            
            DM_성공_임베드 = discord.Embed(
                title="DM 전송 완료",
                description="DM으로 순위를 전송했습니다.",
                color=discord.Color.green()
            )
            DM_성공_임베드.set_thumbnail(url="https://i.imgur.com/ftS8Tc1.jpeg")
            await interaction.followup.send(embed=DM_성공_임베드, ephemeral=True)
            
        except discord.Forbidden:
            DM_실패_임베드 = discord.Embed(
                title="DM 전송 실패",
                description="DM을 보낼 수 없습니다. DM을 허용해주세요.",
                color=discord.Color.red()
            )
            DM_실패_임베드.set_thumbnail(url="https://i.imgur.com/ftS8Tc1.jpeg")
            await interaction.followup.send(embed=DM_실패_임베드, ephemeral=True)
    
    @discord.ui.button(label="영향력 검색", style=discord.ButtonStyle.primary, custom_id="검색_버튼")
    async def 검색_버튼(self, interaction: discord.Interaction, button: discord.ui.Button):
        검색_임베드 = discord.Embed(
            title="영향력 검색",
            description="검색할 서버 별명을 입력해주세요:",
            color=discord.Color.blue()
        )
        검색_임베드.set_thumbnail(url="https://i.imgur.com/ftS8Tc1.jpeg")
        await interaction.response.send_message(embed=검색_임베드, ephemeral=True)
        
        def 확인(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id
        
        try:
            메시지 = await interaction.client.wait_for('message', timeout=60.0, check=확인)
            검색_별명 = 메시지.content
            
            try:
                with open('영향력_데이터.json', 'r', encoding='utf-8') as f:
                    데이터 = json.load(f)
            except FileNotFoundError:
                데이터없음_임베드 = discord.Embed(
                    title="데이터 없음",
                    description="아직 기부 내역이 없습니다.",
                    color=discord.Color.red()
                )
                데이터없음_임베드.set_thumbnail(url="https://i.imgur.com/ftS8Tc1.jpeg")
                await interaction.followup.send(embed=데이터없음_임베드, ephemeral=True)
                await 메시지.delete()
                return
            
            찾은_사용자 = None
            for 멤버 in interaction.guild.members:
                if 멤버.display_name == 검색_별명:
                    찾은_사용자 = 멤버
                    break
            
            if 찾은_사용자 and str(찾은_사용자.id) in 데이터:
                사용자_데이터 = 데이터[str(찾은_사용자.id)]
                검색결과_임베드 = discord.Embed(
    title=f"{검색_별명}의 영향력 정보",
    description=f"총 영향력: {사용자_데이터['총액']}",
    color=discord.Color.blue()
)
                검색결과_임베드.set_thumbnail(url=interaction.user.display_avatar.url)  # 검색한 사람의 프로필
                검색결과_임베드.set_author(
    name="영향력 검색",
    icon_url="https://i.imgur.com/ftS8Tc1.jpeg"
)
                검색결과_임베드.set_footer(
    text="정보가 DB에서 조회되었습니다",
    icon_url="https://i.imgur.com/ftS8Tc1.jpeg"
)
                
                최근_기부 = sorted(사용자_데이터['기부내역'], 
                               key=lambda x: x['날짜'], 
                               reverse=True)[:5]
                
                for 기부 in 최근_기부:
                    날짜 = datetime.datetime.fromisoformat(기부['날짜']).strftime('%Y-%m-%d %H:%M')
                    검색결과_임베드.add_field(
                        name=f"기부 내역",
                        value=f"금액: {기부['금액']}\n날짜: {날짜}",
                        inline=False
                    )
                
                try:
                    await interaction.user.send(embed=검색결과_임베드)
                    
                    DM_성공_임베드 = discord.Embed(
                        title="DM 전송 완료",
                        description="DM으로 검색 결과를 전송했습니다.",
                        color=discord.Color.green()
                    )
                    DM_성공_임베드.set_thumbnail(url="https://i.imgur.com/ftS8Tc1.jpeg")
                    await interaction.followup.send(embed=DM_성공_임베드, ephemeral=True)
                    
                except discord.Forbidden:
                    DM_실패_임베드 = discord.Embed(
                        title="DM 전송 실패",
                        description="DM을 보낼 수 없습니다. DM을 허용해주세요.",
                        color=discord.Color.red()
                    )
                    DM_실패_임베드.set_thumbnail(url="https://i.imgur.com/ftS8Tc1.jpeg")
                    await interaction.followup.send(embed=DM_실패_임베드, ephemeral=True)
            else:
                검색실패_임베드 = discord.Embed(
                    title="검색 실패",
                    description="해당 별명의 사용자를 찾을 수 없거나 기부 내역이 없습니다.",
                    color=discord.Color.red()
                )
                검색실패_임베드.set_thumbnail(url="https://i.imgur.com/ftS8Tc1.jpeg")
                await interaction.followup.send(embed=검색실패_임베드, ephemeral=True)
            
            await 메시지.delete()
            
        except asyncio.TimeoutError:
            시간초과_임베드 = discord.Embed(
                title="시간 초과",
                description="시간이 초과되었습니다. 다시 시도해주세요.",
                color=discord.Color.red()
            )
            시간초과_임베드.set_thumbnail(url="https://i.imgur.com/ftS8Tc1.jpeg")
            await interaction.followup.send(embed=시간초과_임베드, ephemeral=True)

class 영향력(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(영향력뷰())
    
    @commands.command(name="영향력")
    async def 영향력_명령어(self, ctx):
        if ctx.channel.id != self.bot.config['channels']['influence']:
            return
            
        임베드 = discord.Embed(
            title="영향력 시스템",
            description="아래 버튼을 눌러 원하는 기능을 사용하세요.",
            color=discord.Color.blue()
        )
        임베드.add_field(
            name="영향력 기부",
            value="영향력을 기부하고 이미지를 첨부할 수 있습니다. (최대 5개)",
            inline=False
        )
        임베드.add_field(
           name="영향력 순위",
           value="현재 영향력 순위 TOP 10을 확인할 수 있습니다.",
           inline=False
        )
        임베드.add_field(
           name="영향력 검색",
           value="특정 사용자의 영향력 기부 내역을 검색할 수 있습니다.",
           inline=False
        )
        임베드.set_thumbnail(url="https://i.imgur.com/ftS8Tc1.jpeg")
        임베드.set_image(url="https://i.imgur.com/pLwAVhO.jpeg")
       
        뷰 = 영향력뷰()
        await ctx.send(embed=임베드, view=뷰)

async def setup(bot):
   await bot.add_cog(영향력(bot))