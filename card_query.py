# -*- coding: utf-8 -*-
"""
卡片查询模块
负责查询今天新学的、复习错的、复习对的卡片
"""

from datetime import datetime, timedelta
from typing import List, Optional
from anki.collection import Collection
from enum import Enum


class StudyMode(Enum):
    """学习模式枚举"""
    NEW_ONLY = "new_only"  # 仅新学
    REVIEW_ONLY = "review_only"  # 仅复习
    COMBINED = "combined"  # 结合模式（新学 + 复习）


class CardQuery:
    """卡片查询类 - 负责从 Anki 数据库中查询特定卡片"""

    def __init__(self, col: Collection, max_cards: int = 200, deck_ids: Optional[List[int]] = None,
                 study_mode: StudyMode = StudyMode.COMBINED, include_unlearned: bool = False):
        """
        初始化卡片查询器

        Args:
            col: Anki Collection 对象
            max_cards: 最大卡片数量限制
            deck_ids: 指定牌组 ID 列表，None 或空列表表示所有牌组
            study_mode: 学习模式（新学/复习/结合）
            include_unlearned: 是否包含未学习的新卡片（仅在复习模式或结合模式下有效）
        """
        self.col = col
        self.max_cards = max_cards
        self.deck_ids = deck_ids if deck_ids else []
        self.study_mode = study_mode
        self.include_unlearned = include_unlearned

    def get_today_cards(self) -> List[int]:
        """
        获取今天的所有相关卡片（根据学习模式）

        Returns:
            卡片 ID 列表
        """
        card_ids = []

        # 根据学习模式决定查询哪些卡片
        if self.study_mode == StudyMode.NEW_ONLY:
            # 仅新学模式：只查询今天新学的卡片
            new_cards = self._get_new_cards_today()
            card_ids.extend(new_cards)

        elif self.study_mode == StudyMode.REVIEW_ONLY:
            # 仅复习模式：只查询今天复习的卡片
            reviewed_cards = self._get_reviewed_cards_today()
            card_ids.extend(reviewed_cards)

            # 如果启用了"包含未学习的新卡片"，添加今天的新卡片
            if self.include_unlearned:
                unlearned_cards = self._get_unlearned_new_cards()
                card_ids.extend(unlearned_cards)

        else:  # StudyMode.COMBINED
            # 结合模式：新学 + 复习
            new_cards = self._get_new_cards_today()
            card_ids.extend(new_cards)

            reviewed_cards = self._get_reviewed_cards_today()
            card_ids.extend(reviewed_cards)

            # 如果启用了"包含未学习的新卡片"，添加未学习的新卡片
            if self.include_unlearned:
                unlearned_cards = self._get_unlearned_new_cards()
                card_ids.extend(unlearned_cards)

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
        if self.deck_ids:
            # 构建多个牌组的 OR 查询
            deck_queries = []
            for deck_id in self.deck_ids:
                deck_name = self.col.decks.name(deck_id)
                deck_queries.append(f'deck:"{deck_name}"')

            # 使用括号和 OR 连接多个牌组
            if len(deck_queries) == 1:
                query = f'{deck_queries[0]} {query}'
            else:
                decks_query = " OR ".join(deck_queries)
                query = f'({decks_query}) {query}'

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
        if self.deck_ids:
            # 构建多个牌组的 OR 查询
            deck_queries = []
            for deck_id in self.deck_ids:
                deck_name = self.col.decks.name(deck_id)
                deck_queries.append(f'deck:"{deck_name}"')

            # 使用括号和 OR 连接多个牌组
            if len(deck_queries) == 1:
                query = f'{deck_queries[0]} {query}'
            else:
                decks_query = " OR ".join(deck_queries)
                query = f'({decks_query}) {query}'

        card_ids = self.col.find_cards(query)

        return list(card_ids)

    def _get_unlearned_new_cards(self) -> List[int]:
        """
        获取未学习的新卡片（is:new 且未被学习过）

        Returns:
            未学习的新卡片 ID 列表
        """
        # 查询新卡片（尚未学习的卡片）
        # is:new 表示新卡片，-rated:1 表示今天未复习过
        query = "is:new"

        # 如果指定了牌组，添加牌组过滤
        if self.deck_ids:
            # 构建多个牌组的 OR 查询
            deck_queries = []
            for deck_id in self.deck_ids:
                deck_name = self.col.decks.name(deck_id)
                deck_queries.append(f'deck:"{deck_name}"')

            # 使用括号和 OR 连接多个牌组
            if len(deck_queries) == 1:
                query = f'{deck_queries[0]} {query}'
            else:
                decks_query = " OR ".join(deck_queries)
                query = f'({decks_query}) {query}'

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
