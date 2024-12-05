# main.py
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import logging
import logging.handlers
import sys
import asyncio
import json
import traceback
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 로그 디렉토리 생성
if not os.path.exists('logs'):
    os.makedirs('logs')

# 로깅 설정
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler('logs/bot.log', 'a', 'utf-8')
file_handler.setFormatter(log_formatter)
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

logger = logging.getLogger('bot')
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# 환경변수 로드
load_dotenv()

def load_config():
    """config.json 파일 로드"""
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"설정 파일 로드 중 오류 발생: {e}")
        return None

class CustomBot(commands.Bot):
    def __init__(self):
        # config.json 로드
        self.config = load_config()
        if not self.config:
            logger.critical("config.json 파일을 로드할 수 없습니다. 파일이 존재하고 올바른 형식인지 확인하세요.")
            sys.exit(1)

        # Discord 봇 인텐트 설정
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.voice_states = True
        intents.dm_messages = True  # DM 메시지 인텐트 추가

        super().__init__(
            command_prefix=self.config['settings']['prefix'],
            intents=intents,
            help_command=commands.DefaultHelpCommand(),
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="명령어 도움말: !도움말"
            )
        )

    async def setup_hook(self):
        """봇 초기 설정"""
        try:
            logger.info("확장 기능 로드 시작...")
            await self.load_extensions()
            logger.info("확장 기능 로드 완료")
        except Exception as e:
            logger.error(f"Setup hook error: {e}")
            logger.error(traceback.format_exc())

    async def load_extensions(self):
        """Cogs 폴더의 모든 확장 기능을 로드"""
        # 로드하지 않을 파일 목록
        ignore_files = ['combat_bt.py', 'combat_log.py', '__init__.py']
        
        for filename in os.listdir('./cogs'):
            # 무시할 파일이면 건너뛰기
            if filename in ignore_files:
                continue
                
            # 단일 파일 Cog 로드
            if filename.endswith('.py'):
                try:
                    # 언로드 시도
                    try:
                        await self.unload_extension(f'cogs.{filename[:-3]}')
                    except:
                        pass

                    # 로드
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    logger.info(f'확장 기능 로드 완료: {filename}')
                except Exception as e:
                    logger.error(f'확장 기능 로드 실패 [{filename}]: {str(e)}')
                    logger.error(traceback.format_exc())

    async def on_ready(self):
        """봇 준비 완료 이벤트"""
        logger.info(f'봇 로그인 완료: {self.user}')
        logger.info(f'서버 수: {len(self.guilds)}개')
        logger.info(f'명령어 접두사: {self.command_prefix}')
        logger.info(f'로드된 Cogs: {", ".join([ext[5:] for ext in self.extensions.keys()])}')

        # 로드된 명령어 목록 출력
        commands_list = [command.name for command in self.commands]
        logger.info(f'사용 가능한 명령어: {", ".join(commands_list)}')

    async def on_command_error(self, ctx: commands.Context, error: Exception):
        """명령어 실행 중 오류 처리"""
        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.MissingPermissions):
            await ctx.send(self.config['messages']['no_permission'])
            return

        error_message = self.config['messages'].get('error', '❌ 오류가 발생했습니다: {error}')
        await ctx.send(error_message.format(error=str(error)))
        logger.error(f'명령어 실행 오류 - {ctx.command}: {str(error)}')
        logger.error(traceback.format_exc())

class RestartHandler(FileSystemEventHandler):
    """파일 변경을 감지하여 봇을 재시작하는 핸들러"""
    def __init__(self, bot_process):
        self.bot_process = bot_process
        self.watch_extensions = {'.py', '.json'}
        self.ignore_patterns = {
            'logs/',
            '__pycache__',
            '.env',
            '.git/',
            '.vscode/',
            '.idea/'
        }
        self.last_restart = 0

    def should_ignore(self, path):
        """특정 파일/디렉토리를 무시해야 하는지 확인"""
        return any(pattern in path for pattern in self.ignore_patterns)

    def on_modified(self, event):
        """파일 수정 이벤트 처리"""
        if event.is_directory:
            return

        current_time = time.time()
        if current_time - self.last_restart < 3:
            return

        file_path = event.src_path
        file_ext = os.path.splitext(file_path)[1]

        if (file_ext in self.watch_extensions and 
            not self.should_ignore(file_path)):
            logger.info(f"파일 변경 감지됨: {file_path}. 봇을 재시작합니다.")
            self.last_restart = current_time
            self.restart_bot()

    def restart_bot(self):
        """봇 프로세스를 재시작"""
        logger.info("봇 재시작 중...")
        os.execv(sys.executable, ['python'] + sys.argv)

async def main():
    try:
        # Windows 환경에서 UTF-8 설정
        if sys.platform.startswith('win'):
            import subprocess
            subprocess.run(['chcp', '65001'], shell=True)

        # DISCORD_TOKEN 확인
        token = os.getenv('DISCORD_TOKEN')
        if not token:
            logger.critical("DISCORD_TOKEN이 .env 파일에 설정되지 않았습니다.")
            sys.exit(1)

        # 봇 실행
        bot = CustomBot()

        # 파일 변경 감지 시작
        observer = Observer()
        event_handler = RestartHandler(bot_process=sys.argv)
        observer.schedule(event_handler, path='.', recursive=True)
        observer.start()

        try:
            async with bot:
                await bot.start(token)
        finally:
            observer.stop()
            observer.join()

    except Exception as e:
        logger.critical(f"봇 실행 중 치명적인 오류 발생: {e}")
        logger.critical(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())