# -*- coding: utf-8 -*-
"""统一视觉规范（设计令牌）与全局样式表。

全应用的尺寸、间距、颜色只在本模块定义一次，各界面模块引用常量
组装布局，从而保证边距、输入框高度、按钮大小处处一致。

┌─────────────────── 数值速览（像素） ───────────────────┐
│ 页面外边距  PAGE_MARGINS      (18, 14, 18, 10) 左/上/右/下 │
│ 分组框内边距 FORM_MARGINS     (16, 6, 16, 14)            │
│ 输入框高度  INPUT_HEIGHT      34（所有单行输入/行内按钮）  │
│ 普通按钮高  BUTTON_HEIGHT     32（返回 / 关闭 / 复制）    │
│ 动作按钮高  ACTION_HEIGHT     38（清除 / 生成 / 保存）    │
│ 表单行间距  FORM_ROW_SPACING  12                          │
│ 字段名与输入框间距 LABEL_GAP   3                          │
│ 页面区块间距 SECTION_SPACING  10                          │
└──────────────────────────────────────────────────────────┘

颜色：主色（蓝）用于选项卡与聚焦边框，强调色（绿）用于「生成 / 保存」
主按钮，红色仅作必填星号与删除入口，辅助文字统一灰色。

提供的组装函数（页面按序调用即可拼出统一外观）：
- required_label / plain_label   字段名（必填带红色 *）
- size_input / size_inline_button / size_normal_button /
  size_action_button             各类控件的高度与最小宽度
- hint_label                     灰色辅助提示
- build_form                     [(字段名, 输入控件)] -> 纵向表单布局
- make_scroll_area              无边框竖向滚动区（高度不足时滚动）
- make_bottom_bar                底部动作条：左提示 + 右按钮组
- layout_page                    页面外层：统一边距 + 滚动区 + 底部条
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout,
)

# ---------------- 尺寸与间距 ----------------
PAGE_MARGINS = (18, 14, 18, 10)     # 页面四周留白：左、上、右、下
FORM_MARGINS = (16, 6, 16, 14)      # 分组框内部留白
FORM_ROW_SPACING = 12               # 表单相邻字段组的间距
LABEL_GAP = 3                       # 字段名与其输入控件的间距
SECTION_SPACING = 10                # 页面大区块（滚动区 / 底部条）间距

INPUT_HEIGHT = 34                   # 单行输入框与行内按钮高度
BUTTON_HEIGHT = 32                  # 普通按钮高度
ACTION_HEIGHT = 38                  # 动作按钮（清除 / 生成 / 保存）高度

INLINE_BUTTON_WIDTH = 84            # 行内按钮（上传 / 历史）最小宽度
CLEAR_BUTTON_WIDTH = 96             # 「清除」最小宽度
GENERATE_BUTTON_WIDTH = 130         # 「生成」最小宽度
COPY_BUTTON_WIDTH = 96              # 「复制 / 关闭」最小宽度

# ---------------- 颜色 ----------------
COLOR_PRIMARY = "#1c5fb0"           # 主色：选项卡、聚焦边框
COLOR_SUCCESS = "#2e7d32"           # 强调色：生成 / 保存主按钮
COLOR_DANGER = "#c62828"            # 红色：必填星号、删除入口
COLOR_HINT = "#8a94a0"              # 辅助提示文字
COLOR_MUTED = "#999999"             # 次要小字（路径 / 版本号）


# ---------------- 字段名标签 ----------------
def required_label(name):
    """必填字段名：名称 + 红色 *（* 即必填标识，不另写「必填」字样）。"""
    return QLabel("%s <span style='color:%s'>*</span>" % (name, COLOR_DANGER))


def plain_label(name):
    """普通（非必填）字段名。"""
    return QLabel(name)


def hint_label(text):
    """灰色辅助提示文字（底部条与对话框通用）。"""
    label = QLabel(text)
    label.setStyleSheet("color: %s;" % COLOR_HINT)
    return label


# ---------------- 控件尺寸 ----------------
def size_input(widget):
    """单行输入控件统一到标准输入高度。"""
    widget.setMinimumHeight(INPUT_HEIGHT)
    return widget


def size_inline_button(button, width=INLINE_BUTTON_WIDTH):
    """行内按钮（上传 / 历史 / 复制）：与输入框同高，宽度统一。"""
    button.setMinimumHeight(INPUT_HEIGHT)
    button.setMinimumWidth(width)
    return button


def size_normal_button(button, width=None):
    """普通按钮（返回 / 关闭）：统一高度，可选最小宽度。"""
    button.setMinimumHeight(BUTTON_HEIGHT)
    if width:
        button.setMinimumWidth(width)
    return button


def size_action_button(button, width):
    """动作按钮（清除 / 生成 / 保存）：统一高度与最小宽度。"""
    button.setMinimumHeight(ACTION_HEIGHT)
    button.setMinimumWidth(width)
    return button


# ---------------- 布局组装 ----------------
def build_form(rows, margins=FORM_MARGINS, spacing=FORM_ROW_SPACING):
    """把 [(字段名控件, 输入控件), ...] 组成纵向表单布局。

    每个字段为「字段名在上、输入控件整宽在下」的竖排小组；末尾追加
    弹性空白，让内容自然靠上、不随窗口拉伸。
    """
    form = QVBoxLayout()
    form.setContentsMargins(*margins)
    form.setSpacing(spacing)
    for label, field in rows:
        pair = QVBoxLayout()
        pair.setContentsMargins(0, 0, 0, 0)
        pair.setSpacing(LABEL_GAP)
        pair.addWidget(label)
        pair.addWidget(field)
        form.addLayout(pair)
    form.addStretch(1)
    return form


def make_scroll_area(content):
    """无边框竖向滚动区：内容高于窗口时出现滚动条，宽度跟随窗口。"""
    scroll = QScrollArea()
    scroll.setWidget(content)
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QScrollArea.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    return scroll


def make_bottom_bar(hint_text, *buttons):
    """底部动作条：左侧灰色提示，右侧按钮组（按传入顺序排列）。"""
    bar = QHBoxLayout()
    bar.setSpacing(10)
    bar.addWidget(hint_label(hint_text))
    bar.addStretch(1)
    for button in buttons:
        bar.addWidget(button)
    return bar


def layout_page(page, scroll, bottom):
    """页面外层布局：统一页边距，滚动区占主体，动作条固定在底部。

    page 为页面自身（QVBoxLayout 直接挂在 page 上）；
    scroll 为 make_scroll_area 的返回值；bottom 为 make_bottom_bar 的返回值。
    """
    outer = QVBoxLayout(page)
    outer.setContentsMargins(*PAGE_MARGINS)
    outer.setSpacing(SECTION_SPACING)
    outer.addWidget(scroll, 1)
    outer.addLayout(bottom)
    return outer


def action_button(text, object_name, min_width, tooltip=None):
    """创建统一规格的动作按钮（清除 / 生成 / 保存）。"""
    button = QPushButton(text)
    button.setObjectName(object_name)
    size_action_button(button, min_width)
    if tooltip:
        button.setToolTip(tooltip)
    return button


# ---------------- 全局样式表 ----------------
# 仅在 MainWindow 挂载一次，全部子页面与对话框随之生效。
# 按钮高度不写入 QSS（由 setMinimumHeight 控制），避免双重约束。
GLOBAL_QSS = """
    QMainWindow, QDialog { background: #f5f6f8; }

    /* ---- 页头 ---- */
    #headerBar {
        background: #ffffff;
        border-bottom: 1px solid #d8dde4;
    }
    QPushButton {
        background: #ffffff;
        border: 1px solid #c3cbd6;
        border-radius: 4px;
        padding: 6px 16px;
        color: #2f3b47;
    }
    QPushButton:hover { background: #eef3f8; }
    QPushButton:pressed { background: #e2e9f1; }
    QPushButton:disabled { color: #9aa4b0; background: #f2f4f7; }
    QPushButton#homeBtn, QPushButton#settingsBtn {
        padding: 6px 18px;
        font-weight: 600;
    }

    /* ---- 顶部选项卡（字幕 / 短剧） ---- */
    QPushButton[role="tab"] {
        background: transparent;
        color: #4a5561;
        border: none;
        border-bottom: 2px solid transparent;
        padding: 9px 34px;
        font-size: 14px;
    }
    QPushButton[role="tab"]:hover { color: #1c5fb0; }
    QPushButton[role="tab"]:checked {
        color: #1c5fb0;
        font-weight: 600;
        border-bottom: 2px solid #1c5fb0;
    }

    /* ---- 分组框卡片 ---- */
    QGroupBox {
        font-weight: 600;
        border: 1px solid #c8ccd4;
        border-radius: 6px;
        margin-top: 12px;
        background: #ffffff;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 4px;
        color: #3a4a5a;
    }

    /* ---- 输入控件 ---- */
    QLineEdit, QPlainTextEdit {
        background: #ffffff;
        border: 1px solid #c8ccd4;
        border-radius: 4px;
        padding: 5px 8px;
        selection-background-color: #bcd7f5;
    }
    QLineEdit:focus, QPlainTextEdit:focus {
        border: 1px solid #1c5fb0;
    }

    /* ---- 动作按钮 ---- */
    QPushButton#clearBtn {
        padding: 8px 22px;
        font-size: 15px;
    }
    QPushButton#genBtn, QPushButton#saveBtn {
        background-color: #2e7d32;
        color: white;
        padding: 8px 28px;
        border: none;
        border-radius: 4px;
        font-size: 15px;
        font-weight: 600;
    }
    QPushButton#genBtn:hover, QPushButton#saveBtn:hover {
        background-color: #286d2c;
    }
    QPushButton#genBtn:pressed, QPushButton#saveBtn:pressed {
        background-color: #235f27;
    }
    QPushButton#genBtn:disabled, QPushButton#saveBtn:disabled {
        background-color: #a5c8a7;
        color: #f0f4f0;
    }

    /* ---- 滚动区与滚动条 ---- */
    QScrollArea { background: transparent; border: none; }
    QScrollBar:vertical {
        background: transparent;
        width: 10px;
        margin: 2px;
    }
    QScrollBar::handle:vertical {
        background: #c3cbd6;
        border-radius: 5px;
        min-height: 40px;
    }
    QScrollBar::handle:vertical:hover { background: #a8b3c1; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0;
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: transparent;
    }

    /* ---- 状态栏 ---- */
    QStatusBar {
        background: #ffffff;
        color: #5a6470;
    }
"""
