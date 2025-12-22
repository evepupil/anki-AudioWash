# -*- coding: utf-8 -*-
"""
音频提取模块
负责从卡片字段中提取音频文件路径
"""

import re
import os
from typing import List
from anki.collection import Collection
from anki.cards import Card


class AudioExtractor:
    """音频提取器 - 从卡片中提取音频文件"""

    def __init__(self, col: Collection):
        """
        初始化音频提取器

        Args:
            col: Anki Collection 对象
        """
        self.col = col
        # 正则表达式匹配 [sound:filename.mp3] 格式
        self.sound_pattern = re.compile(r'\[sound:(.*?)\]')

    def extract_audio_files(self, card_ids: List[int]) -> List[str]:
        """
        从卡片列表中提取所有音频文件路径

        Args:
            card_ids: 卡片 ID 列表

        Returns:
            音频文件的完整路径列表
        """
        audio_files = []

        for card_id in card_ids:
            # 获取卡片对象
            card = self.col.get_card(card_id)
            if not card:
                continue

            # 从卡片中提取音频
            card_audio_files = self._extract_from_card(card)
            audio_files.extend(card_audio_files)

        # 去重并过滤不存在的文件
        audio_files = list(set(audio_files))
        audio_files = [f for f in audio_files if os.path.exists(f)]

        return audio_files

    def _extract_from_card(self, card: Card) -> List[str]:
        """
        从单个卡片中提取音频文件

        Args:
            card: Anki 卡片对象

        Returns:
            音频文件路径列表
        """
        audio_files = []

        # 获取笔记对象
        note = card.note()
        if not note:
            return audio_files

        # 遍历笔记的所有字段
        for field_name, field_value in note.items():
            # 在字段内容中查找 [sound:...] 标签
            sound_matches = self.sound_pattern.findall(field_value)

            for sound_file in sound_matches:
                # 构建完整的文件路径
                full_path = self._get_full_audio_path(sound_file)
                if full_path:
                    audio_files.append(full_path)

        return audio_files

    def _get_full_audio_path(self, filename: str) -> str:
        """
        获取音频文件的完整路径

        Args:
            filename: 音频文件名（从 [sound:...] 中提取）

        Returns:
            完整的文件路径，如果文件不存在则返回空字符串
        """
        # 获取 Anki 媒体文件夹路径
        media_dir = self.col.media.dir()

        # 构建完整路径
        full_path = os.path.join(media_dir, filename)

        # 检查文件是否存在
        if os.path.exists(full_path):
            return full_path
        else:
            return ""

    def get_audio_count(self, card_ids: List[int]) -> int:
        """
        获取卡片中的音频文件数量

        Args:
            card_ids: 卡片 ID 列表

        Returns:
            音频文件数量
        """
        audio_files = self.extract_audio_files(card_ids)
        return len(audio_files)
