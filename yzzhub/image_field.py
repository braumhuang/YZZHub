# -*- coding: utf-8 -*-
"""帖子图片字段：URL 输入框 + 「上传」按钮 + 「历史」下拉列表。

- 输入框始终保存图片原始 URL（手输、上传成功回填、历史选取均如此），
  i3wp.com 加速只在生成时统一附加（见 markdown.wp_accelerate）；
- 点击「上传」按设置页选择的图床方案上传：默认 freeimage.host
  （免注册，内置公共密钥）；备选 imgbb（需注册）。未选 imgbb 而密钥
  未设置时不弹任何对话框，直接跳设置页（MainWindow 监听
  settingsRequested 信号），保存密钥返回后自动重新选图并继续本次上传；
  密钥已设置则直接打开图片选择；
- 上传在后台 QThread 中执行（UploadThread 按图床分发到
  freeimage / imgbb 模块），成功后把原始 URL 写入输入框并记入历史；
- 「历史」弹层右缘与「历史」按钮右缘对齐：每条显示图片名与原始 URL，
  右侧「删除」按钮；点击条目把该图片的原始 URL 写入输入框。
"""

import os

from PyQt5.QtCore import QPoint, QThread, Qt, pyqtSignal
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import (
    QApplication, QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from yzzhub import config, theme, PROVIDER_IMGBB
from yzzhub.freeimage import upload_image as freeimage_upload
from yzzhub.imgbb import upload_image as imgbb_upload

IMAGE_FILTER = "图片 (*.jpg *.jpeg *.png *.bmp *.webp *.gif);;所有文件 (*.*)"

NAME_WIDTH = 170   # 历史行内图片名可用宽度（超出省略号）
URL_WIDTH = 230    # 历史行内 URL 可用宽度（超出省略号）
POPUP_WIDTH = 470  # 历史弹层总宽
POPUP_MAX_HEIGHT = 300


def _elided(text, width):
    """中文安全省略：用省略号截断超宽文本。"""
    metrics = QFontMetrics(QLabel().font())
    return metrics.elidedText(text, Qt.ElideRight, width)


class UploadThread(QThread):
    """后台执行图床上传（freeimage / imgbb）；结果通过信号回主线程。"""

    succeeded = pyqtSignal(dict)
    failed = pyqtSignal(str)

    def __init__(self, provider, api_key, file_path, parent=None):
        super().__init__(parent)
        self.provider = provider
        self.api_key = api_key
        self.file_path = file_path

    def run(self):
        func = (imgbb_upload if self.provider == PROVIDER_IMGBB
                else freeimage_upload)
        try:
            result = func(self.api_key, self.file_path)
            self.succeeded.emit(result)
        except Exception as e:  # 上传失败不拖垮界面，统一转为提示
            self.failed.emit(str(e))


class _HistoryRow(QFrame):
    """历史弹层里的一行：整行可点（写入输入框），右侧「删除」。"""

    clicked = pyqtSignal(str)      # 图片原始 URL
    deleteRequested = pyqtSignal(str)

    def __init__(self, name, url, parent=None):
        super().__init__(parent)
        self.url = url
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(
            "_HistoryRow { background: #ffffff; border: none; border-bottom: 1px solid #eee; }"
            "_HistoryRow:hover { background: #eef3f8; }")

        name_label = QLabel(_elided(name, NAME_WIDTH))
        name_label.setToolTip(name)
        url_label = QLabel(_elided(url, URL_WIDTH))
        url_label.setStyleSheet("color: #999; font-size: 11px;")
        url_label.setToolTip(url)
        btn_del = QPushButton("删除")
        btn_del.setFlat(True)
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setStyleSheet(
            "QPushButton { color: #c62828; border: none; padding: 4px 8px; }"
            "QPushButton:hover { color: #a02222; text-decoration: underline; }")
        btn_del.clicked.connect(lambda: self.deleteRequested.emit(self.url))

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(0)
        text_layout.addWidget(name_label)
        text_layout.addWidget(url_label)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 6, 6)
        layout.setSpacing(8)
        layout.addLayout(text_layout, 1)
        layout.addWidget(btn_del, 0, Qt.AlignRight | Qt.AlignVCenter)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.url)
        super().mousePressEvent(event)


