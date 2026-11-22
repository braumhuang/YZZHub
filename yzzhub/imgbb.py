# -*- coding: utf-8 -*-
"""imgbb 图片上传（https://api.imgbb.com/1/upload）。

使用标准库 urllib 以 multipart/form-data 上传本地图片，不引入 requests，
保证 Python 3.8 + Windows 7 路径可用。证书优先使用 certifi 随附的 CA 包，
certifi 不可用时退回系统默认证书。

成功返回 dict：{"url": 直链, "name": 本地文件名, "title": imgbb 标题}；
失败抛 RuntimeError，错误信息面向用户可直接展示。
"""

import json
import os
import ssl
import uuid
import urllib.error
import urllib.request

try:
    import certifi
except ImportError:  # pragma: no cover - requirements.txt 固定安装了 certifi
    certifi = None

from yzzhub import IMGBB_API_URL

# imgbb 单文件上限 32 MB；超限直接本地报错，不发请求。
MAX_BYTES = 32 * 1024 * 1024
TIMEOUT = 60  # 秒；大图弱网下 30s 偏紧，取 60


def _ssl_context():
    if certifi is not None:
        try:
            return ssl.create_default_context(cafile=certifi.where())
        except (OSError, ssl.SSLError):
            pass
    return ssl.create_default_context()


def _multipart(boundary, fields, file_field, file_name, file_bytes):
    """手工拼 multipart/form-data 报文。"""
    out = []
    for name, value in fields:
        out.append(
            ("--%s\r\n"
             "Content-Disposition: form-data; name=\"%s\"\r\n\r\n"
             "%s\r\n" % (boundary, name, value)).encode("utf-8"))
    safe_name = file_name.replace('"', "'").replace("\r", "").replace("\n", "")
    out.append(
        ("--%s\r\n"
         "Content-Disposition: form-data; name=\"%s\"; filename=\"%s\"\r\n"
         "Content-Type: application/octet-stream\r\n\r\n"
         % (boundary, file_field, safe_name)).encode("utf-8"))
    out.append(file_bytes)
    out.append(("\r\n--%s--\r\n" % boundary).encode("utf-8"))
    return b"".join(out)


def _error_message(payload):
    """从 imgbb 的 JSON 错误响应里取用户可读信息。"""
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict) and error.get("message"):
            return str(error["message"])
        if isinstance(error, str) and error:
            return error
        if payload.get("status_message"):
            return str(payload["status_message"])
    return ""


def upload_image(api_key, file_path):
    """上传本地图片，返回 {"url":..., "name":..., "title":...}；失败抛 RuntimeError。"""
    api_key = (api_key or "").strip()
    if not api_key:
        raise RuntimeError("尚未设置 imgbb API 密钥，请先在设置页面填写。")

    path = os.path.abspath(file_path)
    if not os.path.isfile(path):
        raise RuntimeError("图片文件不存在：%s" % path)
    size = os.path.getsize(path)
    if size == 0:
        raise RuntimeError("图片文件为空：%s" % path)
    if size > MAX_BYTES:
        raise RuntimeError(
            "图片过大（%.1f MB），imgbb 单文件上限 32 MB。" % (size / 1024.0 / 1024.0))

    try:
        with open(path, "rb") as f:
            file_bytes = f.read()
    except OSError as e:
        raise RuntimeError("无法读取图片文件：%s" % e)

    file_name = os.path.basename(path)
    display_name = os.path.splitext(file_name)[0] or file_name
    boundary = "----YZZHubBoundary%s" % uuid.uuid4().hex
    body = _multipart(
        boundary,
        [("key", api_key), ("name", display_name)],
        "image", file_name, file_bytes)

    request = urllib.request.Request(
        IMGBB_API_URL, data=body, method="POST",
        headers={
            "Content-Type": "multipart/form-data; boundary=%s" % boundary,
            "User-Agent": "YZZHub/1.0 (+https://bbs.yzz.me)",
        })

    try:
        with urllib.request.urlopen(
                request, timeout=TIMEOUT, context=_ssl_context()) as response:
            raw = response.read()
    except urllib.error.HTTPError as e:
        try:
            raw = e.read()
        except Exception:
            raw = b""
        try:
            message = _error_message(json.loads(raw.decode("utf-8", "replace")))
        except ValueError:
            message = ""
        raise RuntimeError(message or ("imgbb 拒绝了上传（HTTP %s）。" % e.code))
    except urllib.error.URLError as e:
        reason = getattr(e, "reason", e)
        raise RuntimeError("网络连接失败：%s" % reason)
    except ssl.SSLError as e:
        raise RuntimeError("安全连接失败：%s" % e)
    except OSError as e:
        raise RuntimeError("网络或读写错误：%s" % e)

    try:
        payload = json.loads(raw.decode("utf-8", "replace"))
    except ValueError:
        raise RuntimeError("imgbb 返回了无法解析的内容。")

    if not isinstance(payload, dict) or not payload.get("success"):
        raise RuntimeError(_error_message(payload) or "imgbb 返回了失败状态。")

    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    url = (data.get("url") or "").strip()
    if not url:
        raise RuntimeError("imgbb 返回数据中没有图片链接。")
    return {
        "url": url,
        "name": file_name,
        "title": (data.get("title") or "").strip() or display_name,
    }
