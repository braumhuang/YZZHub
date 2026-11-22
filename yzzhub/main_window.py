# -*- coding: utf-8 -*-
"""主窗口：页头（论坛按钮 / 字幕-短剧选项卡 / 设置按钮）+ 页面栈 + 状态栏。

- 左上角「论坛」用系统默认浏览器打开 https://bbs.yzz.me；
- 顶部中间「字幕」「短剧」选项卡（互斥可选中按钮），默认选中字幕；
- 右上角「设置」进入设置页（图床方案：默认 freeimage，备选 imgbb）；
  设置页「保存 / 返回」回到之前的选项卡；
- 选了 imgbb 而未填 API 密钥时首次上传跳转设置页，保存后自动回表单继续；
- 全局样式统一挂在 MainWindow（见 yzzhub.theme.GLOBAL_QSS），
  子页面与对话框自动继承，保证边距 / 控件高度 / 按钮规格处处一致。
"""

from PyQt5.QtCore import QUrl, Qt, pyqtSlot
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import (
    QApplication, QButtonGroup, QHBoxLayout, QMainWindow, QPushButton,
    QStackedWidget, QVBoxLayout, QWidget,
)

from yzzhub import APP_NAME, APP_VERSION, HOME_URL
from yzzhub import theme
from yzzhub.drama_page import DramaPage
from yzzhub.settings_page import SettingsPage
from yzzhub.subtitle_page import SubtitlePage

