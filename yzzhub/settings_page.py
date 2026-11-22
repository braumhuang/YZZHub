# -*- coding: utf-8 -*-
"""设置页：图床方案选择与 API 密钥维护。

与字幕 / 短剧页同构的纵向布局（字段名在上、输入框整宽在下），
外观尺寸统一由 yzzhub.theme 定义。

页面自上而下两个分组（freeimage 在 imgbb 上方）：

- 「freeimage 图床上传（默认）」：免注册，内置官网公开的公共密钥，
  开箱即用；选中该组的单选按钮即把 freeimage 设为当前图床；
- 「imgbb 图床上传」：需在 api.imgbb.com 免费注册获取密钥；选中该组
  的单选按钮即把 imgbb 设为当前图床。

两组单选按钮互斥（QButtonGroup），默认选中 freeimage。

- 「保存」写入配置并发射 saved 信号（MainWindow 借此完成
  「挂起上传自动继续」流程）；保存空密钥即清空已存密钥
  （freeimage 空值自动回填内置公共密钥，即恢复默认）；
- 「返回」发射 backRequested 信号回到之前的选项卡页面
  （MainWindow 会在设置有改动时先自动保存）；
- 页脚显示配置文件路径与当前版本号，便于排障。
"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QButtonGroup, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QRadioButton, QVBoxLayout, QWidget,
)

from yzzhub import (
    APP_VERSION, FREEIMAGE_DOC_URL, FREEIMAGE_DEFAULT_KEY,
    IMGBB_DOC_URL, PROVIDER_FREEIMAGE, PROVIDER_IMGBB,
)
from yzzhub import config
from yzzhub import theme


def _radio(text):
    """统一规格的单选按钮（各组第一行，选中即启用该图床）。"""
    button = QRadioButton(text)
    button.setCursor(Qt.PointingHandCursor)
    button.setStyleSheet(
        "QRadioButton { color: #2f3b47; spacing: 8px; }"
        "QRadioButton::indicator { width: 15px; height: 15px; }")
    return button


class SettingsPage(QWidget):
    """「设置」按钮对应的内容页（页面栈第 3 页）。"""

    saved = pyqtSignal()             # 保存成功 -> MainWindow
    backRequested = pyqtSignal()      # 「返回」-> MainWindow
    statusMessage = pyqtSignal(str)   # 状态栏提示 -> MainWindow

    def __init__(self, parent=None):
        super().__init__(parent)

        # ---------------- freeimage 分组（默认，在上） ----------------
        self.radio_freeimage = _radio(
            "使用 freeimage 图床上传（默认，免注册）")
        self.radio_freeimage.setToolTip(
            "选中后「上传」按钮把图片传到 freeimage.host")

        self.fi_key_edit = theme.size_input(QLineEdit())
        self.fi_key_edit.setPlaceholderText("freeimage API 密钥（默认已内置）")
        self.fi_key_edit.setText(config.get_freeimage_key())   # 回显（含默认公共密钥）

        fi_hint = QLabel(
            "默认方案：<a href=\"%s\">freeimage.host</a> 免注册、开箱即用；"
            "已内置官网公开的公共密钥，一般无需改动。"
            "上传的图片存放在 freeimage 图床。" % FREEIMAGE_DOC_URL)
        fi_hint.setOpenExternalLinks(True)
        fi_hint.setWordWrap(True)
        fi_hint.setStyleSheet("color: #666;")

        fi_form = QVBoxLayout()
        fi_form.setContentsMargins(*theme.FORM_MARGINS)
        fi_form.setSpacing(theme.SECTION_SPACING)
        fi_form.addWidget(self.radio_freeimage)
        fi_pair = QVBoxLayout()                       # 字段名 + 输入框竖排小组
        fi_pair.setContentsMargins(0, 0, 0, 0)
        fi_pair.setSpacing(theme.LABEL_GAP)
        fi_pair.addWidget(theme.plain_label("API 密钥"))
        fi_pair.addWidget(self.fi_key_edit)
        fi_form.addLayout(fi_pair)
        fi_form.addWidget(fi_hint)

        fi_box = QGroupBox("freeimage 图床上传（默认）")
        fi_box.setLayout(fi_form)

        # ---------------- imgbb 分组（在下） ----------------
        self.radio_imgbb = _radio(
            "使用 imgbb 图床上传（需注册获取密钥）")
        self.radio_imgbb.setToolTip(
            "选中后「上传」按钮把图片传到 imgbb")

        self.ib_key_edit = theme.size_input(QLineEdit())
        self.ib_key_edit.setPlaceholderText("粘贴 imgbb API 密钥")
        self.ib_key_edit.setText(config.get_api_key())   # 打开即回显已存密钥

        ib_hint = QLabel(
            "备选方案：在 <a href=\"%s\">api.imgbb.com</a> 免费注册即可获得"
            " API 密钥；上传的图片存放在 imgbb 图床。" % IMGBB_DOC_URL)
        ib_hint.setOpenExternalLinks(True)
        ib_hint.setWordWrap(True)
        ib_hint.setStyleSheet("color: #666;")

        ib_form = QVBoxLayout()
        ib_form.setContentsMargins(*theme.FORM_MARGINS)
        ib_form.setSpacing(theme.SECTION_SPACING)
        ib_form.addWidget(self.radio_imgbb)
        ib_pair = QVBoxLayout()
        ib_pair.setContentsMargins(0, 0, 0, 0)
        ib_pair.setSpacing(theme.LABEL_GAP)
        ib_pair.addWidget(theme.plain_label("API 密钥"))
        ib_pair.addWidget(self.ib_key_edit)
        ib_form.addLayout(ib_pair)
        ib_form.addWidget(ib_hint)

        ib_box = QGroupBox("imgbb 图床上传")
        ib_box.setLayout(ib_form)

        # ---------------- 单选互斥（默认 freeimage） ----------------
        self.provider_group = QButtonGroup(self)
        self.provider_group.addButton(self.radio_freeimage)
        self.provider_group.addButton(self.radio_imgbb)
        self.provider_group.setExclusive(True)
        if config.get_provider() == PROVIDER_IMGBB:
            self.radio_imgbb.setChecked(True)
        else:
            self.radio_freeimage.setChecked(True)

        # ---------------- 保存 ----------------
        self.btn_save = theme.action_button(
            "保存", "saveBtn", theme.GENERATE_BUTTON_WIDTH,
            tooltip="保存图床方案与密钥到本地配置文件")
        self.btn_save.clicked.connect(self.on_save)

        # ---------------- 页脚信息 ----------------
        path_label = QLabel("配置文件：%s" % config.config_path())
        path_label.setWordWrap(True)
        path_label.setStyleSheet(
            "color: %s; font-size: 11px;" % theme.COLOR_MUTED)
        path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        version_label = QLabel("YZZ Hub v%s" % APP_VERSION)
        version_label.setStyleSheet(
            "color: %s; font-size: 11px;" % theme.COLOR_MUTED)

        self.btn_back = QPushButton("← 返回")
        theme.size_normal_button(self.btn_back)
        self.btn_back.clicked.connect(self.backRequested.emit)

        bottom = QHBoxLayout()
        bottom.setSpacing(10)
        bottom.addWidget(self.btn_back)
        bottom.addStretch(1)
        bottom.addWidget(version_label, 0, Qt.AlignBottom | Qt.AlignRight)

        # ---------------- 页面组装 ----------------
        outer = QVBoxLayout(self)
        outer.setContentsMargins(*theme.PAGE_MARGINS)
        outer.setSpacing(theme.SECTION_SPACING)
        outer.addWidget(fi_box)     # freeimage 在 imgbb 上方
        outer.addWidget(ib_box)
        outer.addStretch(1)
        outer.addWidget(self.btn_save)
        outer.addWidget(path_label)
        outer.addLayout(bottom)

    # ---------------- 取值 / 保存 ----------------
    def current_provider(self):
        """界面当前选中的图床方案。"""
        return PROVIDER_IMGBB if self.radio_imgbb.isChecked() \
            else PROVIDER_FREEIMAGE

    def has_changes(self):
        """界面内容相对已保存配置是否有改动（供「返回」自动保存判断）。"""
        data = config.load()
        return (
            self.current_provider() != data["upload_provider"]
            or self.fi_key_edit.text().strip() != data["freeimage_api_key"]
            or self.ib_key_edit.text().strip() != data["imgbb_api_key"]
        )

    def on_save(self):
        """保存图床方案与两个密钥；imgbb 空值表示清空，freeimage 空值恢复默认。"""
        provider = self.current_provider()
        fi_key = self.fi_key_edit.text().strip()
        ib_key = self.ib_key_edit.text().strip()
        config.set_provider(provider)
        config.set_freeimage_key(fi_key)
        config.set_api_key(ib_key)
        provider_name = ("freeimage" if provider == PROVIDER_FREEIMAGE
                         else "imgbb")
        self.statusMessage.emit(
            "设置已保存：当前图床为 %s。" % provider_name)
        self.saved.emit()
