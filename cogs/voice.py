import discord
from discord.ext import commands
import json
import asyncio
from datetime import datetime
import os
import logging
from typing import Dict, Optional

if not os.path.exists('logs'):
    os.makedirs('logs')

logger = logging.getLogger(__name__)
handler = logging.FileHandler('logs/voice.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class VoiceChannel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_channels = {}
        self.channel_update_cooldown = {}
        self.load_config()

    def load_config(self):
        try:
            with open(os.path.join(os.path.dirname(__file__), '..', 'config.json'), 'r', encoding='utf-8') as f:
                self.config = json.load(f)
                self.lobby_channel_id = self.config['voice']['lobby_channel_id']
                self.category_id = self.config['voice']['category_id']
                self.settings = self.config['voice']['settings']
        except Exception as e:
            logger.error(f"설정 파일 로드 중 오류: {e}")
            self.config = {}
            self.lobby_channel_id = None
            self.category_id = None
            self.settings = {
                "max_channels": 10,
                "channel_limit": 5,
                "afk_timeout": 300
            }

    async def update_channel_name(self, channel: discord.VoiceChannel, new_name: str) -> bool:
        try:
            current_time = datetime.now().timestamp()
            last_update = self.channel_update_cooldown.get(channel.id, 0)
            
            if current_time - last_update < 5:
                return False
                
            await channel.edit(name=new_name)
            self.channel_update_cooldown[channel.id] = current_time
            return True
        except Exception as e:
            logger.error(f"채널 이름 업데이트 중 오류: {e}")
            return False

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        try:
            if after.channel and after.channel.id == self.lobby_channel_id:
                category = self.bot.get_channel(self.category_id)
                if category:
                    channel_name = f"🔊︱{member.display_name}의 채널"
                    overwrites = {
                        member.guild.default_role: discord.PermissionOverwrite(connect=True),
                        member: discord.PermissionOverwrite(connect=True, manage_channels=True, move_members=True)
                    }
                    
                    new_channel = await category.create_voice_channel(
                        name=channel_name,
                        overwrites=overwrites,
                        user_limit=50
                    )
                    
                    await member.move_to(new_channel)
                    self.voice_channels[new_channel.id] = {
                        "owner": member.id,
                        "created_at": datetime.now()
                    }
                    
                    await self.send_initial_message(member, new_channel)

            if before.channel and before.channel.id in self.voice_channels:
                if len(before.channel.members) == 0:
                    await asyncio.sleep(5)
                    if len(before.channel.members) == 0:
                        await before.channel.delete()
                        del self.voice_channels[before.channel.id]
                        if before.channel.id in self.channel_update_cooldown:
                            del self.channel_update_cooldown[before.channel.id]

        except Exception as e:
            logger.error(f"음성 채널 관리 중 오류: {e}")

    async def send_initial_message(self, member: discord.Member, channel: discord.VoiceChannel):
        try:
            embed = discord.Embed(
                title="🎉 통화방이 생성되었습니다!",
                description=(
                    f"채널 주인: {member.mention}\n"
                    f"채널 제한 인원: 50명\n\n"
                    "채널 관리 명령어:\n"
                    "🔒 `!잠금` - 채널을 잠급니다\n"
                    "🔓 `!잠금해제` - 채널 잠금을 해제합니다\n"
                    "✏️ `!이름 [새이름]` - 채널 이름을 변경합니다\n\n"
                    "**명령어는 봇 DM에서 사용해주세요.**"
                ),
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"채널 ID: {channel.id}")
            embed.set_thumbnail(url=member.display_avatar.url)
            
            await member.send(embed=embed)
        except discord.Forbidden:
            logger.warning(f"Cannot send DM to {member}")
            try:
                await channel.send(f"{member.mention}, DM을 보낼 수 없습니다. DM을 허용해주세요!", delete_after=10)
            except:
                pass

    @commands.command()
    async def 잠금(self, ctx: commands.Context):
        try:
            member = None
            voice_channel = None
            
            for guild in self.bot.guilds:
                member = guild.get_member(ctx.author.id)
                if member and member.voice and member.voice.channel:
                    voice_channel = member.voice.channel
                    break

            if not voice_channel:
                await ctx.send("음성 채널에 접속해있지 않습니다!")
                return

            if voice_channel.id not in self.voice_channels or self.voice_channels[voice_channel.id]["owner"] != ctx.author.id:
                await ctx.send("자신의 통화방만 잠글 수 있습니다!")
                return

            await voice_channel.set_permissions(voice_channel.guild.default_role, connect=False)
            new_name = f"🔒︱{voice_channel.name.split('︱', 1)[1] if '︱' in voice_channel.name else voice_channel.name}"
            name_updated = await self.update_channel_name(voice_channel, new_name)

            embed = discord.Embed(
                title="🔒 채널 잠금",
                description="채널이 잠겼습니다.",
                color=discord.Color.red()
            )
            embed.add_field(name="서버", value=voice_channel.guild.name, inline=True)
            embed.add_field(name="채널", value=new_name, inline=True)
            if not name_updated:
                embed.add_field(
                    name="⚠️ 주의",
                    value="채널 이름 변경은 잠시 후에 가능합니다.",
                    inline=False
                )
            embed.set_thumbnail(url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"채널 잠금 중 오류: {e}")
            await ctx.send(f"오류가 발생했습니다: {str(e)}")

    @commands.command()
    async def 잠금해제(self, ctx: commands.Context):
        try:
            member = None
            voice_channel = None
            
            for guild in self.bot.guilds:
                member = guild.get_member(ctx.author.id)
                if member and member.voice and member.voice.channel:
                    voice_channel = member.voice.channel
                    break

            if not voice_channel:
                await ctx.send("음성 채널에 접속해있지 않습니다!")
                return

            if voice_channel.id not in self.voice_channels or self.voice_channels[voice_channel.id]["owner"] != ctx.author.id:
                await ctx.send("자신의 통화방만 잠금 해제할 수 있습니다!")
                return

            await voice_channel.set_permissions(voice_channel.guild.default_role, connect=True)
            new_name = f"🔊︱{voice_channel.name.split('︱', 1)[1] if '︱' in voice_channel.name else voice_channel.name}"
            name_updated = await self.update_channel_name(voice_channel, new_name)

            embed = discord.Embed(
                title="🔓 채널 잠금 해제",
                description="채널 잠금이 해제되었습니다.",
                color=discord.Color.green()
            )
            embed.add_field(name="서버", value=voice_channel.guild.name, inline=True)
            embed.add_field(name="채널", value=new_name, inline=True)
            if not name_updated:
                embed.add_field(
                    name="⚠️ 주의",
                    value="채널 이름 변경은 잠시 후에 가능합니다.",
                    inline=False
                )
            embed.set_thumbnail(url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"채널 잠금 해제 중 오류: {e}")
            await ctx.send(f"오류가 발생했습니다: {str(e)}")

    @commands.command()
    async def 이름(self, ctx: commands.Context, *, new_name: str):
        try:
            member = None
            voice_channel = None
            
            for guild in self.bot.guilds:
                member = guild.get_member(ctx.author.id)
                if member and member.voice and member.voice.channel:
                    voice_channel = member.voice.channel
                    break

            if not voice_channel:
                await ctx.send("음성 채널에 접속해있지 않습니다!")
                return

            if voice_channel.id not in self.voice_channels or self.voice_channels[voice_channel.id]["owner"] != ctx.author.id:
                await ctx.send("자신의 통화방만 이름을 변경할 수 있습니다!")
                return

            is_locked = voice_channel.name.startswith("🔒")
            prefix = "🔒︱" if is_locked else "🔊︱"
            new_channel_name = f"{prefix}{new_name}"
            name_updated = await self.update_channel_name(voice_channel, new_channel_name)

            embed = discord.Embed(
                title="✏️ 채널 이름 변경",
                description="채널 이름이 변경되었습니다.",
                color=discord.Color.blue()
            )
            embed.add_field(name="서버", value=voice_channel.guild.name, inline=True)
            embed.add_field(name="채널", value=new_channel_name, inline=True)
            if not name_updated:
                embed.add_field(
                    name="⚠️ 주의",
                    value="채널 이름 변경은 잠시 후에 가능합니다.",
                    inline=False
                )
            embed.set_thumbnail(url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"채널 이름 변경 중 오류: {e}")
            await ctx.send(f"오류가 발생했습니다: {str(e)}")

async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceChannel(bot))