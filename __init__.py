VERSION = "0.0.1"
GIT_URL = "https://github.com/yang0/autotask_youtube.git"
NAME = "YouTube 下载工具"
DESCRIPTION = "提供 YouTube 视频、播放列表、频道的下载和字幕提取功能"
TAGS = ["YouTube", "下载", "视频", "字幕", "自动化"]

# Import all nodes
from .download import YouTubeDownloadNode
from .video_info import YouTubeVideoInfoNode
from .playlist_download import YouTubePlaylistDownloadNode
from .subtitle_download import YouTubeSubtitleDownloadNode
from .search import YouTubeSearchNode
from .channel_download import YouTubeChannelDownloadNode

