# -*- coding: utf-8 -*-
"""YZZ Hub 包：PyQt5 markdown 导出工具（字幕 / 短剧）。"""

# APP_VERSION 是应用版本的唯一维护入口；构建脚本会同步平台版本元数据。
APP_NAME = "YZZ Hub"
APP_VERSION = "1.0.0"

# 「论坛」按钮用系统默认浏览器打开的站点。
HOME_URL = "https://bbs.yzz.me"

# 图床方案标识（config.upload_provider 取这两个值）。
PROVIDER_FREEIMAGE = "freeimage"
PROVIDER_IMGBB = "imgbb"

# 默认图床：freeimage.host 免注册，密钥为官网公开的公共密钥，
# 开箱即用；imgbb 需要用户自行注册。
DEFAULT_UPLOAD_PROVIDER = PROVIDER_FREEIMAGE

# freeimage.host 上传接口与帮助页面。
# 端点必须用 /api/1/upload（无尾斜杠）：带尾斜杠时服务端 301，
# urllib 会把 POST 降级成 GET 导致上传失败。
FREEIMAGE_API_URL = "https://freeimage.host/api/1/upload"
FREEIMAGE_DOC_URL = "https://freeimage.host/api"
# 官网 API 页面公开的公共密钥（https://freeimage.host/api），
# 所有用户共用，直接内置在软件里作为默认值。
FREEIMAGE_DEFAULT_KEY = "6d207e02198a847aa98d0a2a901485a5"

# imgbb 上传接口与帮助页面。
IMGBB_API_URL = "https://api.imgbb.com/1/upload"
IMGBB_DOC_URL = "https://api.imgbb.com/"

# 图片 URL 统一使用的 CDN 加速前缀。
WP_PREFIX = "https://i3.wp.com/"

# 短剧页统一附加的图片宽度参数。
DRAMA_IMAGE_WIDTH = "w=560"

# 上传历史最多保留条数（最新在前）。
HISTORY_LIMIT = 20
