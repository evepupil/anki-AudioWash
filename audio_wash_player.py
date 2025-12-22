# -*- coding: utf-8 -*-
"""
Audio Wash Player 主模块
整合所有功能并提供菜单入口
"""

from aqt import mw
from aqt.qt import QAction
from aqt.utils import showInfo, showWarning

from .card_query import CardQuery
from .audio_extractor import AudioExtractor
from .player_window import AudioPlayerWindow


# 全局变量：保存播放器窗口实例
player_window = None


def start_audio_wash():
    """
    启动 Audio Wash Player
    这是菜单项的回调函数
    """
    global player_window

    # 检查是否有打开的集合
    if not mw.col:
        showWarning("请先打开一个 Anki 集合（牌组）")
        return

    try:
        # 1. 查询今天的卡片
        card_query = CardQuery(mw.col, max_cards=200)
        card_ids = card_query.get_today_cards()

        if not card_ids:
            showInfo("今天没有学习或复习任何卡片，无法启动播放器。")
            return

        # 获取卡片统计信息
        card_stats = card_query.get_card_count()

        # 2. 提取音频文件
        audio_extractor = AudioExtractor(mw.col)
        audio_files = audio_extractor.extract_audio_files(card_ids)

        if not audio_files:
            showInfo(
                f"找到 {card_stats['total']} 张卡片，但没有找到任何音频文件。\n"
                f"新学: {card_stats['new']} 张\n"
                f"复习: {card_stats['reviewed']} 张\n\n"
                f"请确保卡片中包含 [sound:...] 标签。"
            )
            return

        # 3. 创建并显示播放器窗口（使用 None 作为 parent，创建独立窗口）
        player_window = AudioPlayerWindow(audio_files, parent=None)
        player_window.show()

        # 不再显示启动信息弹框，直接启动播放器
        # showInfo(
        #     f"Audio Wash Player 已启动！\n\n"
        #     f"卡片统计：\n"
        #     f"- 新学: {card_stats['new']} 张\n"
        #     f"- 复习: {card_stats['reviewed']} 张\n"
        #     f"- 总计: {card_stats['total']} 张\n\n"
        #     f"找到 {len(audio_files)} 个音频文件\n"
        #     f"播放模式：乱序循环"
        # )

    except Exception as e:
        showWarning(f"启动 Audio Wash Player 时出错：\n{str(e)}")


def add_menu_item():
    """
    在 Anki 菜单栏中添加 "Start Audio Wash" 菜单项
    """
    # 创建菜单动作
    action = QAction("Start Audio Wash", mw)
    action.triggered.connect(start_audio_wash)

    # 添加到 Tools 菜单
    mw.form.menuTools.addAction(action)


def init_addon():
    """
    初始化插件
    在 Anki 启动时调用
    """
    # 添加菜单项
    add_menu_item()
