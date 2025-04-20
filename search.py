try:
    from autotask.nodes import GeneratorNode, register_node
except ImportError:
    from stub import GeneratorNode, register_node

import os
import sys
from typing import Dict, Any, AsyncGenerator

# Add youtube-dl to the path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'youtube-dl'))
import youtube_dl


@register_node
class YouTubeSearchNode(GeneratorNode):
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
        },
        "order": {
            "label": "Sort Order",
            "description": "Sort order for results (relevance, date, rating, viewCount, title, videoCount)",
            "type": "STRING",
            "default": "relevance",
            "required": False,
        },
        "upload_date": {
            "label": "Upload Date",
            "description": "Filter by upload date (today, week, month, year)",
            "type": "STRING",
            "default": "",
            "required": False,
        },
        "duration": {
            "label": "Duration",
            "description": "Filter by duration (short, medium, long)",
            "type": "STRING",
            "default": "",
            "required": False,
        },
    }

    OUTPUTS = {
        "video_id": {
            "label": "Video ID",
            "description": "ID of the video",
            "type": "STRING",
        },
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
        "thumbnail_url": {
            "label": "Thumbnail URL",
            "description": "URL of the video thumbnail",
            "type": "STRING",
        },
        "url": {
            "label": "Video URL",
            "description": "URL of the video",
            "type": "STRING",
        },
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> AsyncGenerator[Any, None]:
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
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                # Extract the search results
                results = ydl.extract_info(f"ytsearch{max_results}:{search_query}", download=False)
                
                if 'entries' not in results:
                    workflow_logger.error("No search results found")
                    return
                
                # Process each video in the search results
                for entry in results['entries']:
                    if entry is None:
                        continue
                    
                    video_id = entry.get('id', '')
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    
                    workflow_logger.info(f"Found video: {entry.get('title', 'Unknown')}")
                    
                    # Yield the result
                    yield {
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

        except Exception as e:
            workflow_logger.error(f"YouTube search failed: {str(e)}")
            return 