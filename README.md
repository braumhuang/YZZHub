# YZZ Hub

YZZ Hub 是一个基于 Python 3 与 PyQt5 的桌面工具，用于把「字幕」与「短剧」帖子信息
整理成可直接复制发布的 markdown（标题 + 内容），并内置 freeimage / imgbb 双图床上传
（默认 freeimage，免注册开箱即用）与 i3.wp.com 链接加速。

## 1. 功能概览

### 窗口结构

| 区域 | 内容 |
|---|---|
| 页头左上 | 「论坛」按钮：系统默认浏览器打开 `https://bbs.yzz.me` |
| 页头中间 | 「字幕」「短剧」选项卡，默认选中「字幕」 |
| 页头右上 | 「设置」按钮：进入设置页选择图床方案（默认 freeimage）并维护 API 密钥 |
| 页面栈 | 字幕页 / 短剧页 / 设置页三个内容页 |
| 底部 | 状态栏提示当前操作结果 |

### 表单页（字幕 / 短剧）

- **布局**：字段自上而下纵向排列，字段名在输入框上方，必填字段带红色 * 标识；
- **滚动**：窗口高度不足时自动出现竖向滚动条；
- **清除**：右下角「清除」一键清空当前页全部输入；
- **生成**：校验必填项后弹出结果对话框，「标题」「内容」两个只读框各带一键复制；
- **边距与控件规格**：全部界面统一（见第 2 节设计规范）。

### 字幕页字段

| 字段 | 必填 | 说明 |
|---|---|---|
| 帖子标题 | * | 最少 3 个字符，作为导出标题 |
| 帖子图片 | | 上传 / 手输 URL 均可，留空时省略图片行 |
| 影片名称 | * | 如 Midnight Runway |
| 出演女优 | * | 中文名、女优名，如 张三、John Doe |
| 字幕行数 | * | 多条字幕直接填 `263 + 137` |
| 匹配时长 | * | 多条字幕直接填 `00:45:59 + 00:38:33` |
| 匹配资源 | | magnet 或 ed2k 链接，留空时整行省略 |
| 解压密码 | | 附件解压密码，留空时整行省略 |

### 短剧页字段

| 字段 | 必填 | 说明 |
|---|---|---|
| 帖子标题 | * | 最少 3 个字符，作为导出标题 |
| 帖子图片 | | 留空时省略图片行 |
| 下载链接 | * | 多行文本，网盘链接、提取码等整段放入代码块 |

### 设置页（图床方案与 API 密钥）

设置页自上而下两个分组（freeimage 在 imgbb 上方），每组一个单选按钮 +
一个 API 密钥输入框，选中哪个组的单选按钮就把哪个图床设为当前方案：

| 分组 | 说明 |
|---|---|
| freeimage 图床上传（默认） | 默认方案，免注册、开箱即用；已内置官网公开的公共密钥 `6d207e02198a847aa98d0a2a901485a5`，一般无需改动 |
| imgbb 图床上传 | 备选方案，需在 `https://api.imgbb.com/` 免费注册获取密钥 |

保存空密钥即清空已存密钥（freeimage 空值自动回填内置公共密钥，即恢复默认）；
「返回」时如有改动会先自动保存。

### 帖子图片（两页共用同一个控件）

- 可直接手动输入图片 URL，也可点击「上传」选择本地图片上传到当前设置的图床
  （默认 freeimage，返回直链形如 `https://iili.io/xxx.png`；备选 imgbb），
  成功后把原始 URL 写入输入框；
- 输入框始终保存图片原始 URL（手输 / 上传回填 / 历史选取均如此），
  i3.wp.com 加速只在生成时统一附加；
- 点击「上传」先检查当前图床的 API 密钥：freeimage 内置公共密钥永不为空，
  实际只有「选了 imgbb 但未填密钥」才会直接跳转设置页（不弹任何对话框），
  保存密钥返回后自动继续本次上传；
- 「历史」弹层右缘与「历史」按钮右缘对齐，显示最近 20 条上传记录
  （图片名 + 原始 URL），点击条目填入输入框，条目右侧「删除」可移除
  该记录；
