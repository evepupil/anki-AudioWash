# -*- coding: utf-8 -*-
"""
牌组选择对话框模块
提供选择牌组的界面
"""

from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt
from anki.collection import Collection


class DeckSelectionDialog(QDialog):
    """牌组选择对话框"""

    def __init__(self, col: Collection, parent=None):
        """
        初始化牌组选择对话框

        Args:
            col: Anki Collection 对象
            parent: 父窗口
        """
        super().__init__(parent)
        self.col = col
        self.selected_deck_id = None  # None 表示"全部牌组"
        self._init_ui()

    def _init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("选择牌组")
        self.setMinimumSize(400, 500)

        # 主布局
        main_layout = QVBoxLayout()

        # 标题标签
        title_label = QLabel("请选择要播放的牌组：")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        # 提示标签
        hint_label = QLabel("提示：选择\"全部牌组\"将播放所有今天学习的卡片音频")
        hint_label.setStyleSheet("color: gray; font-size: 12px;")
        main_layout.addWidget(hint_label)

        # 牌组列表
        self.deck_list = QListWidget()
        self.deck_list.itemDoubleClicked.connect(self._on_deck_double_clicked)
        main_layout.addWidget(self.deck_list)

        # 加载牌组列表
        self._load_decks()

        # 按钮布局
        button_layout = QHBoxLayout()

        # 确定按钮
        self.ok_button = QPushButton("确定")
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)

        # 取消按钮
        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def _load_decks(self):
        """加载牌组列表"""
        # 添加"全部牌组"选项
        all_decks_item = QListWidgetItem("📚 全部牌组")
        all_decks_item.setData(Qt.ItemDataRole.UserRole, None)  # None 表示全部
        self.deck_list.addItem(all_decks_item)

        # 获取所有牌组
        deck_manager = self.col.decks
        all_decks = deck_manager.all_names_and_ids()

        # 按名称排序
        sorted_decks = sorted(all_decks, key=lambda x: x.name)

        # 添加每个牌组
        for deck in sorted_decks:
            # 计算缩进层级
            indent_level = deck.name.count("::")
            indent = "    " * indent_level

            # 创建列表项
            deck_name = deck.name.split("::")[-1]  # 只显示最后一级名称
            display_name = f"{indent}📖 {deck_name}"

            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, deck.id)
            item.setToolTip(deck.name)  # 显示完整路径作为提示
            self.deck_list.addItem(item)

        # 默认选中"全部牌组"
        self.deck_list.setCurrentRow(0)

    def _on_deck_double_clicked(self, item):
        """双击牌组时直接确认选择"""
        self.accept()

    def get_selected_deck(self) -> tuple[Optional[int], str]:
        """
        获取选中的牌组

        Returns:
            (deck_id, deck_name) 元组
            deck_id 为 None 表示"全部牌组"
        """
        current_item = self.deck_list.currentItem()
        if current_item:
            deck_id = current_item.data(Qt.ItemDataRole.UserRole)
            deck_name = current_item.text().strip().replace("📚 ", "").replace("📖 ", "")
            return deck_id, deck_name
        return None, "全部牌组"
