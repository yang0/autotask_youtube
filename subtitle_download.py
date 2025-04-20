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
        "format": {
            "label": "Subtitle Format",
            "description": "Format of the subtitles (e.g., 'srt', 'vtt')",
            "type": "STRING",
            "default": "srt",
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
            "type": "STRING",
        },
        "available_languages": {
            "label": "Available Languages",
            "description": "List of available subtitle languages",
            "type": "STRING",
        },
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            url = node_inputs["url"]
            output_dir = node_inputs.get("output_dir", "")
            languages = node_inputs.get("languages", "en")
            auto_generated = node_inputs.get("auto_generated", False)
            format = node_inputs.get("format", "srt")
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
                'quiet': True,
                'no_warnings': True,
                'writesubtitles': True,
                'writeautomaticsub': auto_generated,
                'subtitleslangs': lang_list,
                'subtitlesformat': format,
                'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                'skip_download': True,  # Skip downloading the video
            }

            # Add cookie file if provided
            if cookie_file and os.path.exists(cookie_file):
                workflow_logger.info(f"Using cookie file: {cookie_file}")
                ydl_opts['cookiefile'] = cookie_file

            # Download the subtitles
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                # First, extract the video info without downloading
                info = ydl.extract_info(url, download=False)
                
                # Get available languages
                available_langs = []
                if 'subtitles' in info:
                    available_langs.extend(info['subtitles'].keys())
                if 'automatic_captions' in info and auto_generated:
                    available_langs.extend(info['automatic_captions'].keys())
                
                available_langs_str = ", ".join(sorted(set(available_langs)))
                
                # Download the subtitles
                ydl.download([url])
                
                # Get the subtitle files
                subtitle_files = []
                for lang in lang_list:
                    if lang in available_langs:
                        subtitle_file = os.path.join(output_dir, f"{info['title']}.{lang}.{format}")
                        if os.path.exists(subtitle_file):
                            subtitle_files.append(subtitle_file)
                
                subtitle_files_str = "\n".join(subtitle_files)
                
                workflow_logger.info(f"Subtitle download completed")
                
                return {
                    "success": True,
                    "subtitle_files": subtitle_files_str,
                    "available_languages": available_langs_str,
                }

        except Exception as e:
            workflow_logger.error(f"YouTube subtitle download failed: {str(e)}")
            return {
                "success": False,
                "error_message": str(e)
            } 