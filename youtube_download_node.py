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
        "separate_audio": {
            "label": "Separate Audio",
            "description": "Whether to download video and audio separately",
            "type": "BOOLEAN",
            "required": False,
            "default": False
        },
        "subtitle_langs": {
            "label": "Subtitle Languages",
            "description": "Languages of subtitles to download (comma separated, empty for no subtitles). Available: en,zh-Hans,zh-Hant,ja,ko,fr,de,es,ru etc.",
            "type": "STRING",
            "required": False,
            "default": "en,en-US,zh-Hans",
            "placeholder": "en,en-US,zh-Hans"
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
            "type": "LIST",
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
            separate_audio = node_inputs.get("separate_audio", False)
            cookie_file = node_inputs.get("cookie_file", "")
            subtitle_langs = node_inputs.get("subtitle_langs", "en,en-US,zh-Hans").strip()
            self.workflow_logger = workflow_logger

            # 解析字幕语言列表
            user_langs = [lang.strip() for lang in subtitle_langs.split(",") if lang.strip()]
            if not user_langs:
                user_langs = ["en", "en-US", "zh-Hans"]  # 如果没有指定语言，使用默认值
            workflow_logger.info(f"Will try to download subtitles for languages: {user_langs}")

            # 先用yt-dlp获取所有可用字幕track id
            info_opts = {
                'quiet': True,
                'no_warnings': True,
                'writesubtitles': True,
                'listsubtitles': True,
            }
            if cookie_file:
                netscape_cookie_file = get_cookie_file(cookie_file)
                if netscape_cookie_file:
                    info_opts['cookiefile'] = netscape_cookie_file
            with yt_dlp.YoutubeDL(info_opts) as info_ydl:
                info = info_ydl.extract_info(url, download=False)
            # 收集所有可用字幕track id
            subtitle_tracks = list(info.get('subtitles', {}).keys())
            auto_caption_tracks = list(info.get('automatic_captions', {}).keys())
            all_tracks = subtitle_tracks + auto_caption_tracks
            # 模糊匹配用户指定的语种
            matched_tracks = []
            for user_lang in user_langs:
                for track in all_tracks:
                    if track == user_lang or track.startswith(user_lang + "-") or track.startswith(user_lang):
                        if track not in matched_tracks:
                            matched_tracks.append(track)
            if not matched_tracks:
                workflow_logger.warning(f"No matching subtitle tracks found for: {user_langs}")
            else:
                workflow_logger.info(f"Matched subtitle tracks: {matched_tracks}")

            # 确保下载路径存在
            os.makedirs(path, exist_ok=True)
            
            workflow_logger.info(f"Starting download from: {url}")

            # 根据是否分离音轨设置不同的格式
            if separate_audio:
                format_str = f'bv*[height<={quality[:-1]}],ba' if quality != 'best' else 'bv*,ba'
                workflow_logger.info("Will download video and audio separately")
            else:
                format_str = f'bv*[height<={quality[:-1]}]+ba/b[height<={quality[:-1]}]' if quality != 'best' else 'bv*+ba/b'
                workflow_logger.info("Will download video with merged audio")

            ydl_opts = {
                'format': format_str,
                'outtmpl': f'{path}/%(title)s.%(ext)s',
                'progress_hooks': [self._progress_hook],
                'quiet': False,
                'no_warnings': False,
                'verbose': True,
                'merge_output_format': 'mp4'  # 确保输出为MP4格式
            }
            # 如果有匹配到的字幕track，添加到下载参数
            if matched_tracks:
                ydl_opts.update({
                    'writesubtitles': True,
                    'writeautomaticsub': True,
                    'subtitleslangs': matched_tracks,
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

                # 检查所有相关文件（视频、音频、字幕）
                downloaded_files = []
                # 收集所有以base_filename开头的文件（视频、音频、字幕等）
                dir_files = os.listdir(path)
                for f in dir_files:
                    # 兼容windows和linux路径
                    full_path = os.path.join(path, f)
                    if os.path.isfile(full_path) and os.path.splitext(full_path)[0] == base_filename:
                        downloaded_files.append(full_path)
                # 兜底：如果没找到任何文件，至少返回主视频文件
                if not downloaded_files:
                    downloaded_files.append(filename)
                # 兼容旧逻辑，补充字幕文件
                if matched_tracks:
                    for lang in matched_tracks:
                        subtitle_file = f"{base_filename}.{lang}.vtt"
                        auto_subtitle_file = f"{base_filename}.{lang}.auto.vtt"
                        if os.path.exists(subtitle_file) and subtitle_file not in downloaded_files:
                            downloaded_files.append(subtitle_file)
                        if os.path.exists(auto_subtitle_file) and auto_subtitle_file not in downloaded_files:
                            downloaded_files.append(auto_subtitle_file)
                workflow_logger.info(f"Download completed successfully! Files: {downloaded_files}")
                return {
                    "success": True,
                    "downloaded_files": downloaded_files
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