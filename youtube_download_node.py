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
            "description": "URL of the YouTube video to download",
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
            "options": ["360p", "480p", "720p", "1080p", "1440p", "2160p", "best"]
        },
        "subtitle_langs": {
            "label": "Subtitle Languages",
            "description": "Languages of subtitles to download (comma separated, empty for no subtitles). Available: en,zh-Hans,zh-Hant,ja,ko,fr,de,es,ru etc.",
            "type": "STRING",
            "required": False,
            "default": "en,zh-Hans",
            "placeholder": "en,zh-Hans"
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
        self.workflow_logger = None

    def _progress_hook(self, d):
        """Progress hook to show download progress"""
        if '_percent_str' in d:
            self.workflow_logger.info(f'Downloading: {d["_percent_str"]} of {d["_total_bytes_str"]}')

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            url = node_inputs["url"]
            path = node_inputs["download_path"]
            quality = node_inputs["quality"]
            cookie_file = node_inputs.get("cookie_file", "")
            subtitle_langs = node_inputs.get("subtitle_langs", "en,zh-Hans").strip()
            self.workflow_logger = workflow_logger

            # 解析字幕语言列表
            langs = [lang.strip() for lang in subtitle_langs.split(",") if lang.strip()]
            if not langs:
                langs = ["en", "zh-Hans"]  # 如果没有指定语言，使用默认值
            workflow_logger.info(f"Will try to download subtitles for languages: {langs}")

            # 确保下载路径存在
            os.makedirs(path, exist_ok=True)
            
            workflow_logger.info(f"Starting download from: {url}")

            ydl_opts = {
                'format': f'bv*[height<={quality[:-1]}]+ba/b[height<={quality[:-1]}]' if quality != 'best' else 'bv*+ba/b',
                'outtmpl': f'{path}/%(title)s.%(ext)s',
                'progress_hooks': [self._progress_hook],
                'quiet': False,
                'no_warnings': False,
                'verbose': True,
                'merge_output_format': 'mp4'  # 确保输出为MP4格式
            }

            # 如果指定了字幕语言，添加字幕下载选项
            if langs:
                workflow_logger.info(f"Will try to download subtitles for languages: {langs}")
                ydl_opts.update({
                    'writesubtitles': True,
                    'writeautomaticsub': True,
                    'subtitleslangs': langs,
                    'subtitlesformat': 'vtt'
                })
            else:
                workflow_logger.info("No subtitle languages specified, will not download subtitles")

            # 处理cookie文件
            if cookie_file:
                netscape_cookie_file = get_cookie_file(cookie_file)
                if netscape_cookie_file:
                    workflow_logger.info("Using provided cookie file")
                    ydl_opts['cookiefile'] = netscape_cookie_file
                else:
                    workflow_logger.warning("Invalid cookie file format")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self._ydl = ydl
                workflow_logger.info("Downloading video and subtitles...")
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                base_filename, _ = os.path.splitext(filename)

                # 检查字幕文件是否存在
                subtitle_files = []
                if langs:  # 只有在指定了字幕语言时才检查字幕文件
                    for lang in langs:
                        subtitle_file = f"{base_filename}.{lang}.vtt"
                        auto_subtitle_file = f"{base_filename}.{lang}.auto.vtt"
                        if os.path.exists(subtitle_file):
                            subtitle_files.append(subtitle_file)
                            workflow_logger.info(f"Found manual subtitle file: {subtitle_file}")
                        elif os.path.exists(auto_subtitle_file):
                            subtitle_files.append(auto_subtitle_file)
                            workflow_logger.info(f"Found auto-generated subtitle file: {auto_subtitle_file}")
                        else:
                            workflow_logger.warning(f"No subtitle file found for language: {lang}")

                    if subtitle_files:
                        workflow_logger.info(f"Successfully downloaded subtitle files: {', '.join(subtitle_files)}")
                    else:
                        workflow_logger.warning("No subtitles were downloaded")

                # 返回视频文件和字幕文件的路径
                downloaded_files = [filename] + subtitle_files
                workflow_logger.info("Download completed successfully!")
                return {
                    "success": True,
                    "downloaded_files": '\n'.join(downloaded_files)
                }

        except Exception as e:
            workflow_logger.error(f"Download failed: {str(e)}")
            workflow_logger.error(traceback.format_exc())
            return {
                "success": False,
                "error_message": str(e)
            }
        finally:
            self._ydl = None 