- 图片链接统一使用 `https://i3.wp.com/` 加速，已加速的不会重复包装，`http://`
  同时升级为 `https://`。

## 2. 界面设计规范

全部尺寸、间距与颜色集中定义在 `yzzhub/theme.py`（设计令牌），
全局样式表也由该模块唯一提供，各界面模块只引用常量组装布局：

| 令牌 | 取值 | 用途 |
|---|---|---|
| `PAGE_MARGINS` | (18, 14, 18, 10) | 页面四周留白（左/上/右/下） |
| `FORM_MARGINS` | (16, 6, 16, 14) | 分组框内部留白 |
| `INPUT_HEIGHT` | 34 | 所有单行输入框与行内按钮（上传 / 历史 / 复制） |
| `BUTTON_HEIGHT` | 32 | 普通按钮（返回 / 关闭） |
| `ACTION_HEIGHT` | 38 | 动作按钮（清除 / 生成 / 保存） |
| `FORM_ROW_SPACING` | 12 | 表单相邻字段组的间距 |
| `LABEL_GAP` | 3 | 字段名与其输入控件的间距 |
| `SECTION_SPACING` | 10 | 页面大区块间距 |
| `COLOR_PRIMARY` | #1c5fb0 | 选项卡高亮与输入框聚焦边框 |
| `COLOR_SUCCESS` | #2e7d32 | 「生成」「保存」绿色主按钮 |
| `COLOR_DANGER` | #c62828 | 必填星号与删除入口 |

修改界面外观时只调整 `theme.py` 中的令牌与样式表，各页面自动统一生效；
`theme.py` 还提供 `build_form` / `make_scroll_area` / `make_bottom_bar` /
`layout_page` 等组装函数，新页面按「输入控件 → 表单卡片 → 滚动区 → 底部
动作条 → 外层布局」的顺序调用即可获得与现有页面一致的观感。

## 3. 导出格式

字幕页（帖子图片留空时省略首行；匹配资源 / 解压密码留空时省略对应表格行）：

```markdown
![帖子标题](https://i3.wp.com/媒体图床/图片.jpg)
| 字段 | 内容 |
|---|---|
| 影片名称 | Midnight Runway |
| 出演女优 | 张三、John Doe |
| 字幕行数 | 263 + 137 |
| 匹配时长 | 00:45:59 + 00:38:33 |
| 匹配资源 | magnet:?xt=urn:btih:… |
| 解压密码 | yzz |
```

