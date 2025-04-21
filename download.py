try:
    from autotask.nodes import Node, register_node
except ImportError:
    from stub import Node, register_node

import os
import sys
import tempfile
import json
from typing import Dict, Any

from . import youtube_dl

# Import cookie utilities
from .cookie_utils import get_cookie_file


@register_node
class YouTubeDownloadNode(Node):
    NAME = "YouTube Download"
    DESCRIPTION = "Download videos from YouTube"

    INPUTS = {
        "url": {
            "label": "YouTube URL",
            "description": "URL of the YouTube video to download",
            "type": "STRING",
            "required": True,
        },
        "output_dir": {
            "label": "Output Directory",
            "description": "Directory to save the downloaded video",
            "type": "STRING",
            "default": "",
            "required": False,
            "widget": "DIR",
        },
        "format": {
            "label": "Video Format",
            "description": "Format code for the video (e.g., 'best', 'bestvideo+bestaudio', 'mp4')",
            "type": "COMBO",
            "default": "best",
            "required": False,
            "options": ["best", "worst", "bestvideo", "worstvideo", "bestaudio", "worstaudio"],
        },
        "extract_audio": {
            "label": "Extract Audio",
            "description": "Extract audio from the video",
            "type": "BOOLEAN",
            "default": False,
            "required": False,
        },
        "audio_format": {
            "label": "Audio Format",
            "description": "Format for the extracted audio (e.g., 'mp3', 'm4a')",
            "type": "STRING",
            "default": "mp3",
            "required": False,
        },
        "audio_quality": {
            "label": "Audio Quality",
            "description": "Quality of the extracted audio (0-9, where 0 is best)",
            "type": "INT",
            "default": 5,
            "required": False,
        },
        "write_subs": {
            "label": "Download Subtitles",
            "description": "Download subtitles if available",
            "type": "BOOLEAN",
            "default": False,
            "required": False,
        },
        "write_auto_subs": {
            "label": "Download Auto-generated Subtitles",
            "description": "Download auto-generated subtitles if available",
            "type": "BOOLEAN",
            "default": False,
            "required": False,
        },
        "sub_langs": {
            "label": "Subtitle Languages",
            "description": "Comma-separated list of subtitle languages to download (e.g., 'en,zh-CN'). Use 'all' for all languages.",
            "type": "STRING",
            "default": "en",
            "required": False,
        },
        "cookie_file": {
            "label": "Cookie File",
            "description": "Path to a cookie file for authentication (e.g., 'www.youtube.com.json')",
            "type": "STRING",
            "default": "",
            "required": False,
            "widget": "FILE",
        },
    }

    OUTPUTS = {
        "file_path": {
            "label": "File Path",
            "description": "Path to the downloaded file",
            "type": "STRING",
        },
        "title": {
            "label": "Video Title",
            "description": "Title of the downloaded video",
            "type": "STRING",
        },
        "duration": {
            "label": "Duration",
            "description": "Duration of the video in seconds",
            "type": "INT",
        },
        "subtitle_files": {
            "label": "Subtitle Files",
            "description": "List of paths to downloaded subtitle files",
            "type": "LIST",
        },
    }

    def __init__(self):
        super().__init__()
        self._ydl = None
        self._is_interrupted = False

    def _progress_hook(self, d):
        """Progress hook to check for interruption during download"""
        if self._is_interrupted:
            raise Exception("Download interrupted by user")

    async def stop(self) -> None:
        """
        Stop the node execution when interrupted.
        This method will stop the youtube-dl download process.
        """
        self._is_interrupted = True

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            url = node_inputs["url"]
            output_dir = node_inputs.get("output_dir", "")
            format = node_inputs.get("format", "best")
            extract_audio = node_inputs.get("extract_audio", False)
            audio_format = node_inputs.get("audio_format", "mp3")
            audio_quality = node_inputs.get("audio_quality", 5)
            cookie_file = node_inputs.get("cookie_file", "")
            
            # 字幕相关参数
            write_subs = node_inputs.get("write_subs", False)
            write_auto_subs = node_inputs.get("write_auto_subs", False)
            sub_langs = node_inputs.get("sub_langs", "en")

            workflow_logger.info(f"Starting download of YouTube video: {url}")

            # Create a temporary directory if no output directory is specified
            if not output_dir:
                output_dir = tempfile.mkdtemp()
                workflow_logger.info(f"Using temporary directory: {output_dir}")

            # Configure youtube-dl options
            ydl_opts = {
                'format': format,
                'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                'verbose': True,  # Add verbose mode for debugging
                'progress_hooks': [self._progress_hook],  # Add progress hook to check for interruption
                'writesubtitles': write_subs,  # 是否下载字幕
                'writeautomaticsub': write_auto_subs,  # 是否下载自动生成的字幕
                'subtitleslangs': sub_langs.split(',') if sub_langs != 'all' else ['all'],  # 字幕语言列表
                'subtitlesformat': 'vtt',  # 固定使用vtt格式
                'restrictfilenames': True,  # 避免文件名中的特殊字符
            }

            # Add cookie file if provided
            if cookie_file:
                # Convert cookie file if needed
                netscape_cookie_file = get_cookie_file(cookie_file)
                if netscape_cookie_file:
                    workflow_logger.info(f"Using cookie file: {netscape_cookie_file}")
                    ydl_opts['cookiefile'] = netscape_cookie_file

            # Add audio extraction options if requested
            if extract_audio:
                ydl_opts.update({
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': audio_format,
                        'preferredquality': str(audio_quality),
                    }],
                })

            # Download the video
            print("=============")
            print(ydl_opts)
            print("=============")

            try:
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    self._ydl = ydl
                    # First try to extract info without downloading
                    try:
                        info = ydl.extract_info(url, download=False)
                        workflow_logger.info(f"Successfully extracted video info: {info.get('title', 'Unknown Title')}")
                    except Exception as info_error:
                        workflow_logger.error(f"Failed to extract video info: {str(info_error)}")
                        raise

                    if self._is_interrupted:
                        workflow_logger.info("Download was interrupted after info extraction")
                        return {
                            "success": False,
                            "error_message": "Download interrupted after info extraction"
                        }

                    # Then proceed with download
                    info = ydl.extract_info(url, download=True)
                    
                    # Get the file path
                    if extract_audio:
                        file_path = os.path.join(output_dir, f"{info['title']}.{audio_format}")
                    else:
                        file_path = os.path.join(output_dir, f"{info['title']}.{info['ext']}")

                    # 获取字幕文件路径
                    subtitle_files = []
                    if (write_subs or write_auto_subs) and 'requested_subtitles' in info:
                        base_name = os.path.splitext(file_path)[0]
                        for lang in info['requested_subtitles']:
                            sub_file = f"{base_name}.{lang}.vtt"
                            if os.path.exists(sub_file):
                                subtitle_files.append(sub_file)
                                workflow_logger.info(f"Found subtitle file: {sub_file}")

                    workflow_logger.info(f"Download completed: {file_path}")
                    if subtitle_files:
                        workflow_logger.info(f"Downloaded {len(subtitle_files)} subtitle files")
                    
                    return {
                        "success": True,
                        "file_path": file_path,
                        "title": info.get('title', ''),
                        "duration": info.get('duration', 0),
                        "subtitle_files": subtitle_files,
                    }
            finally:
                self._ydl = None
                self._is_interrupted = False

        except Exception as e:
            if "Download interrupted by user" in str(e):
                workflow_logger.info("Download interrupted by user")
                return {
                    "success": False,
                    "error_message": "Download interrupted by user"
                }
            workflow_logger.error(f"YouTube download failed: {str(e)}")
            return {
                "success": False,
                "error_message": str(e)
            }
