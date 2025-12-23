# -*- coding: utf-8 -*-
"""
卡片查询模块
负责查询今天新学的、复习错的、复习对的卡片
"""

from datetime import datetime, timedelta
from typing import List, Optional
from anki.collection import Collection


class CardQuery:
    """卡片查询类 - 负责从 Anki 数据库中查询特定卡片"""

    def __init__(self, col: Collection, max_cards: int = 200, deck_id: Optional[int] = None):
        """
        初始化卡片查询器

        Args:
            col: Anki Collection 对象
            max_cards: 最大卡片数量限制
            deck_id: 指定牌组 ID，None 表示所有牌组
        """
        self.col = col
        self.max_cards = max_cards
        self.deck_id = deck_id

    def get_today_cards(self) -> List[int]:
        """
        获取今天的所有相关卡片（新学 + 复习错 + 复习对）

        Returns:
            卡片 ID 列表
        """
        card_ids = []

        # 1. 获取今天新增的卡片（今天新学的）
        new_cards = self._get_new_cards_today()
        card_ids.extend(new_cards)

        # 2. 获取今天复习的卡片（包括复习错的和复习对的）
        reviewed_cards = self._get_reviewed_cards_today()
        card_ids.extend(reviewed_cards)

        # 去重并限制数量
        card_ids = list(set(card_ids))

        # 如果超过最大数量，只取最近的卡片
        if len(card_ids) > self.max_cards:
            card_ids = card_ids[-self.max_cards:]

        return card_ids

    def _get_new_cards_today(self) -> List[int]:
        """
        获取今天新增的卡片

        Returns:
            新卡片 ID 列表
        """
        # 获取今天的开始时间戳（毫秒）
        today_start = self._get_today_start_timestamp()

        # 查询今天添加的卡片
        # added:1 表示今天添加的卡片
        query = "added:1"

        # 如果指定了牌组，添加牌组过滤
        if self.deck_id is not None:
            deck_name = self.col.decks.name(self.deck_id)
            query = f'deck:"{deck_name}" {query}'

        card_ids = self.col.find_cards(query)

        return list(card_ids)

    def _get_reviewed_cards_today(self) -> List[int]:
        """
        获取今天复习过的卡片（包括答对和答错的）

        Returns:
            复习过的卡片 ID 列表
        """
        # 查询今天复习过的卡片
        # rated:1 表示今天复习过的卡片
        query = "rated:1"

        # 如果指定了牌组，添加牌组过滤
        if self.deck_id is not None:
            deck_name = self.col.decks.name(self.deck_id)
            query = f'deck:"{deck_name}" {query}'

        card_ids = self.col.find_cards(query)

        return list(card_ids)

    def _get_today_start_timestamp(self) -> int:
        """
        获取今天开始的时间戳（毫秒）
        考虑 Anki 的一天从凌晨 4 点开始

        Returns:
            时间戳（毫秒）
        """
        now = datetime.now()

        # Anki 的一天从凌晨 4 点开始
        if now.hour < 4:
            # 如果当前时间在凌晨 4 点之前，今天的开始时间是昨天的 4 点
            today_start = now.replace(hour=4, minute=0, second=0, microsecond=0) - timedelta(days=1)
        else:
            # 否则今天的开始时间是今天的 4 点
            today_start = now.replace(hour=4, minute=0, second=0, microsecond=0)

        # 转换为毫秒时间戳
        timestamp_ms = int(today_start.timestamp() * 1000)

        return timestamp_ms

    def get_card_count(self) -> dict:
        """
        获取各类卡片的数量统计

        Returns:
            包含各类卡片数量的字典
        """
        new_cards = self._get_new_cards_today()
        reviewed_cards = self._get_reviewed_cards_today()

        return {
            'new': len(new_cards),
            'reviewed': len(reviewed_cards),
            'total': len(set(new_cards + reviewed_cards))
        }
