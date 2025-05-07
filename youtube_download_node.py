import traceback
try:
    from autotask.nodes import Node, register_node
except ImportError:
    from stub import Node, register_node

# 使用绝对导入
from .cookie_utils import get_cookie_file

from typing import Dict, Any
import yt_dlp
import os

@register_node
class YouTubeDownloadNode(Node):
    NAME = "YouTube Download"
    DESCRIPTION = "Download videos from YouTube with simple options"
    CATEGORY = "YouTube"
    MAINTAINER = "AutoTask"
    VERSION = "1.0.0"
    ICON = "🎬"

    INPUTS = {
        "url": {
            "label": "YouTube URL",
            "description": "URL of the YouTube video or playlist to download",
            "type": "STRING",
            "required": True,
            "placeholder": "https://www.youtube.com/watch?v=...",
            "validator": "url"
        },
        "download_path": {
            "label": "Save Location",
            "description": "Where to save the downloaded video",
            "type": "STRING",
            "widget": "DIR",
            "required": True,
            "placeholder": "Select download folder"
        },
        "quality": {
            "label": "Video Quality",
            "description": "Maximum video quality to download",
            "type": "COMBO",
            "required": True,
            "default": "1080p",
            "options": ["360p", "480p", "720p", "1080p", "1440p", "2160p", "best"],
            "widget": "COMBO"
        },
        "extract_audio": {
            "label": "Extract Audio",
            "description": "Extract audio from video",
            "type": "STRING",
            "required": True,
            "default": "false",
            "choices": ["true", "false"],
            "widget": "COMBO"
        },
        "cookie_file": {
            "label": "Cookie File",
            "description": "Optional: Cookie file (supports both Netscape and Playwright JSON formats)",
            "type": "STRING",
            "widget": "FILE",
            "required": False,
            "default": "",
            "placeholder": "Select cookie file",
            "validator": "file_exists"
        }
    }

    OUTPUTS = {
        "downloaded_files": {
            "label": "Downloaded Files",
            "description": "List of downloaded file paths",
            "type": "STRING",
        }
    }

    def __init__(self):
        super().__init__()
        self._ydl = None  # 保存 YoutubeDL 实例的引用
        self._stopped = False  # 添加停止标志
        self.workflow_logger = None

    async def stop(self) -> None:
        """Stop the download process"""
        self._stopped = True

    def _progress_hook(self, d):
        """Progress hook to check stop flag and show progress"""
        if self._stopped:
            self.workflow_logger("Download cancelled by user")
            raise Exception("Download cancelled by user")
        
        if '_percent_str' in d:
            self.workflow_logger.info(f'Downloading: {d["_percent_str"]} of {d["_total_bytes_str"]}')

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            self.workflow_logger = workflow_logger
            self._stopped = False  # 重置停止标志
            url = node_inputs["url"]
            path = node_inputs["download_path"]
            quality = node_inputs["quality"]
            audio_only = node_inputs.get("extract_audio", "false") == "true"
            cookie_file = node_inputs.get("cookie_file", "")

            # 确保下载路径存在
            os.makedirs(path, exist_ok=True)
            
            workflow_logger.info(f"Starting download from: {url}")
            
            # 基本下载配置
            ydl_opts = {
                'format': 'bestaudio/best' if audio_only else f'best[height<={quality[:-1]}]/best' if quality != 'best' else 'bestvideo+bestaudio/best',
                'outtmpl': f'{path}/%(title)s.%(ext)s',
                'progress_hooks': [self._progress_hook],
            }

            # 处理cookie文件
            if cookie_file:
                netscape_cookie_file = get_cookie_file(cookie_file)
                if netscape_cookie_file:
                    workflow_logger.info("Using provided cookie file")
                    ydl_opts['cookiefile'] = netscape_cookie_file
                else:
                    workflow_logger.warning("Invalid cookie file format")

            # 如果是仅下载音频,添加音频处理器
            if audio_only:
                ydl_opts.update({
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }]
                })

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self._ydl = ydl  # 保存实例引用
                workflow_logger.info("Extracting video information...")
                
                if self._stopped:  # 检查是否已停止
                    return {
                        "success": False,
                        "error_message": "Download cancelled by user"
                    }
                
                info = ydl.extract_info(url, download=True)
                if 'entries' in info:  # 播放列表
                    downloaded_files = [ydl.prepare_filename(entry) for entry in info['entries']]
                else:  # 单个视频
                    downloaded_files = [ydl.prepare_filename(info)]

            workflow_logger.info("Download completed successfully!")
            
            return {
                "success": True,
                "downloaded_files": '\n'.join(downloaded_files)
            }

        except Exception as e:
            if self._stopped:
                workflow_logger.info("Download cancelled by user")
                return {
                    "success": False,
                    "error_message": "Download cancelled by user"
                }
            workflow_logger.error(f"Download failed: {str(e)}")
            workflow_logger.error(traceback.format_exc())  # 添加详细的错误堆栈
            return {
                "success": False,
                "error_message": str(e)
            }
        finally:
            self._ydl = None  # 清除实例引用 