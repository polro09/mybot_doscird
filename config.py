import json
import os

def load_config():
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"설정 파일 로드 중 오류 발생: {e}")
        return None

WAVELINK_CONFIG = {
    'NODES': [
        {
            'host': '127.0.0.1',
            'port': 2333,
            'password': '021926',
            'identifier': 'MAIN',
            'region': 'asia',
            'secure': False,
            'search_only': False,
            'retries': 3,
            'retry_delay': 7.0
        }
    ]
}

YYDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',  # 'auto'에서 'ytsearch'로 변경
    'extract_flat': True,
    'source_address': '0.0.0.0',
    'force-ipv4': True,
    'cachedir': False
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -sn -dn'  # 오디오만 추출하도록 옵션 추가
}

BOT_CONFIG = {
    'DEFAULT_PREFIX': '!',
    'COLOR': 0x3498db,
    'TIMEOUT': 60,
    'MAX_QUEUE_SIZE': 100,
    'MAX_SONG_PRELOAD': 5,
    'MUSIC_CHANNEL_NAME': '음악-봇'
}

MESSAGES = {
    'NOT_IN_VOICE': '❌ 먼저 음성 채널에 접속해주세요!',
    'NO_MUSIC_PLAYING': '❌ 현재 재생 중인 곡이 없습니다!',
    'NOT_CONNECTED': '❌ 음성 채널에 접속해있지 않습니다!',
    'NO_RESULTS': '❌ 검색 결과가 없습니다!',
    'ADDED_TO_QUEUE': '✅ 재생목록에 추가됨: `{}`',
    'NOW_PLAYING': '🎵 현재 재생 중: `{}`',
    'VOLUME_CHANGE': '🔊 볼륨이 {}%로 설정되었습니다.',
    'QUEUE_EMPTY': '📋 재생목록이 비어있습니다!',
    'ERROR': '❌ 오류가 발생했습니다: {}',
    'SKIP_SUCCESS': '⏭️ 다음 곡으로 넘어갑니다.',
    'PAUSED': '⏸️ 일시정지되었습니다.',
    'RESUMED': '▶️ 다시 재생합니다.',
    'STOPPED': '⏹️ 재생이 정지되었습니다.',
    'JOINED': '✅ `{}` 채널에 입장했습니다!',
    'LEFT': '👋 음성 채널에서 퇴장했습니다!'
}

LOGGING_CONFIG = {
    'version': 1,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'bot.log',
            'formatter': 'default',
            'encoding': 'utf-8'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default'
        }
    },
    'loggers': {
        'music_bot': {
            'handlers': ['file', 'console'],
            'level': 'INFO'
        }
    }
}

def get_config(key: str, default=None):
    config = load_config()
    if config is None:
        return default
    return config.get(key, default)

def update_config(key: str, value) -> bool:
    try:
        config = load_config()
        if config is None:
            config = {}
        config[key] = value
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"설정 업데이트 중 오류 발생: {e}")
        return False

STATUS_MESSAGES = [
    "!도움말 for help",
    "!재생 [곡 제목/URL]",
    "음악과 함께해요! 🎵"
]