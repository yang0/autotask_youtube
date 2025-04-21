try:
    from autotask.nodes import Node, register_node
except ImportError:
    from stub import Node, register_node

import os
import sys
import tempfile
from typing import Dict, Any

# Add youtube-dl to the path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'youtube-dl'))
import youtube_dl

# Import cookie utilities
from .cookie_utils import get_cookie_file


@register_node
class YouTubeSubtitleDownloadNode(Node):
    NAME = "YouTube Subtitle Download"
    DESCRIPTION = "Download subtitles from a YouTube video"

    INPUTS = {
        "url": {
            "label": "YouTube URL",
            "description": "URL of the YouTube video",
            "type": "STRING",
            "required": True,
        },
        "output_dir": {
            "label": "Output Directory",
            "description": "Directory to save the subtitles",
            "type": "STRING",
            "default": "",
            "required": False,
            "widget": "DIR",
        },
        "languages": {
            "label": "Languages",
            "description": "Comma-separated list of languages to download (e.g., 'en,es,fr')",
            "type": "STRING",
            "default": "en",
            "required": False,
        },
        "auto_generated": {
            "label": "Auto-generated Subtitles",
            "description": "Include auto-generated subtitles",
            "type": "BOOLEAN",
            "default": False,
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
        "subtitle_files": {
            "label": "Subtitle Files",
            "description": "Paths to the downloaded subtitle files",
            "type": "LIST",
        },
        "available_languages": {
            "label": "Available Languages",
            "description": "List of available subtitle languages",
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
            languages = node_inputs.get("languages", "en")
            auto_generated = node_inputs.get("auto_generated", False)
            cookie_file = node_inputs.get("cookie_file", "")

            workflow_logger.info(f"Starting subtitle download for YouTube video: {url}")

            # Create a temporary directory if no output directory is specified
            if not output_dir:
                output_dir = tempfile.mkdtemp()
                workflow_logger.info(f"Using temporary directory: {output_dir}")

            # Parse languages
            lang_list = [lang.strip() for lang in languages.split(",")]

            # Configure youtube-dl options
            ydl_opts = {
                'verbose': True,  # Add verbose mode for debugging
                'progress_hooks': [self._progress_hook],  # Add progress hook
                'writesubtitles': True,
                'writeautomaticsub': auto_generated,
                'subtitleslangs': lang_list,
                'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                'skip_download': True,  # Skip downloading the video
                'restrictfilenames': True,  # 避免文件名中的特殊字符
            }

            # Add cookie file if provided
            if cookie_file:
                # Convert cookie file if needed
                netscape_cookie_file = get_cookie_file(cookie_file)
                if netscape_cookie_file:
                    workflow_logger.info(f"Using cookie file: {netscape_cookie_file}")
                    ydl_opts['cookiefile'] = netscape_cookie_file

            # Download the subtitles
            try:
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    self._ydl = ydl
                    # First, extract the video info without downloading
                    info = ydl.extract_info(url, download=False)
                    
                    if self._is_interrupted:
                        workflow_logger.info("Download was interrupted after info extraction")
                        return {
                            "success": False,
                            "error_message": "Download interrupted after info extraction"
                        }
                    
                    # Get available languages
                    available_langs = []
                    if 'subtitles' in info:
                        available_langs.extend(info['subtitles'].keys())
                    if 'automatic_captions' in info and auto_generated:
                        available_langs.extend(info['automatic_captions'].keys())
                    
                    available_langs = sorted(set(available_langs))
                    workflow_logger.info(f"Available languages: {', '.join(available_langs)}")
                    
                    # Check if requested languages are available
                    unavailable_langs = [lang for lang in lang_list if lang not in available_langs]
                    if unavailable_langs:
                        workflow_logger.warning(f"Languages not available: {', '.join(unavailable_langs)}")
                    
                    # Download the subtitles
                    ydl.download([url])
                    
                    # Get the subtitle files
                    subtitle_files = []
                    
                    # 使用youtube-dl的sanitize_filename函数来确保文件名一致
                    title = info['title']
                    if ydl_opts.get('restrictfilenames', False):
                        from youtube_dl.utils import sanitize_filename
                        title = sanitize_filename(title, restricted=True)
                    
                    for lang in lang_list:
                        if lang in available_langs:
                            vtt_file = os.path.join(output_dir, f"{title}.{lang}.vtt")
                            if os.path.exists(vtt_file):
                                subtitle_files.append(vtt_file)
                                workflow_logger.info(f"Downloaded subtitles for language {lang}")
                            else:
                                workflow_logger.warning(f"Subtitle file not found: {vtt_file}")
                    
                    if not subtitle_files:
                        workflow_logger.warning("No subtitles were downloaded")
                        return {
                            "success": False,
                            "error_message": "No subtitles were downloaded",
                            "subtitle_files": [],
                            "available_languages": available_langs
                        }
                    
                    workflow_logger.info(f"Successfully downloaded {len(subtitle_files)} subtitle files")
                    return {
                        "success": True,
                        "subtitle_files": subtitle_files,
                        "available_languages": available_langs
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
            workflow_logger.error(f"YouTube subtitle download failed: {str(e)}")
            return {
                "success": False,
                "error_message": str(e)
            } 