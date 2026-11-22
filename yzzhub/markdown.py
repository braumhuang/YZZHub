# -*- coding: utf-8 -*-
"""markdown 结果构建。

- wp_accelerate：把任意图片 URL 包装成 https://i3.wp.com/ 加速链接；
  已是 i3.wp.com 的直接返回（不重复包装），http:// 的同时升级为 https。
- build_subtitle_markdown：字幕页导出内容 = 图片行（可选）+ 信息表格，
  可选字段（匹配资源 / 解压密码）留空时整行省略。
- build_drama_markdown：短剧页导出内容 = 图片行（可选，自动附加 ?w=560
  宽度参数）+ 短剧简介引用行（可选，单行 > 前缀）+ 下载链接代码块；
  链接里本身含 ``` 时自动加长围栏。
"""

import re

from yzzhub import DRAMA_IMAGE_WIDTH, WP_PREFIX

# 简介强制单行：换行 / 制表符（含 \r\n、\r、\n）折叠为一个空格。
_FOLD_BREAKS = re.compile(r"[\r\n\t]+")


def wp_accelerate(url):
    """图片 URL -> i3.wp.com 加速 URL；空值返回空字符串。"""
    url = (url or "").strip()
    if not url:
        return ""
    lowered = url.lower()
    if lowered.startswith("https://i3.wp.com/") or lowered.startswith("http://i3.wp.com/"):
        return url
    if lowered.startswith("https://"):
        return WP_PREFIX + url[len("https://"):]
    if lowered.startswith("http://"):
        return WP_PREFIX + url[len("http://"):]
    return WP_PREFIX + url


def _append_width(url, width):
    """在 URL 后追加宽度参数：已有查询串用 &，否则用 ?。"""
    sep = "&" if "?" in url else "?"
    return "%s%s%s" % (url, sep, width)


def _cell(text):
    """表格单元格安全化：折叠换行、转义竖线。"""
    value = " ".join(str(text or "").split())
    return value.replace("|", "\\|")


def build_subtitle_markdown(title, image_url, movie, actors,
                            subtitle_lines, duration,
                            resource="", password=""):
    """字幕页内容。

    | 字段 | 内容 |
    |---|---|
    | 影片名称 | … |
    | 出演女优 | … |
    | 字幕行数 | …（多字幕时形如 263 + 137，由用户直接输入） |
    | 匹配时长 | …（形如 00:45:59 + 00:38:33） |
    | 匹配资源 | …（可选） |
    | 解压密码 | …（可选） |
    """
    parts = []
    image = wp_accelerate(image_url)
    if image:
        parts.append("![%s](%s)" % (title, image))
    parts.append("| 字段 | 内容 |")
    parts.append("|---|---|")
    rows = [
        ("影片名称", movie),
        ("出演女优", actors),
        ("字幕行数", subtitle_lines),
        ("匹配时长", duration),
    ]
    if (resource or "").strip():
        rows.append(("匹配资源", resource))
    if (password or "").strip():
        rows.append(("解压密码", password))
    for field, value in rows:
        parts.append("| %s | %s |" % (field, _cell(value)))
    return "\n".join(parts)


def _quote_block(text):
    """短剧简介（单行）-> markdown 引用行列表；空白时返回空列表。

    输入框已强制单行；这里再把换行 / 制表符折叠为空格（防御程序调用方
    直接传多行文本），保证导出永远是一行「> …」。
    """
    text = _FOLD_BREAKS.sub(" ", text or "").strip()
    return ["> " + text] if text else []


def build_drama_markdown(title, image_url, intro, download_text):
    """短剧页内容：图片行（可选，?w=560）+ 短剧简介引用行（可选，单行）
    + 下载链接代码块。

    引用行位于图片下方、下载链接上方；简介留空时整个引用行省略。
    """
    parts = []
    image = wp_accelerate(image_url)
    if image:
        parts.append("![%s](%s)" % (title, _append_width(image, DRAMA_IMAGE_WIDTH)))
    parts.extend(_quote_block(intro))
    text = (download_text or "").strip()
    fence = "```"
    while fence in text:
        fence += "`"
    parts.append(fence)
    parts.append(text)
    parts.append(fence)
    return "\n".join(parts)
