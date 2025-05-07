try:
    from autotask.nodes import Node, register_node   
except ImportError:
    from stub import Node, register_node
    
from .cookie_utils import get_cookie_file
from typing import Dict, Any, List
import yt_dlp
import os

@register_node
class YouTubeInfoNode(Node):
    NAME = "YouTube Info"
    DESCRIPTION = "Get information about a YouTube video without downloading"
    CATEGORY = "YouTube"
    MAINTAINER = "AutoTask"
    VERSION = "1.0.0"
    ICON = "ℹ️"

    INPUTS = {
        "url": {
            "label": "YouTube URL",
            "description": "URL of the YouTube video to analyze",
            "type": "STRING",
            "required": True,
            "placeholder": "https://www.youtube.com/watch?v=...",
            "validator": "url"
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
        "title": {
            "label": "Video Title",
            "description": "Title of the video",
            "type": "STRING",
        },
        "duration": {
            "label": "Duration",
            "description": "Duration of the video in seconds",
            "type": "STRING",
        },
        "view_count": {
            "label": "View Count",
            "description": "Number of views",
            "type": "STRING",
        },
        "thumbnail": {
            "label": "Thumbnail URL",
            "description": "URL of video thumbnail",
            "type": "STRING",
        },
        "description": {
            "label": "Description",
            "description": "Video description",
            "type": "STRING",
        },
        "subtitles": {
            "label": "Available Subtitles",
            "description": "List of available subtitle languages",
            "type": "STRING",
        },
        "auto_captions": {
            "label": "Auto-generated Captions",
            "description": "List of available auto-generated caption languages",
            "type": "STRING",
        },
        "uploader_id": {
            "label": "Uploader ID",
            "description": "ID of the video uploader",
            "type": "STRING",
        },
        "release_date": {
            "label": "Release Date",
            "description": "Release date of the video (YYYYMMDD)",
            "type": "STRING",
        },
        "availability": {
            "label": "Availability",
            "description": "Video availability status (public, unlisted, private, etc)",
            "type": "STRING",
        },
        "like_count": {
            "label": "Like Count",
            "description": "Number of likes",
            "type": "STRING",
        },
        "comment_count": {
            "label": "Comment Count",
            "description": "Number of comments",
            "type": "STRING",
        },
        "tags": {
            "label": "Tags",
            "description": "Video tags",
            "type": "STRING",
        },
        "categories": {
            "label": "Categories",
            "description": "Video categories",
            "type": "STRING",
        },
        "channel_id": {
            "label": "Channel ID",
            "description": "ID of the channel",
            "type": "STRING",
        }
    }

    def _format_lang_list(self, langs: List[str]) -> str:
        """Format language list into a readable string"""
        if not langs:
            return "None"
        return ", ".join(sorted(langs))

    def _format_list(self, items: List[str]) -> str:
        """Format list into a readable string"""
        if not items:
            return ""
        return ", ".join(items)

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            url = node_inputs["url"]
            cookie_file = node_inputs.get("cookie_file", "")
            
            workflow_logger.info(f"Fetching info for: {url}")

            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'writesubtitles': True,
                'listsubtitles': True,
            }

            # 处理cookie文件
            if cookie_file:
                netscape_cookie_file = get_cookie_file(cookie_file)
                if netscape_cookie_file:
                    workflow_logger.info("Using provided cookie file")
                    ydl_opts['cookiefile'] = netscape_cookie_file
                else:
                    workflow_logger.warning("Invalid cookie file format")

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            # 格式化时长
            duration = info.get('duration')
            if duration:
                hours = duration // 3600
                minutes = (duration % 3600) // 60
                seconds = duration % 60
                duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                duration_str = "Unknown"

            # 格式化观看次数
            view_count = info.get('view_count')
            if view_count:
                if view_count >= 1000000:
                    view_count_str = f"{view_count/1000000:.1f}M"
                elif view_count >= 1000:
                    view_count_str = f"{view_count/1000:.1f}K"
                else:
                    view_count_str = str(view_count)
            else:
                view_count_str = "Unknown"

            # 获取字幕信息
            subtitles = info.get('subtitles', {})
            auto_captions = info.get('automatic_captions', {})

            # 格式化字幕语言列表
            subtitle_langs = self._format_lang_list(subtitles.keys())
            auto_caption_langs = self._format_lang_list(auto_captions.keys())

            # 格式化标签和分类
            tags = self._format_list(info.get('tags', []))
            categories = self._format_list(info.get('categories', []))

            workflow_logger.info(f"Found {len(subtitles)} manual subtitles and {len(auto_captions)} auto-generated captions")

            return {
                "success": True,
                "title": info.get('title', 'Unknown'),
                "duration": duration_str,
                "view_count": view_count_str,
                "thumbnail": info.get('thumbnail', ''),
                "description": info.get('description', ''),
                "subtitles": subtitle_langs,
                "auto_captions": auto_caption_langs,
                "uploader_id": info.get('uploader_id', ''),
                "release_date": info.get('release_date', ''),
                "availability": info.get('availability', ''),
                "like_count": str(info.get('like_count', 0)),
                "comment_count": str(info.get('comment_count', 0)),
                "tags": tags,
                "categories": categories,
                "channel_id": info.get('channel_id', '')
            }

        except Exception as e:
            workflow_logger.error(f"Info extraction failed: {str(e)}")
            return {
                "success": False,
                "error_message": str(e)
            } 