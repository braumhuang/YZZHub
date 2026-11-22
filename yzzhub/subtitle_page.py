# -*- coding: utf-8 -*-
"""字幕页：帖子信息表单 + 右下角「清除 / 生成」生成 markdown。

必填字段以红色 * 标识：帖子标题（≥3 字符）、影片名称、出演女优、
字幕行数、匹配时长；帖子图片 / 匹配资源 / 解压密码留空时导出省略。

页面组装（外观统一由 yzzhub.theme 定义）：
    1. 输入控件（统一输入高度）
    2. 表单卡片（build_form：字段名在上、输入框整宽在下）
    3. 滚动区（窗口过矮时竖向滚动）
    4. 底部动作条（左提示 + 清除 + 生成）
    5. 外层布局（统一页边距）

交互：
    - 「清除」一键清空本页全部输入；
    - 「生成」校验必填后弹出 ResultDialog（标题 / 内容两个复制框）；
    - ImageField 的状态与设置跳转信号转发给 MainWindow。
"""

from PyQt5.QtWidgets import (
    QGroupBox, QLineEdit, QMessageBox, QWidget,
)
from PyQt5.QtCore import pyqtSignal

from yzzhub import theme
from yzzhub.image_field import ImageField
from yzzhub.markdown import build_subtitle_markdown
from yzzhub.result_dialog import ResultDialog

TITLE_MIN_CHARS = 3   # 帖子标题最少字符数


class SubtitlePage(QWidget):
    """主页顶部「字幕」选项卡对应的内容页。"""

    statusMessage = pyqtSignal(str)          # -> 主窗口状态栏
    settingsRequested = pyqtSignal(object)   # -> 主窗口跳设置页（缺密钥时）

    def __init__(self, parent=None):
        super().__init__(parent)

        # ---------------- 1. 输入控件 ----------------
        self.title_edit = theme.size_input(self._line_edit(
            "最少 3 个字符"))
        self.image_field = ImageField()               # 图片 URL + 上传 + 历史

        self.movie_edit = theme.size_input(self._line_edit(
            "日文原文名称"))
        self.actors_edit = theme.size_input(self._line_edit(
            "中文名、演员名"))
        self.lines_edit = theme.size_input(self._line_edit(
            "263 + 137"))
        self.lines_edit.setToolTip("多个字幕时形如 263 + 137，直接按导出格式填写")
        self.duration_edit = theme.size_input(self._line_edit(
            "00:45:59 + 00:38:33"))
        self.duration_edit.setToolTip(
            "多条字幕时形如 00:45:59 + 00:38:33，直接按导出格式填写")
        self.resource_edit = theme.size_input(self._line_edit(
            "magnet或ed2k(可选)"))
        self.password_edit = theme.size_input(self._line_edit(
            "附件解压密码(可选)"))

        # ---------------- 2. 表单卡片 ----------------
        rows = [
            (theme.required_label("帖子标题"), self.title_edit),
            (theme.plain_label("帖子图片"), self.image_field),
            (theme.required_label("影片名称"), self.movie_edit),
            (theme.required_label("出演女优"), self.actors_edit),
            (theme.required_label("字幕行数"), self.lines_edit),
            (theme.required_label("匹配时长"), self.duration_edit),
            (theme.plain_label("匹配资源"), self.resource_edit),
            (theme.plain_label("解压密码"), self.password_edit),
        ]
        box = QGroupBox("字幕帖子")
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
        # ImageField 的状态提示与设置页跳转请求上抛给 MainWindow。
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
        self.movie_edit.clear()
        self.actors_edit.clear()
        self.lines_edit.clear()
        self.duration_edit.clear()
        self.resource_edit.clear()
        self.password_edit.clear()

    def on_clear(self):
        self.clear_form()
        self.title_edit.setFocus()
        self.statusMessage.emit("已清空本页全部输入。")

    # ---------------- 校验与生成 ----------------
    def _validate(self):
        """返回首个校验错误信息（None 表示通过）。"""
        title = self.title_edit.text().strip()
        if len(title) < TITLE_MIN_CHARS:
            return "帖子标题最少 %d 个字符（当前 %d 个）。" % (
                TITLE_MIN_CHARS, len(title))
        # 必填逐项检查：空则聚焦该项并返回提示。
        checks = [
            (self.movie_edit, "请填写影片名称。"),
            (self.actors_edit, "请填写出演女优。"),
            (self.lines_edit, "请填写字幕行数。"),
            (self.duration_edit, "请填写匹配时长。"),
        ]
        for edit, message in checks:
            if not edit.text().strip():
                edit.setFocus()
                return message
        return None

    def build_result(self):
        """校验并生成 (标题, 内容)；校验失败抛 ValueError。"""
        error = self._validate()
        if error:
            raise ValueError(error)
        title = self.title_edit.text().strip()
        content = build_subtitle_markdown(
            title,
            self.image_field.text(),
            self.movie_edit.text().strip(),
            self.actors_edit.text().strip(),
            self.lines_edit.text().strip(),
            self.duration_edit.text().strip(),
            self.resource_edit.text().strip(),
            self.password_edit.text().strip(),
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
