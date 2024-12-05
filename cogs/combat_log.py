# combat_log.py
import discord
from datetime import datetime

class CombatLogger:
    def __init__(self, bot):
        self.bot = bot
        self.log_channel_id = bot.config['combat_system']['channels']['combat_logs']

    async def log_interaction(self, interaction, action):
        """상호작용 로깅"""
        log_channel = self.bot.get_channel(self.log_channel_id)
        
        colors = {
            "참가": discord.Color.green(),
            "대기": discord.Color.blue(),
            "불참": discord.Color.red(),
            "default": discord.Color.orange()
        }
        
        color = next((v for k, v in colors.items() if k in action.lower()), colors["default"])

        embed = discord.Embed(
            title="📋 **모의전 로그**",
            description=f"{interaction.user.mention}님이 {action}",
            color=color,
            timestamp=datetime.utcnow()
        )
        
        if interaction.user.avatar:
            embed.set_thumbnail(url=interaction.user.avatar.url)
                
        embed.add_field(name="유저 ID", value=str(interaction.user.id), inline=True)
        embed.add_field(name="유저 이름", value=interaction.user.display_name, inline=True)
        embed.add_field(name="수행 작업", value=action, inline=False)

        await log_channel.send(embed=embed)