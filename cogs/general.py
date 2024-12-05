import discord
from discord.ext import commands
import platform
import logging
import os
from datetime import datetime
from typing import Dict, Optional

if not os.path.exists('logs'):
    os.makedirs('logs')

logger = logging.getLogger(__name__)
handler = logging.FileHandler('logs/general.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class General(commands.Cog):
    """일반적인 유틸리티 명령어를 제공하는 Cog"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = datetime.now()

    def get_system_info(self) -> dict:
        """시스템 정보를 수집"""
        return {
            'python_version': platform.python_version(),
            'discord_version': discord.__version__,
            'os': f"{platform.system()} {platform.release()}"
        }

    def get_bot_stats(self) -> dict:
        """봇 통계를 수집"""
        return {
            'guild_count': len(self.bot.guilds),
            'user_count': sum(g.member_count for g in self.bot.guilds),
            'command_count': len(self.bot.commands)
        }

    def format_uptime(self) -> str:
        """업타임을 포맷팅"""
        uptime = datetime.now() - self.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}시간 {minutes}분 {seconds}초"

    @commands.hybrid_command(
        name="핑",
        description="봇의 지연시간을 확인합니다"
    )
    async def ping(self, ctx: commands.Context):
        try:
            latency = round(self.bot.latency * 1000)
            color = discord.Color.green() if latency < 100 else discord.Color.yellow() if latency < 200 else discord.Color.red()
            
            embed = discord.Embed(title="🏓 퐁!", color=color, timestamp=datetime.now())
            embed.add_field(name="지연시간", value=f"```{latency}ms```")
            embed.add_field(name="상태", value="🟢 정상" if latency < 100 else "🟡 보통" if latency < 200 else "🔴 지연")
            
            await ctx.send(embed=embed)
            logger.info(f"Ping 명령어 사용됨 - User: {ctx.author}, Latency: {latency}ms")
            
        except Exception as e:
            logger.error(f"Ping 명령어 오류: {e}")
            await ctx.send("⚠️ 명령어 실행 중 오류가 발생했습니다.")

    @commands.hybrid_command(
        name="정보",
        description="봇의 상세 정보를 확인합니다"
    )
    async def info(self, ctx: commands.Context):
        try:
            sys_info = self.get_system_info()
            bot_stats = self.get_bot_stats()
            
            embed = discord.Embed(
                title="🤖 봇 정보",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )

            embed.add_field(
                name="📊 시스템 정보",
                value=f"```\n"
                      f"Python: {sys_info['python_version']}\n"
                      f"Discord.py: {sys_info['discord_version']}\n"
                      f"OS: {sys_info['os']}\n"
                      f"```",
                inline=False
            )

            embed.add_field(
                name="📈 봇 통계",
                value=f"```\n"
                      f"서버 수: {bot_stats['guild_count']}\n"
                      f"총 유저 수: {bot_stats['user_count']}\n"
                      f"명령어 수: {bot_stats['command_count']}\n"
                      f"```",
                inline=False
            )

            embed.add_field(
                name="⏰ 업타임",
                value=f"```\n{self.format_uptime()}\n```",
                inline=False
            )

            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            
            await ctx.send(embed=embed)
            logger.info(f"Info 명령어 사용됨 - User: {ctx.author}")
            
        except Exception as e:
            logger.error(f"Info 명령어 오류: {e}")
            await ctx.send("⚠️ 명령어 실행 중 오류가 발생했습니다.")

async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))