# -*- coding: utf-8 -*-
"""设置与上传历史存取。

数据保存在用户主目录下的 JSON 文件（~/.yzzhub/config.json），
Windows 上即 C:\\Users\\<用户>\\.yzzhub\\config.json，macOS/Linux 上
即 /Users/<用户>/.yzzhub/config.json。文件包含四项内容：

- upload_provider    : 图床方案（"freeimage" 默认 / "imgbb"）；
- freeimage_api_key  : freeimage 密钥，默认为官网公开的公共密钥
                        （6d207e02198a847aa98d0a2a901485a5，免注册）；
- imgbb_api_key      : imgbb API 密钥（设置页面维护）；
- upload_history      : 最近上传记录（最新在最前，上限 HISTORY_LIMIT 条），
                        每条记录 {name, url, time}，url 为图床原始直链。

写入采用「临时文件 + 替换」的原子方式，避免写入中途退出产生半截 JSON。
"""

import json
import os
import threading
import time

from yzzhub import (
    FREEIMAGE_DEFAULT_KEY, HISTORY_LIMIT,
    PROVIDER_FREEIMAGE, PROVIDER_IMGBB, DEFAULT_UPLOAD_PROVIDER,
)

CONFIG_DIR_NAME = ".yzzhub"
CONFIG_FILE_NAME = "config.json"

# 上传在 QThread 里写历史、界面在主线程读写设置，用一把锁串行化磁盘操作。
_LOCK = threading.RLock()

DEFAULTS = {
    "upload_provider": DEFAULT_UPLOAD_PROVIDER,
    "freeimage_api_key": FREEIMAGE_DEFAULT_KEY,
    "imgbb_api_key": "",
    "upload_history": [],
}


def config_dir():
    """配置目录（用户主目录下的 .yzzhub）。"""
    return os.path.join(os.path.expanduser("~"), CONFIG_DIR_NAME)


def config_path():
    """配置文件完整路径。"""
    return os.path.join(config_dir(), CONFIG_FILE_NAME)


def _normalize(data):
    """校验并规范外部 JSON，防止手改文件造成运行期崩溃。

    兼容旧版（v1.0.x 只存 imgbb_api_key 与 upload_history）：缺
    upload_provider 时回退默认 freeimage；freeimage 密钥为空时回填
    内置公共密钥（免注册方案，空值视为未配置）。
    """
    if not isinstance(data, dict):
        return dict(DEFAULTS)
    result = dict(DEFAULTS)
    provider = data.get("upload_provider", DEFAULT_UPLOAD_PROVIDER)
    if provider not in (PROVIDER_FREEIMAGE, PROVIDER_IMGBB):
        provider = DEFAULT_UPLOAD_PROVIDER
    result["upload_provider"] = provider
    fi_key = data.get("freeimage_api_key", FREEIMAGE_DEFAULT_KEY)
    if isinstance(fi_key, str) and fi_key.strip():
        result["freeimage_api_key"] = fi_key.strip()
    key = data.get("imgbb_api_key", "")
    result["imgbb_api_key"] = key.strip() if isinstance(key, str) else ""
    history = data.get("upload_history", [])
    if isinstance(history, list):
        clean = []
        for item in history:
            if not isinstance(item, dict):
                continue
            url = item.get("url", "")
            name = item.get("name", "")
            if isinstance(url, str) and url:
                clean.append({
                    "url": url,
                    "name": name if isinstance(name, str) and name else url,
                    "time": item.get("time", ""),
                })
        result["upload_history"] = clean
    return result


def load():
    """读取配置（文件不存在或损坏时返回默认值，不抛异常）。"""
    with _LOCK:
        path = config_path()
        if not os.path.isfile(path):
            return dict(DEFAULTS)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return _normalize(json.load(f))
        except (OSError, ValueError):
            return dict(DEFAULTS)


def save(data):
    """原子写入整个配置。"""
    with _LOCK:
        path = config_path()
        os.makedirs(config_dir(), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)


def get_provider():
    """当前图床方案："freeimage"（默认）或 "imgbb"。"""
    return load()["upload_provider"]


def set_provider(provider):
    """保存图床方案；仅接受 freeimage / imgbb，非法值回退默认 freeimage。"""
    provider = (provider or "").strip()
    if provider not in (PROVIDER_FREEIMAGE, PROVIDER_IMGBB):
        provider = DEFAULT_UPLOAD_PROVIDER
    with _LOCK:
        data = load()
        data["upload_provider"] = provider
        save(data)
        return data["upload_provider"]


def get_freeimage_key():
    """当前保存的 freeimage 密钥（空值已回填内置公共密钥，不会为空）。"""
    return load()["freeimage_api_key"]


def set_freeimage_key(key):
    """保存 freeimage 密钥；空值回填内置公共密钥（即恢复默认）。"""
    value = (key or "").strip() or FREEIMAGE_DEFAULT_KEY
    with _LOCK:
        data = load()
        data["freeimage_api_key"] = value
        save(data)
        return data["freeimage_api_key"]


def get_api_key():
    """当前保存的 imgbb API 密钥（未设置为空字符串）。"""
    return load()["imgbb_api_key"]


def set_api_key(key):
    """保存 imgbb API 密钥；空字符串表示清除。"""
    with _LOCK:
        data = load()
        data["imgbb_api_key"] = (key or "").strip()
        save(data)
        return data["imgbb_api_key"]


def get_active_api_key():
    """按当前图床方案返回生效密钥（freeimage 用公共密钥，imgbb 用用户密钥）。"""
    data = load()
    if data["upload_provider"] == PROVIDER_IMGBB:
        return data["imgbb_api_key"]
    return data["freeimage_api_key"]


def get_history():
    """上传历史列表（最新在前）：[{"name":..., "url":..., "time":...}]。"""
    return load()["upload_history"]


def add_history(name, url):
    """记录一次上传：插入最前；相同 URL 的旧记录移到最前并更新名称；超出上限裁剪。"""
    with _LOCK:
        data = load()
        history = [h for h in data["upload_history"] if h["url"] != url]
        history.insert(0, {
            "url": url,
            "name": (name or "").strip() or url,
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        })
        data["upload_history"] = history[:HISTORY_LIMIT]
        save(data)
        return data["upload_history"]


def remove_history(url):
    """删除一条与 url 匹配的上传记录。"""
    with _LOCK:
        data = load()
        data["upload_history"] = [h for h in data["upload_history"]
                                  if h["url"] != url]
        save(data)
        return data["upload_history"]
