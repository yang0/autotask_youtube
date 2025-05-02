try:
    from autotask.nodes import Node, register_node
except ImportError:
    from stub import Node, register_node

import os
import sys
from typing import Dict, Any, List

# Add youtube-dl to the path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'youtube-dl'))

from .youtube_dl_lazy import _get_youtube_dl

@register_node
class YouTubeSearchNode(Node):
    NAME = "YouTube Search"
    DESCRIPTION = "Search for videos on YouTube"

    INPUTS = {
        "query": {
            "label": "Search Query",
            "description": "Search query to find videos",
            "type": "STRING",
            "required": True,
        },
        "max_results": {
            "label": "Max Results",
            "description": "Maximum number of results to return",
            "type": "INT",
            "default": 10,
            "required": False,
            "min": 1,
            "max": 50,
        },
        "order": {
            "label": "Sort Order",
            "description": "Sort order for results",
            "type": "COMBO",
            "default": "relevance",
            "required": False,
            "options": ["relevance", "date", "rating", "viewCount", "title"],
        },
        "upload_date": {
            "label": "Upload Date",
            "description": "Filter by upload date",
            "type": "COMBO",
            "default": "",
            "required": False,
            "options": ["", "today", "week", "month", "year"],
        },
        "duration": {
            "label": "Duration",
            "description": "Filter by video duration",
            "type": "COMBO",
            "default": "",
            "required": False,
            "options": ["", "short", "medium", "long"],
        },
    }

    OUTPUTS = {
        "videos": {
            "label": "Videos",
            "description": "List of found videos",
            "type": "LIST",
        },
        "total_results": {
            "label": "Total Results",
            "description": "Total number of videos found",
            "type": "INT",
        },
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        try:
            query = node_inputs["query"]
            max_results = node_inputs.get("max_results", 10)
            order = node_inputs.get("order", "relevance")
            upload_date = node_inputs.get("upload_date", "")
            duration = node_inputs.get("duration", "")

            workflow_logger.info(f"Searching YouTube for: {query}")

            # Configure youtube-dl options
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
            }

            # Build the search query
            search_query = query
            
            # Add filters if specified
            if upload_date:
                search_query += f" upload_date:{upload_date}"
            
            if duration:
                search_query += f" duration:{duration}"
            
            # Add the search query to the options
            ydl_opts['default_search'] = f"ytsearch{max_results}:{search_query}"
            
            # Set the sort order
            if order != "relevance":
                ydl_opts['default_search'] += f" --sort-by {order}"

            # Search for videos
            videos = []
            youtube_dl = _get_youtube_dl()
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                # Extract the search results
                results = ydl.extract_info(f"ytsearch{max_results}:{search_query}", download=False)
                
                if 'entries' not in results:
                    workflow_logger.error("No search results found")
                    return {
                        "success": False,
                        "error_message": "No search results found",
                        "videos": [],
                        "total_results": 0
                    }
                
                # Process each video in the search results
                for entry in results['entries']:
                    if entry is None:
                        continue
                    
                    video_id = entry.get('id', '')
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    
                    video_info = {
                        "video_id": video_id,
                        "title": entry.get('title', ''),
                        "description": entry.get('description', ''),
                        "duration": entry.get('duration', 0),
                        "uploader": entry.get('uploader', ''),
                        "upload_date": entry.get('upload_date', ''),
                        "view_count": entry.get('view_count', 0),
                        "thumbnail_url": entry.get('thumbnail', ''),
                        "url": video_url,
                    }
                    videos.append(video_info)
                    workflow_logger.info(f"Found video: {video_info['title']}")

            total_results = len(videos)
            workflow_logger.info(f"Found {total_results} videos")
            
            return {
                "success": True,
                "videos": videos,
                "total_results": total_results
            }

        except Exception as e:
            workflow_logger.error(f"YouTube search failed: {str(e)}")
            return {
                "success": False,
                "error_message": str(e),
                "videos": [],
                "total_results": 0
            } 