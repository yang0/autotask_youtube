# AutoTask YouTube Plugin

This plugin provides nodes for downloading videos, playlists, and channels from YouTube using the youtube-dl library.

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure you have ffmpeg installed on your system for audio extraction.

## Nodes

### YouTube Download Node

Downloads a single video from YouTube.

**Inputs:**
- `video_url` (required): URL of the YouTube video to download
- `output_dir`: Directory to save the downloaded video
- `format`: Format code for the video (e.g., 'best', 'bestvideo+bestaudio', 'mp4')
- `extract_audio`: Whether to extract audio from the video
- `audio_format`: Format for the extracted audio (e.g., 'mp3', 'm4a')
- `audio_quality`: Quality of the extracted audio (0-9, where 0 is best)
- `cookie_file`: Path to a cookie file for authentication

**Outputs:**
- `file_path`: Path to the downloaded file
- `title`: Title of the downloaded video
- `duration`: Duration of the video in seconds

### YouTube Playlist Download Node

Downloads all videos from a YouTube playlist.

**Inputs:**
- `playlist_url` (required): URL of the YouTube playlist to download
- `output_dir`: Directory to save the downloaded videos
- `format`: Format code for the videos
- `extract_audio`: Whether to extract audio from the videos
- `audio_format`: Format for the extracted audio
- `audio_quality`: Quality of the extracted audio
- `cookie_file`: Path to a cookie file for authentication

**Outputs:**
- `file_paths`: List of paths to the downloaded files
- `titles`: List of titles of the downloaded videos
- `durations`: List of durations of the videos in seconds

### YouTube Channel Download Node

Downloads all videos from a YouTube channel.

**Inputs:**
- `channel_url` (required): URL of the YouTube channel to download
- `output_dir`: Directory to save the downloaded videos
- `format`: Format code for the videos
- `extract_audio`: Whether to extract audio from the videos
- `audio_format`: Format for the extracted audio
- `audio_quality`: Quality of the extracted audio
- `cookie_file`: Path to a cookie file for authentication

**Outputs:**
- `file_paths`: List of paths to the downloaded files
- `titles`: List of titles of the downloaded videos
- `durations`: List of durations of the videos in seconds

### YouTube Video Info Node

Extracts information about a YouTube video without downloading it.

**Inputs:**
- `video_url` (required): URL of the YouTube video
- `cookie_file`: Path to a cookie file for authentication

**Outputs:**
- `title`: Title of the video
- `description`: Description of the video
- `duration`: Duration of the video in seconds
- `upload_date`: Date when the video was uploaded
- `view_count`: Number of views
- `like_count`: Number of likes
- `comment_count`: Number of comments
- `formats`: List of available formats

### YouTube Subtitle Download Node

Downloads subtitles for a YouTube video.

**Inputs:**
- `video_url` (required): URL of the YouTube video
- `output_dir`: Directory to save the subtitles
- `languages`: List of languages to download (e.g., ['en', 'es'])
- `cookie_file`: Path to a cookie file for authentication

**Outputs:**
- `subtitle_paths`: List of paths to the downloaded subtitle files
- `languages`: List of languages of the downloaded subtitles

### YouTube Search Node

Searches for videos on YouTube.

**Inputs:**
- `query` (required): Search query
- `max_results`: Maximum number of results to return
- `cookie_file`: Path to a cookie file for authentication

**Outputs:**
- `video_urls`: List of URLs of the found videos
- `titles`: List of titles of the found videos
- `descriptions`: List of descriptions of the found videos
- `durations`: List of durations of the found videos in seconds

## Cookie File Authentication

To download age-restricted or private videos, you can use a cookie file from your browser. The cookie file should be in the format exported by browser extensions like "Get cookies.txt" or "Cookie-Editor".

Example cookie file path: `www.youtube.com.json`

## Examples

### Download a single video
```python
from autotask_youtube import YouTubeDownloadNode

node = YouTubeDownloadNode()
result = node.run(
    video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    output_dir="./downloads",
    format="best",
    extract_audio=True,
    audio_format="mp3",
    audio_quality=5
)

print(f"Downloaded: {result['file_path']}")
print(f"Title: {result['title']}")
print(f"Duration: {result['duration']} seconds")
```

### Download a playlist
```python
from autotask_youtube import YouTubePlaylistDownloadNode

node = YouTubePlaylistDownloadNode()
result = node.run(
    playlist_url="https://www.youtube.com/playlist?list=PLxxxxxxxx",
    output_dir="./downloads",
    format="best",
    extract_audio=True,
    audio_format="mp3",
    audio_quality=5
)

for i, (path, title, duration) in enumerate(zip(result['file_paths'], result['titles'], result['durations'])):
    print(f"Video {i+1}:")
    print(f"  Path: {path}")
    print(f"  Title: {title}")
    print(f"  Duration: {duration} seconds")
```

### Download a channel
```python
from autotask_youtube import YouTubeChannelDownloadNode

node = YouTubeChannelDownloadNode()
result = node.run(
    channel_url="https://www.youtube.com/channel/UCxxxxxxxx",
    output_dir="./downloads",
    format="best",
    extract_audio=True,
    audio_format="mp3",
    audio_quality=5
)

for i, (path, title, duration) in enumerate(zip(result['file_paths'], result['titles'], result['durations'])):
    print(f"Video {i+1}:")
    print(f"  Path: {path}")
    print(f"  Title: {title}")
    print(f"  Duration: {duration} seconds")
```

### Get video information
```python
from autotask_youtube import YouTubeVideoInfoNode

node = YouTubeVideoInfoNode()
result = node.run(
    video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
)

print(f"Title: {result['title']}")
print(f"Description: {result['description']}")
print(f"Duration: {result['duration']} seconds")
print(f"Upload Date: {result['upload_date']}")
print(f"Views: {result['view_count']}")
print(f"Likes: {result['like_count']}")
print(f"Comments: {result['comment_count']}")
```

### Download subtitles
```python
from autotask_youtube import YouTubeSubtitleDownloadNode

node = YouTubeSubtitleDownloadNode()
result = node.run(
    video_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    output_dir="./subtitles",
    languages=["en", "es"]
)

for path, lang in zip(result['subtitle_paths'], result['languages']):
    print(f"Downloaded {lang} subtitles: {path}")
```

### Search for videos
```python
from autotask_youtube import YouTubeSearchNode

node = YouTubeSearchNode()
result = node.run(
    query="never gonna give you up",
    max_results=5
)

for i, (url, title, desc, duration) in enumerate(zip(
    result['video_urls'],
    result['titles'],
    result['descriptions'],
    result['durations']
)):
    print(f"Result {i+1}:")
    print(f"  URL: {url}")
    print(f"  Title: {title}")
    print(f"  Description: {desc}")
    print(f"  Duration: {duration} seconds")
```

## License

This plugin is licensed under the MIT License. See the LICENSE file for details.

AutoTask.dev User Id: buKkhpRSxA9LT4zZ6GDKH9
