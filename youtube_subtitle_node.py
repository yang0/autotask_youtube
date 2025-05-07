try:
    from autotask.nodes import Node, register_node
except ImportError:
    from stub import Node, register_node

from .cookie_utils import get_cookie_file
from typing import Dict, Any
import yt_dlp
import os

@register_node
class YouTubeSubtitleNode(Node):
    NAME = "YouTube Subtitle Download"
    DESCRIPTION = "Download subtitles from YouTube videos"
    CATEGORY = "YouTube"
    MAINTAINER = "AutoTask"
    VERSION = "1.0.0"
    ICON = "📝"

    INPUTS = {
        "url": {
            "label": "YouTube URL",
            "description": "URL of the YouTube video",
            "type": "STRING",
            "required": True,
            "placeholder": "https://www.youtube.com/watch?v=...",
            "validator": "url"
        },
        "language": {
            "label": "Language",
            "description": "Subtitle language to download",
            "type": "STRING",
            "default": "en",
            "options": ["en", "es", "fr", "de", "it", "ja", "ko", "zh-Hans", "zh-Hant"],
            "required": True,
            "placeholder": "Select language"
        },
        "save_path": {
            "label": "Save Location",
            "description": "Where to save the subtitles",
            "type": "STRING",
            "widget": "DIR",
            "required": True,
            "placeholder": "Select save folder"
        },
        "cookie_file": {
            "label": "Cookie File",
            "description": "Optional: Cookie file (supports both Netscape and Playwright JSON formats)",
            "type": "STRING",
            "widget": "FILE",
            "required": False,
            "default": "",
            "placeholder": "Select cookie file"
        }
    }

    OUTPUTS = {
        "subtitle_file": {
            "label": "Subtitle File",
            "description": "Path to the downloaded subtitle file",
            "type": "STRING",
        }
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            url = node_inputs["url"]
            language = node_inputs["language"]
            path = node_inputs["save_path"]
            cookie_file = node_inputs.get("cookie_file", "")

            # 确保保存路径存在
            os.makedirs(path, exist_ok=True)

            workflow_logger.info(f"Downloading subtitles for: {url}")

            ydl_opts = {
                'skip_download': True,  # 不下载视频
                'writesubtitles': True,  # 下载字幕
                'writeautomaticsub': True,  # 如果没有手动字幕，下载自动字幕
                'subtitleslangs': [language],  # 指定语言
                'subtitlesformat': 'vtt',  # 使用 vtt 格式
                'outtmpl': f'{path}/%(title)s.%(ext)s',  # 输出模板
                'quiet': True,
                'no_warnings': True
            }

            if cookie_file:
                netscape_cookie_file = get_cookie_file(cookie_file)
                if netscape_cookie_file:
                    workflow_logger.info("Using provided cookie file")
                    ydl_opts['cookiefile'] = netscape_cookie_file

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                # 使用 os.path.splitext 正确处理扩展名
                base_filename, _ = os.path.splitext(filename)
                subtitle_file = f"{base_filename}.{language}.vtt"

                if not os.path.exists(subtitle_file):
                    # 检查是否是自动字幕
                    auto_subtitle_file = f"{base_filename}.{language}.auto.vtt"
                    if os.path.exists(auto_subtitle_file):
                        subtitle_file = auto_subtitle_file
                    else:
                        workflow_logger.warning(f"No subtitles found for language: {language}")
                        return {
                            "success": False,
                            "error_message": f"No subtitles available for language: {language}"
                        }

            workflow_logger.info("Subtitle download completed!")
            return {
                "success": True,
                "subtitle_file": subtitle_file
            }

        except Exception as e:
            workflow_logger.error(f"Subtitle download failed: {str(e)}")
            return {
                "success": False,
                "error_message": str(e)
            } 