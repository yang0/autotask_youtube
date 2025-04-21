# AutoTask YouTube 插件

[English](README.md) | 简体中文

这是一个功能强大的 YouTube 下载工具插件，基于 youtube-dl 库开发，提供视频、播放列表、频道的下载以及字幕提取等功能。

## 使用方式

本插件支持两种使用方式：

1. **通过 AutoTask 软件界面使用**

你可以通过以下方式获取并使用本插件：
- 在 AutoTask 软件的插件栏目中搜索并安装 "YouTube 下载工具" 插件
- 或者下载包含 YouTube 相关功能的工作流，系统会自动安装所需插件

安装完成后，你可以直接在 AutoTask 软件中使用图形界面操作所有功能：

![AutoTask YouTube 插件界面](images/screen_shot.png)

2. **通过 MCP 接口调用**

AutoTask 内置了 MCP 服务器，安装插件后你可以通过 MCP 接口在其他程序中调用插件功能：
- MCP 服务器地址：`http://localhost:8283/mcp/sse`
- 将此地址复制到 Cursor 或其他开发环境中即可通过 MCP 协议调用插件功能

## Cookie 文件

对于需要登录的视频，可以直接使用 AutoTask 软件生成所需的 cookie 文件。

## 功能特点

- 支持下载单个视频、播放列表和整个频道
- 支持提取视频信息（标题、描述、时长等）
- 支持下载字幕（包括自动生成的字幕）
- 支持音频提取（多种格式和质量选项）
- 支持搜索 YouTube 视频
- 支持需要登录的视频下载（通过 cookie）
- 支持自定义输出格式和质量
- 支持断点续传和错误重试

## 安装要求

1. 安装依赖包：
```bash
pip install -r requirements.txt
```

2. 确保系统已安装 ffmpeg（用于音频提取和格式转换）

## 可用节点

### YouTube 视频下载节点 (YouTubeDownloadNode)

下载单个 YouTube 视频。

**输入参数：**
- `url`（必需）：YouTube 视频链接
- `output_dir`：输出目录
- `format`：视频格式代码（如 'best', 'bestvideo+bestaudio', 'mp4'）
- `extract_audio`：是否提取音频
- `audio_format`：音频格式（如 'mp3', 'm4a'）
- `audio_quality`：音频质量（0-9，0为最佳）
- `write_subs`：是否下载字幕
- `write_auto_subs`：是否下载自动生成的字幕
- `sub_langs`：字幕语言（如 'en,zh-CN'，使用 'all' 下载所有语言）
- `cookie_file`：cookie 文件路径（用于需要登录的视频）

**输出参数：**
- `file_path`：下载文件的路径
- `title`：视频标题
- `duration`：视频时长（秒）
- `subtitle_files`：字幕文件路径列表

### YouTube 播放列表下载节点 (YouTubePlaylistDownloadNode)

下载整个 YouTube 播放列表。

**输入参数：**
- `playlist_url`（必需）：播放列表链接
- `output_dir`：输出目录
- `format`：视频格式
- `extract_audio`：是否提取音频
- `audio_format`：音频格式
- `audio_quality`：音频质量
- `write_subs`：是否下载字幕
- `write_auto_subs`：是否下载自动生成的字幕
- `sub_langs`：字幕语言
- `cookie_file`：cookie 文件路径
- `playlist_start`：起始视频索引（从1开始）
- `playlist_end`：结束视频索引（-1表示直到列表末尾）
- `playlist_reverse`：是否倒序下载
- `playlist_random`：是否随机顺序下载

**输出参数：**
- `file_paths`：下载文件路径列表
- `titles`：视频标题列表
- `durations`：视频时长列表
- `subtitle_files`：字幕文件路径列表（每个视频对应一个列表）

### YouTube 频道下载节点 (YouTubeChannelDownloadNode)

下载 YouTube 频道的所有视频。

**输入参数：**
与播放列表下载节点类似，但使用 `channel_url` 替代 `playlist_url`。

### YouTube 视频信息节点 (YouTubeVideoInfoNode)

获取视频信息而不下载视频。

**输入参数：**
- `url`（必需）：视频链接
- `cookie_file`：cookie 文件路径

**输出参数：**
- `title`：视频标题
- `description`：视频描述
- `duration`：视频时长
- `uploader`：上传者
- `upload_date`：上传日期
- `view_count`：观看次数
- `like_count`：点赞数
- `comment_count`：评论数
- `formats`：可用格式列表
- `raw_info`：原始信息（JSON格式）

### YouTube 字幕下载节点 (YouTubeSubtitleDownloadNode)

专门用于下载视频字幕。

**输入参数：**
- `url`（必需）：视频链接
- `output_dir`：输出目录
- `languages`：字幕语言列表
- `auto_generated`：是否包含自动生成的字幕
- `cookie_file`：cookie 文件路径

**输出参数：**
- `subtitle_files`：字幕文件路径列表
- `available_languages`：可用的字幕语言列表

### YouTube 搜索节点 (YouTubeSearchNode)

搜索 YouTube 视频。

**输入参数：**
- `query`（必需）：搜索关键词
- `max_results`：最大结果数
- `cookie_file`：cookie 文件路径

**输出参数：**
- `video_urls`：视频链接列表
- `titles`：视频标题列表
- `descriptions`：视频描述列表
- `durations`：视频时长列表

## 使用示例

### 下载单个视频
```python
from autotask_youtube import YouTubeDownloadNode

node = YouTubeDownloadNode()
result = await node.execute({
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "output_dir": "./downloads",
    "format": "best",
    "extract_audio": True,
    "audio_format": "mp3",
    "audio_quality": 5,
    "write_subs": True,
    "sub_langs": "en,zh-CN"
}, workflow_logger)

print(f"下载完成：{result['file_path']}")
print(f"标题：{result['title']}")
print(f"时长：{result['duration']} 秒")
if result['subtitle_files']:
    print(f"字幕文件：{result['subtitle_files']}")
```

### 下载播放列表
```python
from autotask_youtube import YouTubePlaylistDownloadNode

node = YouTubePlaylistDownloadNode()
result = await node.execute({
    "playlist_url": "https://www.youtube.com/playlist?list=PLxxxxxxxx",
    "output_dir": "./downloads",
    "format": "best",
    "write_subs": True,
    "sub_langs": "en,zh-CN"
}, workflow_logger)

for i, (path, title, duration, subs) in enumerate(zip(
    result['file_paths'],
    result['titles'],
    result['durations'],
    result['subtitle_files']
)):
    print(f"视频 {i+1}:")
    print(f"  路径：{path}")
    print(f"  标题：{title}")
    print(f"  时长：{duration} 秒")
    if subs:
        print(f"  字幕：{subs}")
```

## 注意事项

1. 确保有足够的磁盘空间存储下载的视频
2. 对于大型播放列表或频道，建议使用 `playlist_start` 和 `playlist_end` 分批下载
3. 如果下载速度较慢，可以尝试使用不同的视频格式
4. 对于受限制的视频，确保提供有效的 cookie 文件
5. 所有字幕都将以 VTT 格式保存

## 许可证

本插件基于 MIT 许可证开源。详见 LICENSE 文件。

AutoTask.dev User Id: buKkhpRSxA9LT4zZ6GDKH9

