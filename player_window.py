# -*- coding: utf-8 -*-
"""
播放器窗口模块
提供音频播放的图形界面
"""

import random
from typing import List
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QSlider, QListWidget, QCheckBox, QSpinBox, QSystemTrayIcon, QMenu
)
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from aqt.utils import showInfo


class AudioPlayerWindow(QDialog):
    """音频播放器窗口 - 提供播放控制界面"""

    def __init__(self, audio_files: List[str], parent=None):
        """
        初始化播放器窗口

        Args:
            audio_files: 音频文件路径列表
            parent: 父窗口
        """
        super().__init__(parent)

        self.audio_files = audio_files.copy()  # 原始播放列表
        self.shuffled_playlist = []  # 乱序后的播放列表
        self.current_index = 0  # 当前播放索引
        self.is_playing_next = False  # 防止重复触发播放下一曲
        self.auto_loop_enabled = True  # 自动循环开关（默认开启）
        self.loop_interval = 0  # 循环间隔（秒），默认0秒无间隔

        # 初始化媒体播放器
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)

        # 连接播放器信号
        self.player.mediaStatusChanged.connect(self._on_media_status_changed)
        self.player.playbackStateChanged.connect(self._on_playback_state_changed)
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)

        # 初始化界面
        self._init_ui()

        # 初始化系统托盘
        self._init_tray()

        # 乱序播放列表并开始播放
        self._shuffle_playlist()
        if self.shuffled_playlist:
            self._play_current()

    def _init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("Audio Wash Player")
        self.setMinimumSize(400, 500)

        # 设置窗口置顶
        self.setWindowFlags(
            self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint
        )

        # 主布局
        main_layout = QVBoxLayout()

        # 状态信息标签
        self.status_label = QLabel("准备播放...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

        # 当前播放文件标签
        self.current_file_label = QLabel("")
        self.current_file_label.setWordWrap(True)
        self.current_file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.current_file_label)

        # 进度条
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setEnabled(False)
        self.progress_slider.sliderMoved.connect(self._on_slider_moved)
        main_layout.addWidget(self.progress_slider)

        # 时间标签
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.time_label)

        # 控制按钮布局
        control_layout = QHBoxLayout()

        # 上一曲按钮
        self.prev_button = QPushButton("⏮ 上一曲")
        self.prev_button.clicked.connect(self._play_previous)
        control_layout.addWidget(self.prev_button)

        # 播放/暂停按钮
        self.play_pause_button = QPushButton("⏸ 暂停")
        self.play_pause_button.clicked.connect(self._toggle_play_pause)
        control_layout.addWidget(self.play_pause_button)

        # 下一曲按钮
        self.next_button = QPushButton("⏭ 下一曲")
        self.next_button.clicked.connect(self._play_next)
        control_layout.addWidget(self.next_button)

        main_layout.addLayout(control_layout)

        # 重新乱序按钮
        self.shuffle_button = QPushButton("🔀 重新乱序")
        self.shuffle_button.clicked.connect(self._reshuffle)
        main_layout.addWidget(self.shuffle_button)

        # 自动循环设置区域
        loop_settings_layout = QHBoxLayout()

        # 自动循环复选框
        self.auto_loop_checkbox = QCheckBox("自动循环")
        self.auto_loop_checkbox.setChecked(True)  # 默认开启
        self.auto_loop_checkbox.stateChanged.connect(self._on_auto_loop_toggled)
        loop_settings_layout.addWidget(self.auto_loop_checkbox)

        # 循环间隔标签
        loop_interval_label = QLabel("间隔:")
        loop_settings_layout.addWidget(loop_interval_label)

        # 循环间隔输入框（秒）
        self.loop_interval_spinbox = QSpinBox()
        self.loop_interval_spinbox.setMinimum(0)
        self.loop_interval_spinbox.setMaximum(60)
        self.loop_interval_spinbox.setValue(0)
        self.loop_interval_spinbox.setSuffix(" 秒")
        self.loop_interval_spinbox.setToolTip("每首歌播放完毕后的等待时间（0-60秒）")
        self.loop_interval_spinbox.valueChanged.connect(self._on_interval_changed)
        loop_settings_layout.addWidget(self.loop_interval_spinbox)

        loop_settings_layout.addStretch()  # 添加弹性空间
        main_layout.addLayout(loop_settings_layout)

        # 播放列表标签
        playlist_label = QLabel(f"播放列表 (共 {len(self.audio_files)} 首)")
        main_layout.addWidget(playlist_label)

        # 播放列表显示
        self.playlist_widget = QListWidget()
        main_layout.addWidget(self.playlist_widget)

        # 关闭按钮改为最小化到托盘按钮
        self.minimize_button = QPushButton("最小化到托盘")
        self.minimize_button.clicked.connect(self._minimize_to_tray)
        main_layout.addWidget(self.minimize_button)

        # 退出按钮
        self.quit_button = QPushButton("退出播放器")
        self.quit_button.clicked.connect(self._quit_player)
        main_layout.addWidget(self.quit_button)

        self.setLayout(main_layout)

    def _init_tray(self):
        """初始化系统托盘"""
        # 创建系统托盘图标
        self.tray_icon = QSystemTrayIcon(self)

        # 尝试使用 Anki 的图标，如果失败则使用默认图标
        try:
            from aqt import mw
            if mw and mw.windowIcon():
                self.tray_icon.setIcon(mw.windowIcon())
            else:
                # 使用默认应用图标
                self.tray_icon.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_MediaPlay))
        except:
            # 使用默认应用图标
            self.tray_icon.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_MediaPlay))

        # 创建托盘菜单
        tray_menu = QMenu()

        # 显示窗口动作
        show_action = QAction("显示播放器", self)
        show_action.triggered.connect(self._show_window)
        tray_menu.addAction(show_action)

        # 播放/暂停动作
        self.tray_play_pause_action = QAction("暂停", self)
        self.tray_play_pause_action.triggered.connect(self._toggle_play_pause)
        tray_menu.addAction(self.tray_play_pause_action)

        # 下一曲动作
        next_action = QAction("下一曲", self)
        next_action.triggered.connect(self._play_next)
        tray_menu.addAction(next_action)

        tray_menu.addSeparator()

        # 退出动作
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self._quit_player)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)

        # 双击托盘图标显示窗口
        self.tray_icon.activated.connect(self._on_tray_activated)

        # 显示托盘图标
        self.tray_icon.show()

    def _on_tray_activated(self, reason):
        """托盘图标被激活时的回调"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._show_window()

    def _minimize_to_tray(self):
        """最小化到系统托盘"""
        self.hide()
        self.tray_icon.showMessage(
            "Audio Wash Player",
            "播放器已最小化到托盘，双击图标可恢复窗口",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )

    def _show_window(self):
        """显示窗口"""
        self.show()
        self.activateWindow()  # 激活窗口，使其获得焦点

    def _quit_player(self):
        """退出播放器"""
        self.close()  # 关闭窗口

    def _shuffle_playlist(self):
        """乱序播放列表"""
        self.shuffled_playlist = self.audio_files.copy()
        random.shuffle(self.shuffled_playlist)
        self.current_index = 0
        self._update_playlist_display()

    def _reshuffle(self):
        """重新乱序并从头开始播放"""
        self._shuffle_playlist()
        if self.shuffled_playlist:
            self._play_current()

    def _on_auto_loop_toggled(self, state):
        """自动循环开关切换"""
        self.auto_loop_enabled = (state == Qt.CheckState.Checked.value)
        print(f"[DEBUG] Auto loop {'enabled' if self.auto_loop_enabled else 'disabled'}")

    def _on_interval_changed(self, value):
        """循环间隔改变"""
        self.loop_interval = value
        print(f"[DEBUG] Loop interval changed to {value} seconds")

    def _update_playlist_display(self):
        """更新播放列表显示"""
        self.playlist_widget.clear()
        for i, file_path in enumerate(self.shuffled_playlist):
            # 只显示文件名
            import os
            filename = os.path.basename(file_path)
            prefix = "▶ " if i == self.current_index else "  "
            self.playlist_widget.addItem(f"{prefix}{i+1}. {filename}")

        # 滚动到当前播放项
        self.playlist_widget.setCurrentRow(self.current_index)

    def _play_current(self):
        """播放当前索引的音频"""
        if not self.shuffled_playlist:
            self.status_label.setText("播放列表为空")
            return

        # 获取当前文件路径
        current_file = self.shuffled_playlist[self.current_index]

        # 设置媒体源并播放
        self.player.setSource(QUrl.fromLocalFile(current_file))
        self.player.play()

        # 更新界面
        import os
        filename = os.path.basename(current_file)
        self.current_file_label.setText(f"正在播放: {filename}")
        self.status_label.setText(f"播放中 ({self.current_index + 1}/{len(self.shuffled_playlist)})")
        self.play_pause_button.setText("⏸ 暂停")
        self.tray_play_pause_action.setText("暂停")  # 同步更新托盘菜单

        # 更新播放列表显示
        self._update_playlist_display()

    def _play_next(self):
        """播放下一曲"""
        print(f"[DEBUG] _play_next called, current_index={self.current_index}, playlist_length={len(self.shuffled_playlist)}")

        if not self.shuffled_playlist:
            print("[DEBUG] Playlist is empty!")
            return

        self.current_index += 1
        print(f"[DEBUG] Incremented index to {self.current_index}")

        # 如果到达列表末尾，重新乱序并从头开始（无限循环）
        if self.current_index >= len(self.shuffled_playlist):
            print("[DEBUG] Reached end of playlist, reshuffling...")
            self._shuffle_playlist()

        print(f"[DEBUG] About to play current (index={self.current_index})")
        self._play_current()

    def _play_previous(self):
        """播放上一曲"""
        if not self.shuffled_playlist:
            return

        self.current_index -= 1

        # 如果到达列表开头，跳到末尾
        if self.current_index < 0:
            self.current_index = len(self.shuffled_playlist) - 1

        self._play_current()

    def _toggle_play_pause(self):
        """切换播放/暂停状态"""
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.play_pause_button.setText("▶ 播放")
            self.tray_play_pause_action.setText("播放")  # 同步更新托盘菜单
            self.status_label.setText("已暂停")
        else:
            self.player.play()
            self.play_pause_button.setText("⏸ 暂停")
            self.tray_play_pause_action.setText("暂停")  # 同步更新托盘菜单
            self.status_label.setText(f"播放中 ({self.current_index + 1}/{len(self.shuffled_playlist)})")

    def _on_media_status_changed(self, status):
        """媒体状态改变时的回调"""
        # 调试信息
        status_names = {
            QMediaPlayer.MediaStatus.NoMedia: "NoMedia",
            QMediaPlayer.MediaStatus.LoadingMedia: "LoadingMedia",
            QMediaPlayer.MediaStatus.LoadedMedia: "LoadedMedia",
            QMediaPlayer.MediaStatus.StalledMedia: "StalledMedia",
            QMediaPlayer.MediaStatus.BufferingMedia: "BufferingMedia",
            QMediaPlayer.MediaStatus.BufferedMedia: "BufferedMedia",
            QMediaPlayer.MediaStatus.EndOfMedia: "EndOfMedia",
            QMediaPlayer.MediaStatus.InvalidMedia: "InvalidMedia"
        }
        print(f"[DEBUG] Media status changed: {status_names.get(status, 'Unknown')}")

        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            # 防止重复触发
            if self.is_playing_next:
                print("[DEBUG] Already playing next, skipping...")
                return

            print("[DEBUG] End of media detected, playing next...")
            self.is_playing_next = True
            # 使用 QTimer 延迟执行，避免在信号处理中直接操作播放器
            QTimer.singleShot(100, self._delayed_play_next)

    def _on_playback_state_changed(self, state):
        """播放状态改变时的回调 - 用于更可靠地检测播放结束"""
        state_names = {
            QMediaPlayer.PlaybackState.StoppedState: "Stopped",
            QMediaPlayer.PlaybackState.PlayingState: "Playing",
            QMediaPlayer.PlaybackState.PausedState: "Paused"
        }
        print(f"[DEBUG] Playback state changed: {state_names.get(state, 'Unknown')}")

        # 只在真正停止时才处理（不是暂停）
        if state == QMediaPlayer.PlaybackState.StoppedState:
            # 检查是否是因为播放完毕而停止
            if self.player.mediaStatus() == QMediaPlayer.MediaStatus.EndOfMedia:
                # 防止重复触发
                if self.is_playing_next:
                    print("[DEBUG] Already playing next (from state change), skipping...")
                    return

                print("[DEBUG] Stopped at end of media, playing next...")
                self.is_playing_next = True
                # 使用 QTimer 延迟执行
                QTimer.singleShot(100, self._delayed_play_next)

    def _delayed_play_next(self):
        """延迟播放下一曲 - 避免在信号处理中直接操作"""
        print("[DEBUG] _delayed_play_next called")
        self.is_playing_next = False

        # 检查是否启用自动循环
        if not self.auto_loop_enabled:
            print("[DEBUG] Auto loop is disabled, stopping playback")
            self.status_label.setText("播放完毕（自动循环已关闭）")
            return

        # 如果设置了循环间隔，先等待
        if self.loop_interval > 0:
            print(f"[DEBUG] Waiting {self.loop_interval} seconds before next track...")
            self.status_label.setText(f"等待 {self.loop_interval} 秒后播放下一曲...")
            # 使用 QTimer 延迟指定的秒数后再播放下一曲
            QTimer.singleShot(self.loop_interval * 1000, self._play_next)
        else:
            # 无间隔，直接播放下一曲
            self._play_next()

    def _on_position_changed(self, position):
        """播放位置改变时的回调"""
        self.progress_slider.setValue(position)
        self._update_time_label()

    def _on_duration_changed(self, duration):
        """音频时长改变时的回调"""
        self.progress_slider.setMaximum(duration)
        self.progress_slider.setEnabled(duration > 0)
        self._update_time_label()

    def _on_slider_moved(self, position):
        """进度条拖动时的回调"""
        self.player.setPosition(position)

    def _update_time_label(self):
        """更新时间显示"""
        position = self.player.position()
        duration = self.player.duration()

        position_str = self._format_time(position)
        duration_str = self._format_time(duration)

        self.time_label.setText(f"{position_str} / {duration_str}")

    def _format_time(self, ms):
        """格式化时间（毫秒转为 MM:SS）"""
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def closeEvent(self, event):
        """窗口关闭时的处理"""
        # 停止播放
        self.player.stop()
        # 隐藏托盘图标
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
        event.accept()