class HistoryPopup(QFrame):
    """上传历史下拉弹层（Qt.Popup，点击外部自动关闭）。"""

    selected = pyqtSignal(str)   # 选中的图片原始 URL

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Popup)
        self.setObjectName("historyPopup")
        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedSize(POPUP_WIDTH, min(POPUP_MAX_HEIGHT, 340))
        self.setStyleSheet(
            "#historyPopup { background: #ffffff; border: 1px solid #c8ccd4;"
            " border-radius: 6px; }")

        self._rows_host = QWidget()
        self._rows_layout = QVBoxLayout(self._rows_host)
        self._rows_layout.setContentsMargins(6, 6, 6, 6)
        self._rows_layout.setSpacing(0)
        self._rows_layout.addStretch(1)

        self._scroll = QScrollArea(self)
        self._scroll.setWidget(self._rows_host)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(2, 2, 2, 2)
        outer.addWidget(self._scroll)

    def set_records(self, records):
        """重建列表内容；records 为 [{name, url, ...}]。"""
        while self._rows_layout.count() > 1:
            item = self._rows_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        for record in records:
            row = _HistoryRow(record.get("name", ""), record.get("url", ""))
            row.clicked.connect(self._on_row_clicked)
            row.deleteRequested.connect(self._on_row_delete)
            self._rows_layout.insertWidget(self._rows_layout.count() - 1, row)
        height = max(120, min(POPUP_MAX_HEIGHT, 52 * len(records) + 16))
        self.setFixedSize(POPUP_WIDTH, height)

    def _on_row_clicked(self, url):
        self.selected.emit(url)
        self.hide()

    def _on_row_delete(self, url):
        config.remove_history(url)
        self.set_records(config.get_history())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)