INDEX_SUBTITLE = 0   # 页面栈下标：字幕页
INDEX_DRAMA = 1      # 页面栈下标：短剧页
INDEX_SETTINGS = 2   # 页面栈下标：设置页


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("%s v%s —— markdown 生成工具" % (APP_NAME, APP_VERSION))

        # 依据屏幕可用区域设定初始尺寸（与 ImgZip 相同的防小屏策略）。
        screen = QApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()
            window_w = min(820, max(1, available.width() - 40))
            window_h = min(640, max(1, available.height() - 40))
            self.setMinimumSize(min(660, window_w), min(560, window_h))
            self.resize(window_w, window_h)
            self.move(
                available.x() + (available.width() - window_w) // 2,
                available.y() + (available.height() - window_h) // 2,
            )
        else:
            self.setMinimumSize(660, 560)
            self.resize(820, 640)

        # ---------------- 页头 ----------------
        self.btn_home = QPushButton("论坛")
        self.btn_home.setObjectName("homeBtn")
        self.btn_home.setToolTip("使用浏览器访问 %s" % HOME_URL)
        self.btn_home.clicked.connect(self.on_open_home)

        # 顶部中间选项卡：两个互斥的可选中按钮（进入设置页时可以全部取消高亮）
        self.btn_tab_subtitle = QPushButton("字幕")
        self.btn_tab_drama = QPushButton("短剧")
        for button in (self.btn_tab_subtitle, self.btn_tab_drama):
            button.setProperty("role", "tab")
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            button.setFocusPolicy(Qt.NoFocus)
        self.tab_group = QButtonGroup(self)
        self.tab_group.setExclusive(True)
        self.tab_group.addButton(self.btn_tab_subtitle, INDEX_SUBTITLE)
        self.tab_group.addButton(self.btn_tab_drama, INDEX_DRAMA)
        # 先设置默认选中（尚未连接信号，不会触发页面切换）
        self.btn_tab_subtitle.setChecked(True)
        self.btn_tab_subtitle.toggled.connect(
            lambda checked: self.on_tab_toggled(INDEX_SUBTITLE, checked))
        self.btn_tab_drama.toggled.connect(
            lambda checked: self.on_tab_toggled(INDEX_DRAMA, checked))

        self.btn_settings = QPushButton("设置")
        self.btn_settings.setObjectName("settingsBtn")
        self.btn_settings.setToolTip("选择图床方案（默认 freeimage）并维护 API 密钥")
        self.btn_settings.clicked.connect(lambda: self.open_settings())

        header = QHBoxLayout()
        header.setContentsMargins(10, 8, 10, 8)   # 页头留白（左右 10、上下 8）
        header.addWidget(self.btn_home)
        header.addStretch(1)                       # 选项卡居中：两侧弹性空白
        header.addWidget(self.btn_tab_subtitle)
        header.addWidget(self.btn_tab_drama)
        header.addStretch(1)
        header.addWidget(self.btn_settings)
        header_widget = QWidget()
        header_widget.setObjectName("headerBar")
        header_widget.setLayout(header)

        # ---------------- 页面栈 ----------------
        self.subtitle_page = SubtitlePage()
        self.drama_page = DramaPage()
        self.settings_page = SettingsPage()

        self.stack = QStackedWidget()
        self.stack.addWidget(self.subtitle_page)     # 0 字幕
        self.stack.addWidget(self.drama_page)        # 1 短剧
        self.stack.addWidget(self.settings_page)      # 2 设置

        central = QWidget()
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(header_widget)
        outer.addWidget(self.stack, 1)
        self.setCentralWidget(central)

        # 信号：表单页 -> 主窗口
        for page in (self.subtitle_page, self.drama_page):
            page.statusMessage.connect(self.show_status)
            page.settingsRequested.connect(self.on_field_settings_requested)
        # 信号：设置页 -> 主窗口
        self.settings_page.saved.connect(self.on_settings_saved)
        self.settings_page.backRequested.connect(self.on_settings_back)
        self.settings_page.statusMessage.connect(self.show_status)

        self._settings_return_index = INDEX_SUBTITLE
        self._upload_requester = None

        self._apply_styles()
        self.statusBar().showMessage(
            "就绪：填写表单信息后，点击右下角「生成」生成 markdown；"
            "「论坛」访问论坛，「设置」维护图床与 API 密钥。")

    # ---------------- 样式 ----------------
    def _apply_styles(self):
        """挂载全局样式表（唯一入口，令牌见 yzzhub.theme）。"""
        self.setStyleSheet(theme.GLOBAL_QSS)

    # ---------------- 状态栏 ----------------
    def show_status(self, message, timeout=8000):
        """显示状态栏提示；timeout 毫秒后自动清空（0 表示常驻）。"""
        self.statusBar().showMessage(message, timeout)

    # ---------------- 主页 ----------------
    def on_open_home(self):
        QDesktopServices.openUrl(QUrl(HOME_URL))
        self.show_status("正在使用浏览器打开论坛：%s" % HOME_URL)

    # ---------------- 选项卡 ----------------
    @pyqtSlot(int, bool)
    def on_tab_toggled(self, index, checked):
        if checked and index in (INDEX_SUBTITLE, INDEX_DRAMA):
            self.stack.setCurrentIndex(index)

    def checked_tab_index(self):
        """当前选中的选项卡序号；都在设置页时返回 None。"""
        if self.btn_tab_subtitle.isChecked():
            return INDEX_SUBTITLE
        if self.btn_tab_drama.isChecked():
            return INDEX_DRAMA
        return None

    def current_form_index(self):
        """当前（或最近一次）表单页序号。"""
        index = self.checked_tab_index()
        if index is not None:
            return index
        return self._settings_return_index

    # ---------------- 设置页 ----------------
    def open_settings(self, requester=None):
        """进入设置页；requester 为发起跳转的 ImageField（可空）。"""
        index = self.checked_tab_index()
        if index is not None:
            self._settings_return_index = index
        self._upload_requester = requester
        self.stack.setCurrentIndex(INDEX_SETTINGS)
        self._clear_tab_highlight()
        self.show_status(
            "设置：选择图床方案（默认 freeimage）并填写 API 密钥后点击「保存」。", 0)

    def _clear_tab_highlight(self):
        """取消两个选项卡高亮（进入设置页时使用）。

        互斥 QButtonGroup 会拒绝把当前选中按钮 setChecked(False)，
        因此先临时关闭互斥，全部取消后再恢复互斥。
        """
        self.tab_group.setExclusive(False)
        for button in (self.btn_tab_subtitle, self.btn_tab_drama):
            button.blockSignals(True)
            button.setChecked(False)
            button.blockSignals(False)
        self.tab_group.setExclusive(True)

    def leave_settings(self):
        """返回之前所在的表单页。"""
        index = self._settings_return_index
        if index == INDEX_DRAMA:
            self.btn_tab_drama.setChecked(True)
        else:
            self.btn_tab_subtitle.setChecked(True)
        self.stack.setCurrentIndex(index)

    def on_field_settings_requested(self, field):
        self.open_settings(requester=field)

    def on_settings_saved(self):
        """设置页「保存」：如有挂起的上传则返回表单并自动继续。"""
        requester = self._upload_requester
        self._upload_requester = None
        if requester is not None and requester.has_pending_upload():
            self.leave_settings()
            self.show_status("API 密钥已保存，正在继续上传……", 0)
            requester.resume_pending_upload()
        else:
            self.leave_settings()

    def on_settings_back(self):
        """设置页「返回」：设置有改动时自动保存，再回到表单页。"""
        if self.settings_page.has_changes():
            self.settings_page.on_save()
        else:
            self.leave_settings()
        self._upload_requester = None
