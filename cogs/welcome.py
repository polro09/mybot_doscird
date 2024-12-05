import discord
from discord.ext import commands
from datetime import datetime
import logging
import json
import os
from typing import Optional

logger = logging.getLogger(__name__)

class WelcomeConfig:
    """입퇴장 시스템 설정을 관리하는 클래스"""
    def __init__(self):
        self.load_config()

    def load_config(self) -> None:
        """config.json에서 설정을 로드합니다."""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.welcome_channel_id = config.get('channels', {}).get('welcome')
                self.log_channel_id = config.get('channels', {}).get('log')
                self.guild_id = config.get('guild_id')
                self.footer_text = "🛡️APS-applied"
                self.welcome_image = "https://i.imgur.com/pLwAVhO.jpeg"
                self.thumbnail_image = "https://i.imgur.com/ftS8Tc1.jpeg"
        except Exception as e:
            logger.error(f"설정 파일 로드 중 오류 발생: {e}")
            self.set_defaults()

    def set_defaults(self) -> None:
        """기본 설정값을 설정합니다."""
        self.welcome_channel_id = None
        self.log_channel_id = None
        self.guild_id = None
        self.footer_text = "🛡️APS-applied"
        self.welcome_image = "https://i.imgur.com/pLwAVhO.jpeg"
        self.thumbnail_image = "https://i.imgur.com/ftS8Tc1.jpeg"

class Welcome(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = WelcomeConfig()
        self.setup_logger()

    def setup_logger(self) -> None:
        """로거를 설정합니다."""
        handler = logging.FileHandler(filename='welcome.log', encoding='utf-8', mode='a')
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    def create_member_embed(self, member: discord.Member, is_join: bool = True) -> discord.Embed:
        """멤버 입/퇴장 임베드를 생성합니다."""
        embed = discord.Embed(
            title="멤버입장" if is_join else "멤버퇴장",
            description=f"{member.mention}님이 서버에 {'입장' if is_join else '퇴장'}하였습니다.",
            color=discord.Color.green() if is_join else discord.Color.red(),
            timestamp=datetime.now()
        )

        # 멤버 정보 필드 추가
        embed.add_field(
            name="📋 유저 정보",
            value=f"```\n"
                  f"유저 ID: {member.id}\n"
                  f"계정 생성일: {member.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                  f"서버 참가일: {member.joined_at.strftime('%Y-%m-%d %H:%M:%S') if member.joined_at else 'N/A'}\n"
                  f"```",
            inline=False
        )

        # 서버 통계 필드 추가
        total_members = len(member.guild.members)
        humans = len([m for m in member.guild.members if not m.bot])
        bots = total_members - humans
        
        embed.add_field(
            name="📊 서버 통계",
            value=f"```\n"
                  f"전체 멤버: {total_members}명\n"
                  f"유저: {humans}명\n"
                  f"봇: {bots}명\n"
                  f"```",
            inline=False
        )

        # 임베드 이미지 설정
        avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
        embed.set_thumbnail(url=avatar_url)
        embed.set_image(url=self.config.welcome_image)

        # 푸터 설정
        embed.set_footer(
            text=f"{self.config.footer_text}",
            icon_url=member.guild.icon.url if member.guild.icon else None
        )

        return embed

    async def send_log(self, member: discord.Member, is_join: bool = True) -> None:
        """입/퇴장 로그를 전송합니다."""
        try:
            channel = await self.get_log_channel(member.guild)
            if channel:
                embed = self.create_member_embed(member, is_join)
                await channel.send(embed=embed)
                logger.info(f"{'입장' if is_join else '퇴장'} 로그 전송 완료 - User: {member}")
        except Exception as e:
            logger.error(f"로그 전송 중 오류 발생: {e}")

    async def get_log_channel(self, guild: discord.Guild) -> Optional[discord.TextChannel]:
        """로그 채널을 반환합니다."""
        channel = guild.get_channel(self.config.log_channel_id)
        if not channel:
            logger.warning(f"로그 채널을 찾을 수 없습니다. Guild: {guild.name}")
            return None
        return channel

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """멤버 입장 이벤트를 처리합니다."""
        try:
            await self.send_log(member, True)
            
            # 환영 메시지 DM 전송 시도
            try:
                welcome_embed = discord.Embed(
                    title="🎉 환영합니다!",
                    description=f"{member.guild.name}에 오신 것을 환영합니다!",
                    color=discord.Color.blue()
                )
                welcome_embed.add_field(
                    name="📌 안내사항",
                    value="• 서버 규칙을 확인해주세요.\n"
                          "• 역할은 자동으로 지급됩니다.\n"
                          "• 문의사항은 티켓을 통해 문의해주세요.",
                    inline=False
                )
                await member.send(embed=welcome_embed)
            except discord.Forbidden:
                logger.info(f"DM 전송 실패 - User: {member}")

        except Exception as e:
            logger.error(f"멤버 입장 처리 중 오류 발생: {e}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        """멤버 퇴장 이벤트를 처리합니다."""
        try:
            await self.send_log(member, False)
        except Exception as e:
            logger.error(f"멤버 퇴장 처리 중 오류 발생: {e}")

    @commands.Cog.listener()
    async def on_error(self, event: str, *args, **kwargs) -> None:
        """에러 이벤트를 처리합니다."""
        logger.error(f"이벤트 처리 중 오류 발생 - Event: {event}", exc_info=True)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Welcome(bot))