class ImageField(QWidget):
    """帖子图片输入行：QLineEdit + 上传 + 历史。"""

    settingsRequested = pyqtSignal(object)   # 缺 API 密钥 -> 请求打开设置页
    statusMessage = pyqtSignal(str)          # 状态栏提示

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread = None
        self._pending_path = ""     # 缺密钥时挂起的待上传文件（路径已选中）
        self._pending_no_key = False  # 点「上传」时缺密钥：保存后重新选图继续

        self.edit = QLineEdit()
        self.edit.setPlaceholderText(
            "图片 URL，或点击「上传」使用图床（默认 freeimage）")
        theme.size_input(self.edit)   # 输入框高度与其他页面统一

        self.btn_upload = QPushButton("上传")
        theme.size_inline_button(self.btn_upload)   # 与输入框同高
        self.btn_upload.setToolTip(
            "选择本地图片上传到当前图床（默认 freeimage.host），"
            "成功后 URL 自动填入")
        self.btn_upload.clicked.connect(self._on_upload_clicked)

        self.btn_history = QPushButton("历史 ▾")
        theme.size_inline_button(self.btn_history)   # 与输入框同高
        self.btn_history.setToolTip("查看最近上传的图片，点击填入 URL，或删除记录")
        self.btn_history.clicked.connect(self._show_history)

        self._popup = HistoryPopup()
        self._popup.selected.connect(self._on_history_selected)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self.edit, 1)
        layout.addWidget(self.btn_upload)
        layout.addWidget(self.btn_history)

    # ---------------- 取值 ----------------
    def text(self):
        """当前输入的图片 URL（去首尾空白）。"""
        return self.edit.text().strip()

    def set_text(self, value):
        self.edit.setText(value or "")
        self.edit.setCursorPosition(0)   # 写入后从头显示

    # ---------------- 上传 ----------------
    def _on_upload_clicked(self):
        """点击「上传」：先查当前图床的 API 密钥，缺密钥直接跳设置页
        （不弹任何对话框）。

        freeimage 内置公共密钥永不为空，实际只有「选了 imgbb 但未填密钥」
        才会走到跳转分支。MainWindow 在设置页保存后回调
        resume_pending_upload（见下），届时重新打开选图对话框继续本次上传。
        """
        if not config.get_active_api_key():
            self._pending_no_key = True
            self.settingsRequested.emit(self)
            return
        self._pending_no_key = False
        path, _ = QFileDialog.getOpenFileName(
            self, "选择要上传的图片", "", IMAGE_FILTER)
        if not path:
            return
        self.upload(path)

    def upload(self, path):
        """上传本地图片（路径已知时的入口，如选图后续传）。

        当前图床缺密钥则挂起该路径并请求跳转设置页（无弹窗），
        保存密钥返回后自动继续上传这张图片。
        """
        if not config.get_active_api_key():
            self._pending_path = path
            self.settingsRequested.emit(self)
            return
        self._start_upload(path)

    def _start_upload(self, path):
        if self._thread is not None and self._thread.isRunning():
            self.statusMessage.emit("正在上传中，请稍候……")
            return
        if not os.path.isfile(path):
            QMessageBox.warning(self, "文件不存在", "待上传的图片不存在：\n%s" % path)
            return
        self._pending_path = ""
        self.btn_upload.setEnabled(False)
        self.btn_history.setEnabled(False)
        self.btn_upload.setText("上传中…")
        self.statusMessage.emit("正在上传图片：%s" % os.path.basename(path))
        self._thread = UploadThread(
            config.get_provider(), config.get_active_api_key(), path,
            parent=self)
        self._thread.succeeded.connect(self._on_uploaded)
        self._thread.failed.connect(self._on_upload_failed)
        self._thread.finished.connect(self._on_upload_finished)
        self._thread.start()

    def _on_uploaded(self, result):
        # 输入框始终保存原始 URL；i3wp.com 加速在生成时统一附加。
        self.edit.setText(result["url"])
        self.edit.setCursorPosition(0)   # 长链接从头显示，不滚动到尾部
        config.add_history(result["name"], result["url"])
        self.statusMessage.emit(
            "上传成功：%s（原始 URL 已写入并加入历史，生成时自动加速）"
            % result["name"])

    def _on_upload_failed(self, message):
        QMessageBox.critical(self, "上传失败", message)
        self.statusMessage.emit("图片上传失败。")

    def _on_upload_finished(self):
        self.btn_upload.setEnabled(True)
        self.btn_history.setEnabled(True)
        self.btn_upload.setText("上传")
        self._thread = None

    # ---------------- 挂起续传（设置页保存密钥后调用） ----------------
    def resume_pending_upload(self):
        """设置页保存后继续挂起的上传。

        - 有挂起路径：直接续传该文件；
        - 点击「上传」时缺密钥（路径未选）：重新打开选图对话框继续；
        - 密钥仍为空：放弃本次续传并提示。
        """
        path = self._pending_path
        no_key = self._pending_no_key
        self._pending_path = ""
        self._pending_no_key = False
        if not path and not no_key:
            return
        if not config.get_active_api_key():
            if path:
                QMessageBox.warning(
                    self, "仍未设置密钥", "API 密钥仍为空，本次上传未继续。")
            else:
                self.statusMessage.emit("API 密钥仍为空，请先设置后再上传。")
            return
        if path:
            self._start_upload(path)
        else:
            self._on_upload_clicked()   # 密钥已就绪：重新选图继续本次上传

    def has_pending_upload(self):
        return bool(self._pending_path) or self._pending_no_key

    # ---------------- 历史 ----------------
    def _show_history(self):
        records = config.get_history()
        if not records:
            self.statusMessage.emit("暂无上传历史记录。")
            QMessageBox.information(
                self, "暂无历史",
                "还没有上传历史记录。\n点击「上传」把第一张图传到图床。")
            return
        self._popup.set_records(records)
        # 弹层右缘对齐「历史」按钮右缘，按钮下方留 4px；
        # 按钮过于靠左时向屏幕左缘收拢，避免弹层越出屏幕。
        anchor = self.btn_history.mapToGlobal(QPoint(0, 0))
        x = anchor.x() + self.btn_history.width() - self._popup.width()
        y = anchor.y() + self.btn_history.height() + 4
        screen = QApplication.primaryScreen()
        if screen is not None:
            left = screen.availableGeometry().left()
            if x < left:
                x = left
        self._popup.show()
        # 部分平台显示带边框的顶层弹层时会整体偏移约 2px（边框宽度），
        # show 之后再次定位，保证右缘与按钮右缘精确对齐。
        self._popup.move(x, y)

    def _on_history_selected(self, url):
        # 历史选取同样回填原始 URL；加速在生成时统一附加。
        self.edit.setText(url)
        self.edit.setCursorPosition(0)   # 长链接从头显示
        self.statusMessage.emit("已从历史填入图片 URL。")
