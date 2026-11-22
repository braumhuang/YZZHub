# -*- coding: utf-8 -*-
"""短剧页：帖子信息表单 + 右下角「清除 / 生成」导出 markdown。

必填字段以红色 * 标识：帖子标题（≥1 字符）、下载链接（多行文本）；
帖子图片、短剧简介（单行）留空时省略对应导出内容。

页面组装与字幕页同构（外观统一由 yzzhub.theme 定义）：
    输入控件 -> 表单卡片 -> 滚动区 -> 底部动作条（清除 / 生成）。

导出内容：图片行（自动附加 ?w=560 宽度参数）+ 短剧简介引用行
（单行「> 」前缀，位于图片下方、下载链接上方）+ 下载链接代码块；
链接文本本身含 ``` 时自动加长围栏（见 markdown.py）。
"""

import re

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QGroupBox, QLineEdit, QMessageBox, QPlainTextEdit, QWidget,
)

from yzzhub import theme
from yzzhub.image_field import ImageField
from yzzhub.markdown import build_drama_markdown
from yzzhub.result_dialog import ResultDialog

TITLE_MIN_CHARS = 1    # 帖子标题最少字符数
DOWNLOAD_HEIGHT = 140  # 下载链接多行框的初始高度

# 简介强制单行：换行 / 制表符（含 \r\n、\r、\n）折叠为一个空格。
_INTRO_BREAKS = re.compile(r"[\r\n\t]+")


class _SingleLineEdit(QLineEdit):
    """单行输入框：粘贴的多行文本强制合并为一行。

    QLineEdit 不接受键入换行，但粘贴会把 \r\n / \n 原样带入文本
    （已实测），因此监听 textChanged 统一清洗，覆盖快捷键粘贴、
    右键菜单粘贴等全部路径；光标位置按清洗结果等价换算，不跳末尾。
    """

    def __init__(self, placeholder=""):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.textChanged.connect(self._force_single_line)

    def _force_single_line(self, text):
        cleaned = _INTRO_BREAKS.sub(" ", text)
        if cleaned == text:
            return
        self.blockSignals(True)
        pos = self.cursorPosition()
        head = _INTRO_BREAKS.sub(" ", text[:pos])
        self.setText(cleaned)
        self.setCursorPosition(min(len(head), len(cleaned)))
        self.blockSignals(False)


class DramaPage(QWidget):
    """主页顶部「短剧」选项卡对应的内容页。"""

    statusMessage = pyqtSignal(str)          # -> 主窗口状态栏
    settingsRequested = pyqtSignal(object)   # -> 主窗口跳设置页（缺密钥时）

    def __init__(self, parent=None):
        super().__init__(parent)

        # ---------------- 1. 输入控件 ----------------
        self.title_edit = theme.size_input(self._line_edit(
            "最少 1 个字符"))
        self.image_field = ImageField()               # 图片 URL + 上传 + 历史

        # 短剧简介：单行输入，导出为「> …」引用行（图片下方、链接上方）；
        # 粘贴的多行文本自动合并为一行（见 _SingleLineEdit）。
        self.intro_edit = theme.size_input(
            _SingleLineEdit("短剧简介（可选，导出为引用行）"))

        self.download_edit = QPlainTextEdit()
        self.download_edit.setPlaceholderText(
            "下载链接（可多行）")
        self.download_edit.setMinimumHeight(DOWNLOAD_HEIGHT)
        self.download_edit.setTabChangesFocus(True)   # Tab 键切换焦点而非插入制表符

        # ---------------- 2. 表单卡片 ----------------
        rows = [
            (theme.required_label("帖子标题"), self.title_edit),
            (theme.plain_label("帖子图片"), self.image_field),
            (theme.plain_label("短剧简介"), self.intro_edit),
            (theme.required_label("下载链接"), self.download_edit),
        ]
        box = QGroupBox("短剧帖子")
        box.setLayout(theme.build_form(rows))

        # ---------------- 3. 滚动区 ----------------
        scroll = theme.make_scroll_area(box)

        # ---------------- 4. 底部动作条 ----------------
        self.btn_clear = theme.action_button(
            "清除", "clearBtn", theme.CLEAR_BUTTON_WIDTH,
            tooltip="清空本页所有输入")
        self.btn_clear.clicked.connect(self.on_clear)
        self.btn_generate = theme.action_button(
            "生成", "genBtn", theme.GENERATE_BUTTON_WIDTH)
        self.btn_generate.clicked.connect(self.on_generate)
        bottom = theme.make_bottom_bar(
            "生成后可在结果对话框一键复制 标题 与 内容",
            self.btn_clear, self.btn_generate)

        # ---------------- 5. 页面组装 ----------------
        theme.layout_page(self, scroll, bottom)

        # ---------------- 信号转发 ----------------
        self.image_field.statusMessage.connect(self.statusMessage)
        self.image_field.settingsRequested.connect(self.settingsRequested)

    @staticmethod
    def _line_edit(placeholder):
        """带占位提示的输入框（高度由调用处统一）。"""
        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        return edit

    # ---------------- 清除 ----------------
    def clear_form(self):
        """清空本页所有输入。"""
        self.title_edit.clear()
        self.image_field.set_text("")
        self.intro_edit.clear()
        self.download_edit.clear()

    def on_clear(self):
        self.clear_form()
        self.title_edit.setFocus()
        self.statusMessage.emit("已清空本页全部输入。")

    # ---------------- 校验与生成 ----------------
    def _validate(self):
        """返回首个校验错误信息（None 表示通过）。"""
        title = self.title_edit.text().strip()
        if len(title) < TITLE_MIN_CHARS:
            return "请填写帖子标题（最少 %d 个字符）。" % TITLE_MIN_CHARS
        if not self.download_edit.toPlainText().strip():
            return "请填写下载链接。"
        return None

    def build_result(self):
        """校验并生成 (标题, 内容)；校验失败抛 ValueError。"""
        error = self._validate()
        if error:
            raise ValueError(error)
        title = self.title_edit.text().strip()
        content = build_drama_markdown(
            title,
            self.image_field.text(),
            self.intro_edit.text(),
            self.download_edit.toPlainText(),
        )
        return title, content

    def on_generate(self):
        try:
            title, content = self.build_result()
        except ValueError as e:
            QMessageBox.warning(self, "信息不完整", str(e))
            return
        self.statusMessage.emit("已生成，请在结果对话框中复制。")
        dialog = ResultDialog(self, title, content)
        dialog.exec_()
