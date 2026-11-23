# -*- coding: utf-8 -*-
"""markdown 结果构建。

- wp_accelerate：把任意图片 URL 包装成 https://i3.wp.com/ 加速链接；
  已是 i3.wp.com 的直接返回（不重复包装），http:// 的同时升级为 https。
- to_half_width：全角（中文输入法）字符转半角，匹配时长输入框即时调用。
- format_resource_links / _resource_cell：匹配资源生成时格式化——
  magnet 转最简可用形式 magnet:?xt=urn:btih:大写哈希（保留 magnet
  前缀，复制即可下载）；ed2k 转最简可用形式
  ed2k://|file|文件名|size|大写哈希|/（去掉 h= 等尾部字段、补上结尾
  |/），在表格单元格内整体包上反引号（反引号内的竖线原样保留，
  不按表格规则转义）。v1.2.0 旧最简形式 文件名|size|大写哈希
  自动升级为完整 ed2k 链接。
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

# ---------------- 匹配资源链接识别 ----------------
# magnet 链接整条（到空白为止）：magnet:?xt=urn:btih:哈希&dn=…&tr=…。
# 哈希字符集兼容十六进制（40 位）与 base32（32 位）两种 v1 形式。
_MAGNET_URI_RE = re.compile(r"magnet:\?\S+", re.IGNORECASE)
_MAGNET_HASH_RE = re.compile(r"xt=urn:btih:([0-9A-Za-z]+)", re.IGNORECASE)

# ed2k 文件链接：ed2k://|file|文件名|size|哈希|（尾部可有 h=… 等字段）。
# 文件名可含空格但不能含竖线；size 为字节数；哈希为 32 位十六进制（MD4）。
_ED2K_URI_RE = re.compile(
    r"ed2k://\|file\|([^|\r\n\t]+)\|(\d+)\|([0-9A-Fa-f]{32})(?:\|[^\s]*)?",
    re.IGNORECASE)

# v1.2.0 旧最简形式：文件名|size|哈希（升级为完整链接用，带分组）。
# 文件名部分不含问号——magnet 链接里必有 "?"，避免整段匹配把
# 同框的 magnet 链接误当成 ed2k 文件名的一部分。
_ED2K_SIMPLE_RE = re.compile(r"([^|\r\n\t?]+)\|(\d+)\|([0-9A-Fa-f]{32})")

# 格式化后的完整 ed2k 链接：ed2k://|file|文件名|size|大写哈希|/
# （_resource_cell 按此整体识别并包反引号；文件名可含空格，不能按
# 空白逐词拆分，只能整体匹配；格式化已保证哈希大写）。
_ED2K_FULL_RE = re.compile(r"ed2k://\|file\|[^|\r\n]+\|\d+\|[0-9A-F]{32}\|/")


def to_half_width(text):
    """全角（中文输入法）字符转半角；非全角字符原样保留。

    全角空格（U+3000）转普通空格；全角 ASCII 区 U+FF01..U+FF5E
    （含 ：＋０-９ 等）平移到对应半角字符。转换严格一一对应，文本
    长度不变，输入框里转换后光标位置不受影响。
    """
    chars = []
    for ch in text or "":
        code = ord(ch)
        if code == 0x3000:
            chars.append(" ")
        elif 0xFF01 <= code <= 0xFF5E:
            chars.append(chr(code - 0xFEE0))
        else:
            chars.append(ch)
    return "".join(chars)


def _build_ed2k_uri(name, size, digest):
    """ed2k 三要素 -> 最简可用链接 ed2k://|file|文件名|size|大写哈希|/。"""
    return "ed2k://|file|%s|%s|%s|/" % (name, size, digest.upper())


def _format_ed2k_uri(match):
    """单条 ed2k 链接 -> 最简可用形式；尾部 h=… 等字段全部丢弃。"""
    return _build_ed2k_uri(match.group(1), match.group(2), match.group(3))


def _format_magnet_uri(match):
    """单条 magnet 链接 -> 最简可用形式 magnet:?xt=urn:btih:大写哈希。

    保留 magnet 前缀与 xt 参数，复制即可直接下载；无 btih 哈希时
    原样返回。
    """
    hash_match = _MAGNET_HASH_RE.search(match.group(0))
    if hash_match is None:
        return match.group(0)
    return "magnet:?xt=urn:btih:" + hash_match.group(1).upper()


def _strip_code_ticks(token):
    """去掉 v1.2.0 导出内容外层包裹的一对反引号（如有）。"""
    if len(token) >= 2 and token.startswith("`") and token.endswith("`"):
        return token[1:-1]
    return token


