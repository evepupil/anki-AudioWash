# Audio Wash Player - Anki 插件

## 功能简介

Audio Wash Player 是一个 Anki 插件，可以自动提取今天学习和复习的卡片中的音频，并在后台循环播放。

### 核心功能

- ✅ **智能卡片筛选**：自动抓取今天新学的、复习错的、复习对的卡片
- ✅ **音频提取**：自动解析卡片中的 `[sound:...]` 标签
- ✅ **乱序播放**：每次播放都会随机打乱顺序
- ✅ **无限循环**：播放完毕后自动重新乱序并继续播放
- ✅ **独立窗口**：提供独立的播放器窗口，可置顶显示
- ✅ **播放控制**：支持播放/暂停、上一曲、下一曲、进度条拖动

## 安装方法

1. 将整个 `anki-AudioWash` 文件夹复制到 Anki 插件目录：
   - Windows: `%APPDATA%\Anki2\addons21\`
   - Mac: `~/Library/Application Support/Anki2/addons21/`
   - Linux: `~/.local/share/Anki2/addons21/`

2. 重启 Anki

## 使用方法

1. 在 Anki 主界面，点击菜单栏 **Tools > Start Audio Wash**
2. 插件会自动：
   - 查询今天学习和复习的卡片
   - 提取这些卡片中的音频文件
   - 打开播放器窗口并开始播放

3. 播放器窗口功能：
   - **⏮ 上一曲**：播放上一首音频
   - **⏸ 暂停 / ▶ 播放**：暂停或继续播放
   - **⏭ 下一曲**：播放下一首音频
   - **🔀 重新乱序**：重新打乱播放列表并从头开始
   - **进度条**：显示当前播放进度，可拖动跳转
   - **播放列表**：显示所有音频文件

## 项目结构

```
anki-AudioWash/
├── __init__.py              # 插件入口
├── manifest.json            # 插件配置文件
├── audio_wash_player.py     # 主模块（菜单入口和整合）
├── card_query.py            # 卡片查询模块
├── audio_extractor.py       # 音频提取模块
└── player_window.py         # 播放器窗口组件
```

### 模块说明

- **card_query.py**：负责从 Anki 数据库查询今天的卡片
  - `CardQuery` 类：查询今天新学、复习的卡片

- **audio_extractor.py**：负责从卡片中提取音频文件
  - `AudioExtractor` 类：解析 `[sound:...]` 标签并获取音频文件路径

- **player_window.py**：播放器窗口界面
  - `AudioPlayerWindow` 类：提供图形界面和播放控制

- **audio_wash_player.py**：主控制模块
  - 整合所有功能
  - 提供菜单入口

## 配置选项

在 `card_query.py` 中可以修改最大卡片数量限制：

```python
card_query = CardQuery(mw.col, max_cards=200)  # 默认 200 张
```

## 注意事项

1. 确保卡片中包含 `[sound:...]` 标签，否则无法提取音频
2. 音频文件必须存在于 Anki 的媒体文件夹中
3. 播放器窗口会置顶显示，方便随时控制
4. 关闭播放器窗口会停止播放

## 技术栈

- Python 3.9+
- PyQt6（Anki 界面框架）
- Anki API

## 版本信息

- 版本：1.0.0
- 作者：Evepupil
- 最低 Anki 版本：2.1.45

## 许可证

MIT License
