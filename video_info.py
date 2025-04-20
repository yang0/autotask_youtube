try:
    from autotask.nodes import Node, register_node
except ImportError:
    from stub import Node, register_node

import os
import sys
import json
from typing import Dict, Any

# Add youtube-dl to the path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'youtube-dl'))
import youtube_dl


@register_node
class YouTubeVideoInfoNode(Node):
    NAME = "YouTube Video Info"
    DESCRIPTION = "Extract information about a YouTube video without downloading"

    INPUTS = {
        "url": {
            "label": "YouTube URL",
            "description": "URL of the YouTube video",
            "type": "STRING",
            "required": True,
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
        "title": {
            "label": "Video Title",
            "description": "Title of the video",
            "type": "STRING",
        },
        "description": {
            "label": "Video Description",
            "description": "Description of the video",
            "type": "STRING",
        },
        "duration": {
            "label": "Duration",
            "description": "Duration of the video in seconds",
            "type": "INT",
        },
        "uploader": {
            "label": "Uploader",
            "description": "Name of the channel that uploaded the video",
            "type": "STRING",
        },
        "upload_date": {
            "label": "Upload Date",
            "description": "Date when the video was uploaded (YYYYMMDD)",
            "type": "STRING",
        },
        "view_count": {
            "label": "View Count",
            "description": "Number of views",
            "type": "INT",
        },
        "like_count": {
            "label": "Like Count",
            "description": "Number of likes",
            "type": "INT",
        },
        "dislike_count": {
            "label": "Dislike Count",
            "description": "Number of dislikes",
            "type": "INT",
        },
        "comment_count": {
            "label": "Comment Count",
            "description": "Number of comments",
            "type": "INT",
        },
        "thumbnail_url": {
            "label": "Thumbnail URL",
            "description": "URL of the video thumbnail",
            "type": "STRING",
        },
        "formats": {
            "label": "Available Formats",
            "description": "List of available video formats",
            "type": "STRING",
        },
        "raw_info": {
            "label": "Raw Info",
            "description": "Raw video information as JSON",
            "type": "STRING",
        },
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            url = node_inputs["url"]
            cookie_file = node_inputs.get("cookie_file", "")
            
            workflow_logger.info(f"Extracting information for YouTube video: {url}")

            # Configure youtube-dl options
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }

            # Add cookie file if provided
            if cookie_file and os.path.exists(cookie_file):
                workflow_logger.info(f"Using cookie file: {cookie_file}")
                ydl_opts['cookiefile'] = cookie_file

            # Extract the video info without downloading
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Get available formats
                formats = []
                if 'formats' in info:
                    for fmt in info['formats']:
                        format_id = fmt.get('format_id', 'N/A')
                        ext = fmt.get('ext', 'N/A')
                        resolution = fmt.get('resolution', 'N/A')
                        formats.append(f"{format_id} - {ext} - {resolution}")
                
                formats_str = "\n".join(formats)
                
                workflow_logger.info(f"Information extracted successfully")
                
                return {
                    "success": True,
                    "title": info.get('title', ''),
                    "description": info.get('description', ''),
                    "duration": info.get('duration', 0),
                    "uploader": info.get('uploader', ''),
                    "upload_date": info.get('upload_date', ''),
                    "view_count": info.get('view_count', 0),
                    "like_count": info.get('like_count', 0),
                    "dislike_count": info.get('dislike_count', 0),
                    "comment_count": info.get('comment_count', 0),
                    "thumbnail_url": info.get('thumbnail', ''),
                    "formats": formats_str,
                    "raw_info": json.dumps(info, indent=2),
                }

        except Exception as e:
            workflow_logger.error(f"YouTube video info extraction failed: {str(e)}")
            return {
                "success": False,
                "error_message": str(e)
            } 