def _upgrade_old_simple_forms(value):
    """v1.2.0 旧最简形式 文件名|size|哈希 升级为完整 ed2k 链接。

    覆盖旧导出内容重贴回来的三种情形：裸的最简形式、整体包着反引
    号的最简形式、逐词混在其他内容里的最简形式。整段匹配优先（文
    件名可含空格）；无任何升级时原样返回。调用方已保证文本中没有
    完整 ed2k 链接（有则跳过升级），不会误拆链接内部结构。
    """
    stripped = value.strip()
    if not stripped:
        return value
    whole = _ED2K_SIMPLE_RE.fullmatch(_strip_code_ticks(stripped))
    if whole is not None:
        return _build_ed2k_uri(whole.group(1), whole.group(2), whole.group(3))
    tokens = stripped.split()
    upgraded = False
    for i, token in enumerate(tokens):
        match = _ED2K_SIMPLE_RE.fullmatch(_strip_code_ticks(token))
        if match is not None:
            tokens[i] = _build_ed2k_uri(
                match.group(1), match.group(2), match.group(3))
            upgraded = True
    return " ".join(tokens) if upgraded else value


def format_resource_links(text):
    """文本里的 magnet / ed2k 链接就地格式化，其余内容原样保留。

    - magnet:?xt=urn:btih:哈希&dn=…&tr=… -> magnet:?xt=urn:btih:大写哈希
      （保留 magnet 前缀与 xt 参数，复制即可下载；dn / tr 等其余参数
      全部丢弃）；
    - ed2k://|file|文件名|size|哈希|… -> ed2k://|file|文件名|size|大写哈希|/
      （去掉 h= 等尾部字段、补上结尾 |/，复制即可直接下载）；
    - v1.2.0 旧最简形式 文件名|size|哈希 升级为完整 ed2k 链接；
    - 文本里有多条链接时逐一替换；找不到 btih 哈希的 magnet、
      server 型 ed2k 等不成形链接原样保留。
    """
    value = text or ""
    # 旧最简形式升级仅在没有完整 ed2k 链接时进行：完整链接的内部
    # 结构（协议头、含空格的文件名）与旧形式无法区分，混在一起时
    # 不升级、原样保留。
    if "ed2k://" not in value.lower():
        value = _upgrade_old_simple_forms(value)
    # ed2k（结构更具体）先于 magnet 替换，避免 magnet 的整段匹配吞掉
    # 紧跟其后、中间无空白的 ed2k 链接。
    value = _ED2K_URI_RE.sub(_format_ed2k_uri, value)
    value = _MAGNET_URI_RE.sub(_format_magnet_uri, value)
    return value


def _resource_cell(resource):
    """匹配资源单元格：生成时格式化 magnet / ed2k。

    magnet 为 magnet:?xt=urn:btih:大写哈希（不含竖线，按普通单元格
    处理）；ed2k 为完整可用形式 ed2k://|file|文件名|size|大写哈希|/，
    整体包上反引号——反引号内的竖线原样保留，不再按表格规则转义
    （这正是添加反引号的目的）。文件名可含空格，因此按完整链接
    整体匹配而非按空白逐词拆分；混合内容（magnet + ed2k、多条
    ed2k）分段处理，链接之外的文本仍走 _cell 普通转义。
    """
    text = " ".join(format_resource_links(resource or "").split())
    if not text:
        return ""
    pieces = []
    pos = 0
    for match in _ED2K_FULL_RE.finditer(text):
        if match.start() > pos:
            gap = text[pos:match.start()]
            if gap.strip():
                pieces.append(_cell(gap))
        pieces.append("`%s`" % match.group(0))
        pos = match.end()
    if pos == 0:
        # 没有任何 ed2k（纯文本 / magnet）：按普通单元格转义。
        return _cell(text)
    if pos < len(text):
        tail = text[pos:]
        if tail.strip():
            pieces.append(_cell(tail))
    return " ".join(pieces)


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
    | 匹配时长 | …（形如 00:45:59 + 00:38:33；输入框已即时转半角，
      这里再兜底转一次，任何调用路径都是半角） |
    | 匹配资源 | …（可选；magnet 为 magnet:?xt=urn:btih:大写哈希，
      ed2k 为 `ed2k://|file|文件名|size|大写哈希|/`（整体包反引号）） |
    | 解压密码 | …（可选） |
    """
    parts = []
    image = wp_accelerate(image_url)
    if image:
        parts.append("![%s](%s)" % (title, image))
    parts.append("| 字段 | 内容 |")
    parts.append("|---|---|")
    rows = [
        ("影片名称", _cell(movie)),
        ("出演女优", _cell(actors)),
        ("字幕行数", _cell(subtitle_lines)),
        # 匹配时长：输入框已即时转半角，导出时再兜底转一次，
        # 保证任何调用路径下发出去的都是半角冒号 / 加号 / 数字。
        ("匹配时长", _cell(to_half_width(duration))),
    ]
    # 匹配资源行：单元格已含反引号包裹的完整 ed2k 链接，成品单元格
    # 直接使用，不再经过 _cell（那样会把反引号内的竖线转义掉）。
    resource_cell = _resource_cell(resource)
    if resource_cell:
        rows.append(("匹配资源", resource_cell))
    if (password or "").strip():
        rows.append(("解压密码", _cell(password)))
    for field, value in rows:
        parts.append("| %s | %s |" % (field, value))
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
