#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""YZZ Hub —— markdown 导出工具（入口）。

字幕 / 短剧帖子信息 -> 生成可复制的 markdown（标题 + 内容）。
"""

import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QApplication

from yzzhub import APP_NAME, APP_VERSION
from yzzhub.main_window import MainWindow


def resource_path(relative):
    """资源路径：源码运行取项目目录；PyInstaller 打包后取 _MEIPASS。

    打包脚本里用 --add-data "assets;assets"(Win) / "assets:assets"(Mac)
    把 assets 目录一起带进包里。
    """
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative)


def pick_cjk_font():
    """各平台挑选一个更合适的中文 UI 字体（缺字体时 Qt 自动回退）。"""
    if sys.platform.startswith("win"):
        return QFont("Microsoft YaHei", 10)
    if sys.platform == "darwin":
        return QFont("PingFang SC", 13)
    return QFont("Noto Sans SC", 10)


def main():
    # 启动顺序：配置 Qt 显示属性 -> 创建 QApplication -> 元数据与图标 -> 主窗口。
    # 高分屏适配（Win7 / Win10 / macOS 均有效，必须在创建 QApplication 之前设置）
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setFont(pick_cjk_font())

    icon_path = resource_path(os.path.join("assets", "icon.png"))
    if os.path.isfile(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
