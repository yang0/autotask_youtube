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

# Import cookie utilities
from .cookie_utils import get_cookie_file
from .youtube_dl_lazy import _get_youtube_dl

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
            "type": "COMBO",
            "default": "best",
            "required": False,
            "options": ["best", "worst", "bestvideo", "worstvideo", "bestaudio", "worstaudio"],
        },
        "extract_audio": {
            "label": "Extract Audio",
            "description": "Extract audio from the videos",
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
            "widget": "INT",
            "min": 0,
            "max": 9,
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
        "playlist_start": {
            "label": "Start Index",
            "description": "Playlist video to start at (default is 1)",
            "type": "INT",
            "default": 1,
            "required": False,
            "widget": "INT",
            "min": 1,
        },
        "playlist_end": {
            "label": "End Index",
            "description": "Playlist video to end at (default is last)",
            "type": "INT",
            "default": -1,
            "required": False,
            "widget": "INT",
            "min": -1,
        },
        "playlist_reverse": {
            "label": "Reverse Order",
            "description": "Download playlist videos in reverse order",
            "type": "BOOLEAN",
            "default": False,
            "required": False
        },
        "playlist_random": {
            "label": "Random Order",
            "description": "Download playlist videos in random order",
            "type": "BOOLEAN",
            "default": False,
            "required": False
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
        "subtitle_files": {
            "label": "Subtitle Files",
            "description": "List of paths to downloaded subtitle files for each video",
            "type": "LIST",
            "default": [],
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
            playlist_url = node_inputs["playlist_url"]
            output_dir = node_inputs.get("output_dir", "")
            format = node_inputs.get("format", "best")
            extract_audio = node_inputs.get("extract_audio", False)
            audio_format = node_inputs.get("audio_format", "mp3")
            audio_quality = node_inputs.get("audio_quality", 5)
            cookie_file = node_inputs.get("cookie_file", "")
            
            # 获取播放列表特定参数
            playlist_start = node_inputs.get("playlist_start", 1)
            playlist_end = node_inputs.get("playlist_end", -1)
            playlist_reverse = node_inputs.get("playlist_reverse", False)
            playlist_random = node_inputs.get("playlist_random", False)
            
            # 字幕相关参数
            write_subs = node_inputs.get("write_subs", False)
            write_auto_subs = node_inputs.get("write_auto_subs", False)
            sub_langs = node_inputs.get("sub_langs", "en")

            workflow_logger.info(f"Starting download of YouTube playlist: {playlist_url}")
            if playlist_start > 1:
                workflow_logger.info(f"Starting from video #{playlist_start}")
            if playlist_end != -1:
                workflow_logger.info(f"Ending at video #{playlist_end}")
            if playlist_reverse:
                workflow_logger.info("Downloading in reverse order")
            if playlist_random:
                workflow_logger.info("Downloading in random order")

            # Create a temporary directory if no output directory is specified
            if not output_dir:
                output_dir = tempfile.mkdtemp()
                workflow_logger.info(f"Using temporary directory: {output_dir}")

            # Configure youtube-dl options
            ydl_opts = {
                'format': format,
                'outtmpl': os.path.join(output_dir, '%(title)s-%(id)s.%(ext)s') if output_dir else '%(title)s-%(id)s.%(ext)s',
                'verbose': True,
                'progress_hooks': [self._progress_hook],
                'extract_flat': False,  # 获取完整的视频信息
                'writethumbnail': True,
                'writeinfojson': True,
                'ignoreerrors': True,
                'nooverwrites': True,
                'restrictfilenames': True,  # 避免文件名中的特殊字符
                'playlistreverse': playlist_reverse,  # 是否反向下载
                'playlistrandom': playlist_random,  # 是否随机顺序
                'playliststart': playlist_start,  # 起始视频索引
                'playlistend': playlist_end if playlist_end != -1 else None,  # 结束视频索引
                'writesubtitles': write_subs,  # 是否下载字幕
                'writeautomaticsub': write_auto_subs,  # 是否下载自动生成的字幕
                'subtitleslangs': sub_langs.split(',') if sub_langs != 'all' else ['all'],  # 字幕语言列表
            }

            # Add cookie file if provided
            if cookie_file:
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
            file_paths = []
            titles = []
            durations = []
            subtitle_files = []
            errors = []
            
            try:
                youtube_dl = _get_youtube_dl()
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    self._ydl = ydl
                    # First extract playlist info without downloading
                    workflow_logger.info("Extracting playlist information...")
                    playlist_info = ydl.extract_info(playlist_url, download=False)
                    
                    if self._is_interrupted:
                        return {
                            "success": False,
                            "error_message": "Download interrupted during playlist info extraction"
                        }

                    total_videos = len(playlist_info['entries'])
                    workflow_logger.info(f"Found {total_videos} videos in playlist")
                    
                    # Download each video
                    for i, entry in enumerate(playlist_info['entries'], 1):
                        if self._is_interrupted:
                            break
                            
                        if not entry:
                            error_msg = f"Failed to get info for video {i}"
                            workflow_logger.error(error_msg)
                            errors.append(error_msg)
                            continue
                            
                        try:
                            workflow_logger.info(f"Downloading video {i}/{total_videos}: {entry.get('title', 'Unknown Title')}")
                            
                            # Download the video
                            video_info = ydl.process_ie_result(entry, download=True)
                            
                            if not video_info:
                                error_msg = f"Failed to download video {i}"
                                workflow_logger.error(error_msg)
                                errors.append(error_msg)
                                continue
                            
                            # Get the file path
                            if extract_audio:
                                file_path = os.path.join(output_dir, f"{video_info['title']}-{video_info['id']}.{audio_format}") if output_dir else f"{video_info['title']}-{video_info['id']}.{audio_format}"
                            else:
                                file_path = os.path.join(output_dir, f"{video_info['title']}-{video_info['id']}.{video_info['ext']}") if output_dir else f"{video_info['title']}-{video_info['id']}.{video_info['ext']}"
                            
                            file_paths.append(file_path)
                            titles.append(video_info.get('title', 'Unknown Title'))
                            durations.append(video_info.get('duration', 0))
                            
                            # 获取字幕文件路径
                            video_subtitle_files = []
                            if (write_subs or write_auto_subs) and 'requested_subtitles' in video_info:
                                base_name = os.path.splitext(file_path)[0]
                                for lang in video_info['requested_subtitles']:
                                    sub_file = f"{base_name}.{lang}.vtt"
                                    if os.path.exists(sub_file):
                                        video_subtitle_files.append(sub_file)
                                        workflow_logger.info(f"Found subtitle file: {sub_file}")
                            subtitle_files.append(video_subtitle_files)
                            
                            workflow_logger.info(f"Successfully downloaded: {video_info.get('title', 'Unknown Title')}")
                            if video_subtitle_files:
                                workflow_logger.info(f"Downloaded {len(video_subtitle_files)} subtitle files for this video")
                                
                        except Exception as e:
                            error_msg = f"Error downloading video {entry.get('id', '')}: {str(e)}"
                            workflow_logger.error(error_msg)
                            errors.append(error_msg)
                            continue
            finally:
                self._ydl = None
                self._is_interrupted = False

            successful_downloads = len(file_paths)
            
            if self._is_interrupted:
                workflow_logger.info(f"Download interrupted after downloading {successful_downloads}/{total_videos} videos")
                return {
                    "success": successful_downloads > 0,
                    "error_message": f"Download interrupted. Successfully downloaded {successful_downloads}/{total_videos} videos",
                    "file_paths": file_paths,
                    "titles": titles,
                    "durations": durations,
                    "subtitle_files": subtitle_files,
                    "errors": errors
                }
            
            if successful_downloads == 0:
                workflow_logger.error("No videos were successfully downloaded")
                return {
                    "success": False,
                    "error_message": "Failed to download any videos",
                    "errors": errors
                }
            
            workflow_logger.info(f"Successfully downloaded {successful_downloads}/{total_videos} videos")
            return {
                "success": True,
                "file_paths": file_paths,
                "titles": titles,
                "durations": durations,
                "subtitle_files": subtitle_files,
                "errors": errors,
                "total_videos": total_videos,
                "successful_downloads": successful_downloads
            }

        except Exception as e:
            workflow_logger.error(f"YouTube playlist download failed: {str(e)}")
            return {
                "success": False,
                "error_message": str(e)
            } 