短剧页（图片统一附加 `?w=560` 宽度参数；链接文本本身含 ``` 时自动加长围栏）：

```markdown
![帖子标题](https://i3.wp.com/媒体图床/图片.jpg?w=560)
```
下载链接内容（可多行）
```
```

## 4. 运行环境

| 项目 | 要求 |
|---|---|
| Python | 3.8.5 或以后 |
| PyQt5 | 5.15.11 |
| certifi | 2024.8.30（HTTPS 根证书，兼容 Win7 旧证书库） |
| Windows | Windows 7 SP1 及以后；兼容 Win7 请用 Python 3.8.x 构建 |
| macOS | macOS 11 及以后；Intel 与 Apple Silicon 分别构建原生版本 |

Windows 7 使用 Python 3.8.x 的构建路径（PyInstaller 4.10）；Python 3.9 及以后
不支持 Windows 7，只用于面向 Windows 8.1+ 的构建。上传依赖仅 `PyQt5 + certifi`
两个包，网络请求用标准库 `urllib` 实现，不引入 `requests`。

打包产物内的 VC++ 运行库（`msvcp140*.dll` / `vcruntime140*.dll`）由
`YZZ Hub.spec` 统一锁定为 PyQt5 轮子自带的 14.26 系列（仅依赖经典 UCRT
符号），因此无论在哪台机器上打包——本地 Win7 还是 GitHub Actions 这类
装着最新运行库的新系统——EXE 都能在 Win7 SP1 的老 Universal CRT 上运行。

## 5. 源码运行

首次运行前在项目根目录创建虚拟环境并安装依赖。构建脚本会优先使用项目目录下的
`.venv`，其次 `venv`，两者都不存在时才使用系统 Python。

**Windows 7：** 建议安装 64 位 Python 3.8.x，在项目根目录打开 CMD：

```bat
py -3.8 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade "pip<25"
python -m pip install -r requirements.txt
python main.py
```

**Windows 8.1 及以后：** 将 `py -3.8` 替换为本机 Python 启动器版本（如
`py -3.11`），其余命令相同。

**macOS：** 在项目根目录打开终端，使用当前 Mac 原生架构的 Python：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

退出虚拟环境用 `deactivate`。运行期间终端需保持打开，关闭程序窗口即结束应用。

## 6. 使用说明

1. 默认开箱即用：上传功能默认走 freeimage 图床（免注册，内置公共密钥），
   无需任何配置。如需改用 imgbb，点击右上角「设置」，选中 imgbb 分组的
   单选按钮并粘贴 API 密钥（在 <https://api.imgbb.com/> 免费注册即可获得）。
2. 在「字幕」或「短剧」页填写信息：帖子图片可留空，点击「上传」自动选图上传，
   成功后原始 URL 自动填入（也可直接手输 URL；i3.wp.com 加速在生成时统一附加）。
   选了 imgbb 且未填密钥时点「上传」会直接跳到设置页，保存后自动回表单继续。
3. 点击右下角「生成」，在结果对话框分别复制「标题」与「内容」；
   「清除」可一键清空当前页全部输入，重新填写。

## 7. 配置文件

设置与上传历史保存在 `~/.yzzhub/config.json`
（Windows 即 `C:\Users\<用户>\.yzzhub\config.json`）：

| 键 | 内容 |
|---|---|
| `upload_provider` | 图床方案：`freeimage`（默认）/ `imgbb` |
| `freeimage_api_key` | freeimage 密钥（默认内置公共密钥；空值自动回填） |
| `imgbb_api_key` | imgbb API 密钥（保存空值即清空） |
| `upload_history` | 上传历史，最新在前，最多 20 条，每条含 `name` 与 `url` |

删除该文件即恢复初始状态（重新默认 freeimage）。旧版 v1.0.x 配置文件只含
`imgbb_api_key` 与 `upload_history`，升级后自动兼容：imgbb 密钥与历史保留，
图床切到默认 freeimage。

## 8. 版本号与本地打包

### 修改版本号

项目版本的唯一维护入口是 `yzzhub/__init__.py` 的 `APP_VERSION`
（格式 `主版本.次版本.修订版本`，如 `1.0.1`）。发布新版本时修改该值后执行：

```bash
python tools/sync_version.py 1.0.1
```

脚本把版本同步到 `version_info.txt` 的 `filevers`、`prodvers`、`FileVersion`、
`ProductVersion`；macOS 打包脚本会把同一版本写入 `.app` 的 `Info.plist`。
两个本地打包脚本在构建前也会自动执行同步，日常只需维护 `APP_VERSION`。

### Windows 本地打包

保证 EXE 可在 Windows 7 SP1 运行，请使用 Python 3.8.x（建议 3.8.10），
且项目 `.venv` 已安装依赖，然后运行 `build_win.bat`，产物为
`dist\YZZ Hub.exe`（单文件 EXE），构建日志写入 `build_win.log`。

构建入口是手写的 `YZZ Hub.spec`：它等价于原来的命令行参数（onefile、
窗口模式、图标、版本资源、assets 打包），并额外把 `msvcp140*.dll` /
`vcruntime140*.dll` 替换为 PyQt5 轮子 `PyQt5\Qt5\bin` 里自带的副本。
PyInstaller 按目录优先级收集依赖时会先命中 `C:\Windows\System32`，
CI Runner 上那是最新版 VC++ 2015-2022 运行库（依赖新版 UCRT 的 `_o_*`
导出），会让 EXE 在老 UCRT 的 Win7 上报
「DLL load failed while importing QtCore: 找不到指定的程序」；锁定为
轮子自带的 14.26 版本后，本地与 CI 产物内容一致，Win7 到 Win11 通吃。

### macOS 本地打包

在目标架构的 Mac 上使用同架构 Python 执行 `bash build_mac.sh`，产物为
`dist/YZZ Hub.app`。Intel Mac 生成 x86_64 App，Apple Silicon Mac 生成
arm64 App；脚本将最低系统版本设为 macOS 11.0 并检查产物架构，随后做
adhoc 签名（公开分发需 Developer ID + 公证）。

本地构建结果位于 `dist/`，PyInstaller 中间文件位于 `build/`，两者均已在
`.gitignore` 中忽略。

## 9. GitHub Actions 自动发布

项目已配置 `.github/workflows/release.yml`：推送符合 `vX.Y.Z` 格式的 Git tag
后自动并行执行三个构建任务，全部成功后创建 GitHub Release 并上传安装包。

```bash
git add .
git commit -m "Prepare YZZ Hub 1.0.1"
git push origin main
git tag -a v1.0.1 -m "YZZ Hub v1.0.1"
git push origin v1.0.1
```

| 构建任务 | Runner | Python / 架构 | 目标平台 |
|---|---|---|---|
| Windows | `windows-2022` | 3.8.10 x64 | Windows 7 SP1 及以后（x64） |
| Mac Intel | `macos-15-intel` | x86_64 | macOS 11 及以后（Intel） |
| Mac Apple Silicon | `macos-15` | arm64 | macOS 11 及以后（Apple Silicon） |

以 `v1.0.1` 为例，Release 附件：

| 文件名 | 内容 | 适用平台 |
|---|---|---|
| `YZZ_Hub_v1.0.1_Win.exe` | 单文件 EXE | Windows 7 SP1 及以后（x64） |
| `YZZ_Hub_v1.0.1_MacIntel.zip` | `YZZ Hub.app` 压缩包 | macOS 11 及以后（Intel） |
| `YZZ_Hub_v1.0.1_MacApple.zip` | `YZZ Hub.app` 压缩包 | macOS 11 及以后（Apple Silicon） |

构建过程与日志在仓库 **Actions** 页面查看；发布需要工作流具备仓库内容写入
权限，当前 workflow 已为发布 job 声明 `contents: write`。

## 10. 更换应用图标

图标唯一图源是 `assets/icon.icns`，更换时执行：

```bash
python -m pip install "Pillow>=9.4"
python tools/install_icon.py /path/to/新图标.icns
```

工具会同时刷新 `assets/icon.icns`（macOS App 图标）、`assets/icon.png`
（512×512 窗口图标）与 `assets/icon.ico`（16~256 多尺寸，Windows exe 图标）。
Pillow 仅是图标工具的开发依赖，不属于运行依赖。

## 11. 项目结构

```text
YZZ-Hub/
├── .github/workflows/release.yml   # GitHub Actions 自动构建与发布
├── assets/                          # 应用图标（icns / ico / png）
├── yzzhub/
│   ├── __init__.py                  # 版本号与全局常量（API 地址等）
│   ├── theme.py                     # 统一设计令牌 + 全局样式表 + 布局组装函数
│   ├── config.py                    # 设置与上传历史（~/.yzzhub/config.json）
│   ├── main_window.py               # 主窗口：页头 / 选项卡 / 页面栈 / 状态栏
│   ├── subtitle_page.py             # 字幕表单页
│   ├── drama_page.py                # 短剧表单页
│   ├── settings_page.py             # 设置页（图床方案选择 + API 密钥）
│   ├── image_field.py               # 帖子图片控件：URL 输入 + 上传 + 历史
│   ├── result_dialog.py             # 生成结果对话框（标题 / 内容复制框）
│   ├── freeimage.py                 # freeimage 上传（默认图床，标准库 urllib）
│   ├── imgbb.py                     # imgbb 上传（备选图床，标准库 urllib）
│   └── markdown.py                  # i3.wp.com 加速与 markdown 模板
├── tools/
│   ├── install_icon.py              # 图标资源转换工具（开发用，需 Pillow）
│   └── sync_version.py              # 同步应用与 Windows 文件版本
├── main.py                          # 程序入口（字体 / 图标 / 高分屏适配）
├── requirements.txt                 # 运行依赖
├── version_info.txt                 # Windows EXE 版本资源
├── YZZ Hub.spec                     # Windows 打包配方（锁定 Win7 兼容 VC++ 运行库）
├── build_win.bat                    # Windows 本地打包脚本
└── build_mac.sh                     # macOS 本地打包脚本
```
