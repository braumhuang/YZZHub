# -*- coding: utf-8 -*-
"""生成结果对话框：标题 + 内容两个复制框。

- 「标题」只读单行框 + 行内「复制」按钮（与输入框同高）；
- 「内容」只读多行等宽字体框 + 「复制」按钮；
- 复制成功后按钮短暂显示「已复制」再复原；
- 尺寸与边距统一走 yzzhub.theme（与主界面一致）。
"""

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtWidgets import (
    QApplication, QDialog, QGroupBox, QHBoxLayout, QLineEdit,
    QPlainTextEdit, QPushButton, QVBoxLayout,
)

from yzzhub import theme

COPY_REVERT_MS = 1200   # 「已复制」提示的停留毫秒数


def _make_copy_button():
    """创建复制按钮及配套的复制回调（成功后按钮短暂显示「已复制」）。"""
    button = QPushButton("复制")
    theme.size_inline_button(button, theme.COPY_BUTTON_WIDTH)

    def copy_to_clipboard(value, source=button):
        QApplication.clipboard().setText(value)
        source.setText("已复制")
        QTimer.singleShot(
            COPY_REVERT_MS, lambda: source.setText("复制"))

    return button, copy_to_clipboard


class ResultDialog(QDialog):
    """展示并复制生成结果：标题（单行）+ 内容（多行等宽）。"""

    def __init__(self, parent, title_text, content_text):
        super().__init__(parent)
        self.setWindowTitle("生成结果")
        self.setModal(True)
        self.resize(660, 520)
        self.setMinimumSize(560, 420)

        # ---------------- 标题复制框 ----------------
        title_box = QGroupBox("标题")
        title_layout = QHBoxLayout(title_box)
        title_layout.setContentsMargins(*theme.FORM_MARGINS)
        title_layout.setSpacing(10)
        self.title_edit = theme.size_input(QLineEdit(title_text))
        self.title_edit.setReadOnly(True)
        title_button, title_copy = _make_copy_button()
        title_button.clicked.connect(
            lambda: title_copy(self.title_edit.text()))
        title_layout.addWidget(self.title_edit, 1)
        title_layout.addWidget(title_button)

        # ---------------- 内容复制框（等宽字体） ----------------
        content_box = QGroupBox("内容")
        content_layout = QVBoxLayout(content_box)
        content_layout.setContentsMargins(*theme.FORM_MARGINS)
        content_layout.setSpacing(10)
        self.content_edit = QPlainTextEdit(content_text)
        self.content_edit.setReadOnly(True)
        fixed_font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        fixed_font.setStyleHint(fixed_font.StyleHint.Monospace)
        self.content_edit.setFont(fixed_font)
        content_button, content_copy = _make_copy_button()
        content_button.clicked.connect(
            lambda: content_copy(self.content_edit.toPlainText()))
        content_layout.addWidget(self.content_edit, 1)
        content_layout.addWidget(content_button, 0, Qt.AlignRight)

        # ---------------- 关闭按钮 ----------------
        close_button = QPushButton("关闭")
        theme.size_normal_button(close_button, theme.COPY_BUTTON_WIDTH)
        close_button.clicked.connect(self.accept)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        button_row.addWidget(close_button)

        # ---------------- 对话框组装 ----------------
        outer = QVBoxLayout(self)
        outer.setContentsMargins(*theme.PAGE_MARGINS)
        outer.setSpacing(theme.SECTION_SPACING)
        outer.addWidget(title_box)
        outer.addWidget(content_box, 1)
        outer.addLayout(button_row)
