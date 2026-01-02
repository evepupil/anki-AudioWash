# -*- coding: utf-8 -*-
"""
牌组选择对话框模块
提供选择牌组的界面
"""

from typing import Optional, Tuple, List
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QListWidget, QListWidgetItem, QRadioButton, QButtonGroup,
    QCheckBox, QGroupBox
)
from PyQt6.QtCore import Qt
from anki.collection import Collection
from .card_query import StudyMode


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
        self.selected_deck_ids = []  # 选中的牌组 ID 列表，空列表表示"全部牌组"
        self.study_mode = StudyMode.COMBINED  # 默认结合模式
        self.include_unlearned = False  # 默认不包含未学习的新卡片
        self._init_ui()

    def _init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("选择牌组和学习模式")
        self.setMinimumSize(450, 600)

        # 主布局
        main_layout = QVBoxLayout()

        # 标题标签
        title_label = QLabel("请选择要播放的牌组（支持多选）：")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        # 牌组列表（启用多选）
        self.deck_list = QListWidget()
        self.deck_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        self.deck_list.itemDoubleClicked.connect(self._on_deck_double_clicked)
        main_layout.addWidget(self.deck_list)

        # 加载牌组列表
        self._load_decks()

        # 学习模式选择组
        mode_group = QGroupBox("学习模式")
        mode_layout = QVBoxLayout()

        # 创建单选按钮组
        self.mode_button_group = QButtonGroup()

        # 结合模式（默认）
        self.combined_radio = QRadioButton("结合模式：今天新学 + 今天复习")
        self.combined_radio.setChecked(True)
        self.combined_radio.setToolTip("播放今天新学的卡片和今天复习的卡片")
        self.mode_button_group.addButton(self.combined_radio, 0)
        mode_layout.addWidget(self.combined_radio)

        # 学习模式
        self.new_only_radio = QRadioButton("学习模式：仅今天新学")
        self.new_only_radio.setToolTip("只播放今天新学的卡片")
        self.mode_button_group.addButton(self.new_only_radio, 1)
        mode_layout.addWidget(self.new_only_radio)

        # 复习模式
        self.review_only_radio = QRadioButton("复习模式：仅今天复习")
        self.review_only_radio.setToolTip("只播放今天复习的卡片（之前学过的）")
        self.mode_button_group.addButton(self.review_only_radio, 2)
        mode_layout.addWidget(self.review_only_radio)

        # 包含未学习新卡片的复选框
        self.include_unlearned_checkbox = QCheckBox("包含未学习的新卡片")
        self.include_unlearned_checkbox.setToolTip("勾选后将包含还未学习过的新卡片（预习）\n取消勾选只播放已经学习过的卡片")
        self.include_unlearned_checkbox.setStyleSheet("margin-left: 20px; color: gray;")
        mode_layout.addWidget(self.include_unlearned_checkbox)

        # 连接单选按钮信号，更新复选框可用性
        self.combined_radio.toggled.connect(self._update_unlearned_checkbox)
        self.new_only_radio.toggled.connect(self._update_unlearned_checkbox)
        self.review_only_radio.toggled.connect(self._update_unlearned_checkbox)

        mode_group.setLayout(mode_layout)
        main_layout.addWidget(mode_group)

        # 提示标签
        hint_label = QLabel("提示：\n• 按住 Ctrl 点击可多选牌组\n• 不选择任何牌组 = 全部牌组\n• 学习模式 - 只听今天新学的单词\n• 复习模式 - 只听今天复习的单词\n• 结合模式 - 听今天新学+复习的单词\n• 勾选\"包含未学习\"可以预习还未学习的新单词")
        hint_label.setStyleSheet("color: gray; font-size: 11px; padding: 5px;")
        hint_label.setWordWrap(True)
        main_layout.addWidget(hint_label)

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

    def _on_deck_double_clicked(self, item):
        """双击牌组时直接确认选择"""
        self.accept()

    def _update_unlearned_checkbox(self):
        """更新\"包含未学习的新卡片\"复选框的可用性"""
        # 只有在\"学习模式\"时禁用此复选框（因为学习模式本身就是新学的）
        is_new_only = self.new_only_radio.isChecked()
        self.include_unlearned_checkbox.setEnabled(not is_new_only)

        if is_new_only:
            self.include_unlearned_checkbox.setChecked(False)

    def get_selected_decks(self) -> Tuple[List[int], str]:
        """
        获取选中的牌组列表

        Returns:
            (deck_ids, deck_names) 元组
            deck_ids 为空列表表示"全部牌组"
        """
        selected_items = self.deck_list.selectedItems()

        if not selected_items:
            # 没有选择任何牌组，返回空列表表示全部牌组
            return [], "全部牌组"

        deck_ids = []
        deck_names = []

        for item in selected_items:
            deck_id = item.data(Qt.ItemDataRole.UserRole)
            deck_name = item.text().strip().replace("📖 ", "")
            deck_ids.append(deck_id)
            deck_names.append(deck_name)

        # 生成显示名称
        if len(deck_names) == 1:
            display_name = deck_names[0]
        elif len(deck_names) <= 3:
            display_name = "、".join(deck_names)
        else:
            display_name = f"{deck_names[0]}、{deck_names[1]} 等 {len(deck_names)} 个牌组"

        return deck_ids, display_name

    def get_study_mode(self) -> StudyMode:
        """
        获取选中的学习模式

        Returns:
            StudyMode 枚举值
        """
        if self.new_only_radio.isChecked():
            return StudyMode.NEW_ONLY
        elif self.review_only_radio.isChecked():
            return StudyMode.REVIEW_ONLY
        else:
            return StudyMode.COMBINED

    def get_include_unlearned(self) -> bool:
        """
        获取是否包含未学习的新卡片

        Returns:
            是否包含未学习的新卡片
        """
        return self.include_unlearned_checkbox.isChecked()
