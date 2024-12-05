import discord
from discord.ext import commands
import wavelink
import asyncio
import logging
import os
import datetime
from typing import Optional
from config import MESSAGES, WAVELINK_CONFIG

if not os.path.exists('logs'):
    os.makedirs('logs')

logger = logging.getLogger(__name__)
handler = logging.FileHandler('logs/music.log', encoding='utf-8', mode='a')
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = {}
        self.now_playing = {}
        self.volume = {}

    def get_queue(self, guild_id: int) -> list:
        if guild_id not in self.queue:
            self.queue[guild_id] = []
        return self.queue[guild_id]

    def get_volume(self, guild_id: int) -> float:
        if guild_id not in self.volume:
            self.volume[guild_id] = 1.0
        return self.volume[guild_id]

    async def send_now_playing(self, guild: discord.Guild, track: wavelink.Playable):
        embed = discord.Embed(
            title="🎵 현재 재생 중",
            description=f"[{track.title}]({track.uri})",
            color=discord.Color.blue()
        )
        
        duration = str(datetime.timedelta(seconds=int(track.length)))
        embed.add_field(name="길이", value=duration, inline=True)
        embed.add_field(name="신청자", value=track.requester.mention if hasattr(track, 'requester') else "Unknown", inline=True)
        
        text_channel = discord.utils.get(guild.text_channels, name="음악-봇")
        if not text_channel:
            text_channel = await guild.create_text_channel("음악-봇")
        await text_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, player: wavelink.Player, track: wavelink.Playable):
        guild_id = player.guild.id
        self.now_playing[guild_id] = track
        await self.send_now_playing(player.guild, track)

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player: wavelink.Player, track: wavelink.Playable, reason: str):
        guild_id = player.guild.id
        queue = self.get_queue(guild_id)

        if queue:
            next_track = queue.pop(0)
            await player.play(next_track)
        elif guild_id in self.now_playing:
            del self.now_playing[guild_id]

    @commands.command(name="입장", aliases=["join", "j"])
    async def join(self, ctx: commands.Context):
        try:
            if not ctx.author.voice:
                await ctx.send(MESSAGES['NOT_IN_VOICE'])
                return

            channel = ctx.author.voice.channel
            player = await channel.connect(cls=wavelink.Player)
            await player.set_volume(100)
            await ctx.send(MESSAGES['JOINED'].format(channel.name))

        except Exception as e:
            logger.error(f"입장 명령어 오류: {e}")
            await ctx.send(MESSAGES['ERROR'].format(str(e)))

    @commands.command(name="재생", aliases=["play", "p"])
    async def play(self, ctx: commands.Context, *, query: str):
        """음악 재생"""
        try:
            if not ctx.author.voice:
                await ctx.send(MESSAGES['NOT_IN_VOICE'])
                return

            if not ctx.voice_client:
                await ctx.invoke(self.join)
            
            player = ctx.voice_client

            try:
                # URL 처리
                if 'youtube.com' in query or 'youtu.be' in query:
                    # 재생목록 제거
                    query = query.split('&')[0]
                    query = query.split('?')[0]
                else:
                    # 검색어인 경우
                    query = f'ytsearch:{query}'

                # 트랙 로드
                tracks = await wavelink.Pool.fetch_tracks(query)
                if not tracks:
                    await ctx.send(MESSAGES['NO_RESULTS'])
                    return

                track = tracks[0]
                track.requester = ctx.author

                if player.playing:
                    self.queue[ctx.guild.id].append(track)
                    await ctx.send(MESSAGES['ADDED_TO_QUEUE'].format(track.title))
                else:
                    await player.play(track)
                    self.now_playing[ctx.guild.id] = track
                    await ctx.send(MESSAGES['NOW_PLAYING'].format(track.title))

            except Exception as e:
                logger.error(f"트랙 검색 중 오류: {e}")
                raise Exception(f"트랙 검색 실패: {e}")

        except Exception as e:
            logger.error(f"재생 명령어 오류: {e}")
            await ctx.send(MESSAGES['ERROR'].format(str(e)))

    @commands.command(name="재생", aliases=["play", "p"])
    async def play(self, ctx: commands.Context, *, query: str):
        """음악 재생"""
        try:
            if not ctx.author.voice:
                await ctx.send(MESSAGES['NOT_IN_VOICE'])
                return

            if not ctx.voice_client:
                await ctx.invoke(self.join)
            
            player = ctx.voice_client

            # URL 또는 검색어 처리
            if not any(s in query for s in ['youtube.com', 'youtu.be']):
                search_query = f"ytsearch:{query}"
            else:
                search_query = query.split('&')[0].split('?')[0]

            tracks = await wavelink.Pool.fetch_tracks(search_query)
            if not tracks:
                await ctx.send(MESSAGES['NO_RESULTS'])
                return

            track = tracks[0]
            track.requester = ctx.author

            if player.playing:
                self.queue[ctx.guild.id].append(track)
                await ctx.send(MESSAGES['ADDED_TO_QUEUE'].format(track.title))
            else:
                await player.play(track)
                await ctx.send(MESSAGES['NOW_PLAYING'].format(track.title))

        except Exception as e:
            logger.error(f"재생 명령어 오류: {e}")
            await ctx.send(MESSAGES['ERROR'].format(str(e)))

    @commands.command(name="스킵", aliases=["skip", "s"])
    async def skip(self, ctx: commands.Context):
        try:
            player = ctx.voice_client
            if not player:
                await ctx.send(MESSAGES['NOT_CONNECTED'])
                return

            if player.playing:
                await player.stop()
                await ctx.send(MESSAGES['SKIP_SUCCESS'])
            else:
                await ctx.send(MESSAGES['NO_MUSIC_PLAYING'])

        except Exception as e:
            logger.error(f"스킵 명령어 오류: {e}")
            await ctx.send(MESSAGES['ERROR'].format(str(e)))

    @commands.command(name="볼륨", aliases=["volume", "v"])
    async def volume(self, ctx: commands.Context, volume: int = None):
        try:
            player = ctx.voice_client
            if not player:
                await ctx.send(MESSAGES['NOT_CONNECTED'])
                return

            if volume is None:
                current_volume = int(self.get_volume(ctx.guild.id) * 100)
                await ctx.send(f"🔊 현재 볼륨: {current_volume}%")
                return

            if not 0 <= volume <= 100:
                await ctx.send("❌ 볼륨은 0에서 100 사이의 값이어야 합니다!")
                return

            self.volume[ctx.guild.id] = volume / 100
            await player.set_volume(volume)
            await ctx.send(MESSAGES['VOLUME_CHANGE'].format(volume))

        except Exception as e:
            logger.error(f"볼륨 명령어 오류: {e}")
            await ctx.send(MESSAGES['ERROR'].format(str(e)))

async def setup(bot):
    await bot.add_cog(Music(bot))