try:
    from autotask.nodes import Node, register_node
except ImportError:
    from stub import Node, register_node

import os
import sys
import tempfile
import json
from typing import Dict, Any

# Add youtube-dl to the path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'youtube-dl'))
import youtube_dl

# Import cookie utilities
from .cookie_utils import get_cookie_file


@register_node
class YouTubePlaylistDownloadNode(Node):
    NAME = "YouTube Playlist Download"
    DESCRIPTION = "Download videos from a YouTube playlist"
    CATEGORY = "YouTube"
    VERSION = "1.0.0"
    AUTHOR = "AutoTask"
    TAGS = ["youtube", "download", "playlist", "video"]

    INPUTS = {
        "playlist_url": {
            "label": "Playlist URL",
            "description": "URL of the YouTube playlist to download",
            "type": "STRING",
            "required": True,
            "widget": "TEXT",
            "default": "",
        },
        "output_dir": {
            "label": "Output Directory",
            "description": "Directory to save the downloaded videos",
            "type": "STRING",
            "default": "",
            "required": False,
            "widget": "DIR",
        },
        "format": {
            "label": "Video Format",
            "description": "Format code for the videos (e.g., 'best', 'bestvideo+bestaudio', 'mp4')",
            "type": "STRING",
            "default": "best",
            "required": False,
            "widget": "TEXT",
        },
        "extract_audio": {
            "label": "Extract Audio",
            "description": "Extract audio from the videos",
            "type": "BOOLEAN",
            "default": False,
            "required": False,
            "widget": "CHECKBOX",
        },
        "audio_format": {
            "label": "Audio Format",
            "description": "Format for the extracted audio (e.g., 'mp3', 'm4a')",
            "type": "STRING",
            "default": "mp3",
            "required": False,
            "widget": "TEXT",
        },
        "audio_quality": {
            "label": "Audio Quality",
            "description": "Quality of the extracted audio (0-9, where 0 is best)",
            "type": "INT",
            "default": 5,
            "required": False,
            "widget": "NUMBER",
            "min": 0,
            "max": 9,
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
        "file_paths": {
            "label": "File Paths",
            "description": "Paths to the downloaded files",
            "type": "LIST",
            "default": [],
        },
        "titles": {
            "label": "Video Titles",
            "description": "Titles of the downloaded videos",
            "type": "LIST",
            "default": [],
        },
        "durations": {
            "label": "Durations",
            "description": "Durations of the videos in seconds",
            "type": "LIST",
            "default": [],
        },
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            playlist_url = node_inputs["playlist_url"]
            output_dir = node_inputs.get("output_dir", "")
            format = node_inputs.get("format", "best")
            extract_audio = node_inputs.get("extract_audio", False)
            audio_format = node_inputs.get("audio_format", "mp3")
            audio_quality = node_inputs.get("audio_quality", 5)
            cookie_file = node_inputs.get("cookie_file", "")

            workflow_logger.info(f"Starting download of YouTube playlist: {playlist_url}")

            # Create a temporary directory if no output directory is specified
            if not output_dir:
                output_dir = tempfile.mkdtemp()
                workflow_logger.info(f"Using temporary directory: {output_dir}")

            # Configure youtube-dl options
            ydl_opts = {
                'format': format,
                'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
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

            # Download the playlist
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(playlist_url, download=True)
                
                # Get the file paths, titles, and durations
                file_paths = []
                titles = []
                durations = []
                
                for entry in info['entries']:
                    if entry:
                        if extract_audio:
                            file_path = os.path.join(output_dir, f"{entry['title']}.{audio_format}")
                        else:
                            file_path = os.path.join(output_dir, f"{entry['title']}.{entry['ext']}")
                        
                        file_paths.append(file_path)
                        titles.append(entry.get('title', ''))
                        durations.append(entry.get('duration', 0))

                workflow_logger.info(f"Download completed: {len(file_paths)} videos downloaded")
                
                return {
                    "success": True,
                    "file_paths": file_paths,
                    "titles": titles,
                    "durations": durations,
                }

        except Exception as e:
            workflow_logger.error(f"YouTube playlist download failed: {str(e)}")
            return {
                "success": False,
                "error_message": str(e)
            } 