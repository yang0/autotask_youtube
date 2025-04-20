import os
import youtube_dl
from autotask_nodes import Node
from .cookie_utils import get_cookie_file

class YouTubeChannelDownloadNode(Node):
    """
    Node for downloading all videos from a YouTube channel.
    """
    CATEGORY = "YouTube"
    VERSION = "1.0.0"
    AUTHOR = "AutoTask"
    TAGS = ["youtube", "download", "channel", "video"]

    INPUTS = {
        "channel_url": {
            "label": "Channel URL",
            "description": "URL of the YouTube channel to download",
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

    def run(self, **kwargs):
        channel_url = kwargs.get("channel_url")
        output_dir = kwargs.get("output_dir", "")
        format = kwargs.get("format", "best")
        extract_audio = kwargs.get("extract_audio", False)
        audio_format = kwargs.get("audio_format", "mp3")
        audio_quality = kwargs.get("audio_quality", 5)
        cookie_file = kwargs.get("cookie_file", "")

        if not channel_url:
            raise ValueError("Channel URL is required")

        # Convert cookie file if provided
        if cookie_file:
            cookie_file = get_cookie_file(cookie_file)

        # Prepare youtube-dl options
        ydl_opts = {
            "format": format,
            "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s") if output_dir else "%(title)s.%(ext)s",
            "quiet": True,
            "no_warnings": True,
        }

        if cookie_file:
            ydl_opts["cookiefile"] = cookie_file

        if extract_audio:
            ydl_opts.update({
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": audio_format,
                    "preferredquality": str(audio_quality),
                }],
            })

        # Download all videos from the channel
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            try:
                # Extract channel information
                channel_info = ydl.extract_info(channel_url, download=False)
                
                # Get all video URLs from the channel
                video_urls = []
                for entry in channel_info.get("entries", []):
                    if entry:
                        video_urls.append(entry["url"])
                
                # Download all videos
                file_paths = []
                titles = []
                durations = []
                
                for video_url in video_urls:
                    try:
                        # Download the video
                        info = ydl.extract_info(video_url, download=True)
                        
                        # Get the file path
                        if extract_audio:
                            file_path = os.path.join(output_dir, f"{info['title']}.{audio_format}") if output_dir else f"{info['title']}.{audio_format}"
                        else:
                            file_path = os.path.join(output_dir, f"{info['title']}.{info['ext']}") if output_dir else f"{info['title']}.{info['ext']}"
                        
                        file_paths.append(file_path)
                        titles.append(info["title"])
                        durations.append(info.get("duration", 0))
                    except Exception as e:
                        print(f"Error downloading video {video_url}: {str(e)}")
                
                return {
                    "file_paths": file_paths,
                    "titles": titles,
                    "durations": durations,
                }
            except Exception as e:
                raise Exception(f"Error downloading channel videos: {str(e)}") 