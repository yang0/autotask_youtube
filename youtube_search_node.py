try:
    from autotask.nodes import Node, register_node
except ImportError:
    from stub import Node, register_node

from .cookie_utils import get_cookie_file
from typing import Dict, Any
import yt_dlp
import os

@register_node
class YouTubeSearchNode(Node):
    NAME = "YouTube Search"
    DESCRIPTION = "Search videos on YouTube"
    CATEGORY = "YouTube"
    MAINTAINER = "AutoTask"
    VERSION = "1.0.0"
    ICON = "🔍"

    INPUTS = {
        "search_query": {
            "label": "Search Query",
            "description": "Keywords to search for",
            "type": "STRING",
            "required": True,
            "placeholder": "Enter search keywords"
        },
        "max_results": {
            "label": "Maximum Results",
            "description": "Maximum number of search results to return",
            "type": "INT",
            "required": True,
            "default": 5,
            "minimum": 1,
            "maximum": 50
        },
        "sort_by": {
            "label": "Sort By",
            "description": "How to sort the search results",
            "type": "STRING",
            "required": True,
            "default": "relevance",
            "choices": ["relevance", "rating", "upload_date", "view_count"],
            "placeholder": "Select sort method"
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
        "video_urls": {
            "label": "Video URLs",
            "description": "List of found video URLs",
            "type": "LIST"
        },
        "video_titles": {
            "label": "Video Titles",
            "description": "List of found video titles",
            "type": "LIST"
        }
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            search_query = node_inputs["search_query"]
            max_results = node_inputs["max_results"]
            sort_by = node_inputs["sort_by"]
            cookie_file = node_inputs.get("cookie_file", "")

            # 构建搜索URL
            search_url = f"ytsearch{max_results}:{search_query}"
            if sort_by != "relevance":
                search_url = f"ytsearch{max_results}:{search_query}, {sort_by}"

            workflow_logger.info(f"Searching YouTube for: {search_query}")

            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,  # 只获取基本信息
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
                results = ydl.extract_info(search_url, download=False)
                
                if not results or 'entries' not in results:
                    workflow_logger.warning("No results found")
                    return {
                        "success": False,
                        "error_message": "No results found"
                    }

                entries = results['entries']
                
                # 收集结果
                video_urls = []
                video_titles = []
                video_descriptions = []

                for entry in entries:
                    if entry:
                        video_urls.append(f"https://www.youtube.com/watch?v={entry['id']}")
                        video_titles.append(entry.get('title', 'Unknown Title'))

            workflow_logger.info(f"Found {len(video_urls)} videos")

            return {
                "success": True,
                "video_urls": video_urls,
                "video_titles": video_titles
            }

        except Exception as e:
            workflow_logger.error(f"Search failed: {str(e)}")
            return {
                "success": False,
                "error_message": str(e)
            } 