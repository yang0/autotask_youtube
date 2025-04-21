import os
import youtube_dl
try:
    from autotask.nodes import Node, register_node
except ImportError:
    from stub import Node, register_node
from .cookie_utils import get_cookie_file
from typing import Dict, Any

@register_node
class YouTubeChannelDownloadNode(Node):
    """
    Node for downloading all videos from a YouTube channel.
    """
    NAME = "YouTube Channel Download"
    DESCRIPTION = "Download all videos from a YouTube channel"

    INPUTS = {
        "channel_url": {
            "label": "Channel URL",
            "description": "URL of the YouTube channel to download",
            "type": "STRING",
            "required": True,
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
        },
        "titles": {
            "label": "Video Titles",
            "description": "Titles of the downloaded videos",
            "type": "LIST",
        },
        "durations": {
            "label": "Durations",
            "description": "Durations of the videos in seconds",
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
            channel_url = node_inputs["channel_url"]
            output_dir = node_inputs.get("output_dir", "")
            format = node_inputs.get("format", "best")
            extract_audio = node_inputs.get("extract_audio", False)
            audio_format = node_inputs.get("audio_format", "mp3")
            audio_quality = node_inputs.get("audio_quality", 5)
            cookie_file = node_inputs.get("cookie_file", "")

            workflow_logger.info(f"Starting download of YouTube channel: {channel_url}")

            # Configure youtube-dl options
            ydl_opts = {
                'format': format,
                'outtmpl': os.path.join(output_dir, '%(title)s-%(id)s.%(ext)s') if output_dir else '%(title)s-%(id)s.%(ext)s',
                'verbose': True,  # Add verbose mode for debugging
                'progress_hooks': [self._progress_hook],  # Add progress hook to check for interruption
                'writethumbnail': True,
                'writeinfojson': True,
                'ignoreerrors': True,
                'nooverwrites': True,
                'restrictfilenames': True,  # 避免文件名中的特殊字符
                'extract_flat': False,  # 确保获取完整的视频信息
                'force_generic_extractor': False
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

            try:
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    self._ydl = ydl
                    # Extract channel information
                    workflow_logger.info("Extracting channel information...")
                    channel_info = ydl.extract_info(channel_url, download=False)
                    
                    if self._is_interrupted:
                        workflow_logger.info("Download was interrupted after channel info extraction")
                        return {
                            "success": False,
                            "error_message": "Download interrupted after channel info extraction"
                        }

                    # Get all video URLs from the channel
                    video_urls = []
                    for entry in channel_info.get("entries", []):
                        if entry and not self._is_interrupted:
                            # 保存完整的视频信息而不是仅仅URL
                            video_urls.append(entry)
                    
                    if self._is_interrupted:
                        workflow_logger.info("Download was interrupted while collecting video URLs")
                        return {
                            "success": False,
                            "error_message": "Download interrupted while collecting video URLs"
                        }

                    workflow_logger.info(f"Found {len(video_urls)} videos in channel")
                    
                    # Download all videos
                    file_paths = []
                    titles = []
                    durations = []
                    errors = []
                    
                    for i, video_info in enumerate(video_urls, 1):
                        if self._is_interrupted:
                            break
                            
                        try:
                            workflow_logger.info(f"Downloading video {i}/{len(video_urls)}")
                            # Download the video using saved info
                            info = ydl.process_ie_result(video_info, download=True)
                            
                            if not info:
                                error_msg = f"Failed to get video info for video {i}"
                                workflow_logger.error(error_msg)
                                errors.append(error_msg)
                                continue
                                
                            # Get the file path
                            if extract_audio:
                                file_path = os.path.join(output_dir, f"{info['title']}-{info['id']}.{audio_format}") if output_dir else f"{info['title']}-{info['id']}.{audio_format}"
                            else:
                                file_path = os.path.join(output_dir, f"{info['title']}-{info['id']}.{info['ext']}") if output_dir else f"{info['title']}-{info['id']}.{info['ext']}"
                            
                            file_paths.append(file_path)
                            titles.append(info.get("title", "Unknown Title"))
                            durations.append(info.get("duration", 0))
                            
                            workflow_logger.info(f"Successfully downloaded: {info.get('title', 'Unknown Title')}")
                        except Exception as e:
                            error_msg = f"Error downloading video {video_info.get('id', '')}: {str(e)}"
                            workflow_logger.error(error_msg)
                            errors.append(error_msg)
                            continue
                    
                    total_videos = len(video_urls)
                    successful_downloads = len(file_paths)
                    
                    if self._is_interrupted:
                        workflow_logger.info(f"Download interrupted after downloading {successful_downloads}/{total_videos} videos")
                        return {
                            "success": successful_downloads > 0,  # 如果至少下载了一个视频就算部分成功
                            "error_message": f"Download interrupted. Successfully downloaded {successful_downloads}/{total_videos} videos",
                            "file_paths": file_paths,
                            "titles": titles,
                            "durations": durations,
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
                        "errors": errors,
                        "partial_success": successful_downloads < total_videos,
                        "total_videos": total_videos,
                        "successful_downloads": successful_downloads
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
            workflow_logger.error(f"YouTube channel download failed: {str(e)}")
            return {
                "success": False,
                "error_message": str(e)
            } 