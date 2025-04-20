VERSION = "0.0.1"
GIT_URL = "https://github.com/yang0/autotask_youtube.git"
NAME = "Youtube相关功能"
DESCRIPTION = "Youtube相关功能"
TAGS=["Youtube"]

# Import all nodes
from .download import YouTubeDownloadNode
from .playlist_download import YouTubePlaylistDownloadNode
from .video_info import YouTubeVideoInfoNode
from .subtitle_download import YouTubeSubtitleDownloadNode
from .search import YouTubeSearchNode
from .channel_download import YouTubeChannelDownloadNode
