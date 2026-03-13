skill---
name: skill-content-crawler
description: |
  多平台爆款内容拆解器。支持小红书、抖音、B 站三个平台的爆款内容采集与分析。
  可以单独爬取某个平台，也可以多平台同时采集并生成跨平台对比报告。
  功能包括：关键词搜索、多关键词拓展、按标题去重、按点赞排序取 Top N、
  视频下载转录（Whisper/字幕提取）、图文正文提取、高赞评论抓取、爆款分析报告生成。
  当用户提到"爆款分析"、"内容拆解"、"抖音爬虫"、"B站爬虫"、"小红书爬虫"、
  "多平台分析"、"全网爆款"、"跨平台对比"、"视频转录"、"评论抓取"时使用。
  即使用户只说"分析某个关键词的爆款"也应触发此 skill。
---

# 多平台爆款内容拆解器

## Overview

支持**小红书、抖音、B 站**三个平台的爆款内容采集与分析。用户可以选择单平台或多平台同时采集。

| 平台 | Cookie 要求 | 技术栈 | 内容类型 |
|------|-----------|--------|----------|
| 📕 小红书 | **必须** | Selenium + Cookie 注入 | 图文 + 短视频 |
| 🎵 抖音 | **必须** | undetected_chromedriver + Cookie | 短视频 |
| 📺 B 站 | **必须**（字幕/评论） | 公开 API + Cookie | 中长视频 |

> **Cookie 获取方式**：当检测到对应平台 Cookie 缺失时，脚本会**自动打开浏览器**让用户登录：
> - 自动弹出 Chrome 浏览器，打开对应平台的登录页面
> - 用户在浏览器中完成登录（支持扫码、账号密码等方式）
> - 登录成功后，脚本自动提取 Cookie 并缓存到**当前脚本目录下的 `.cookie_cache` 文件夹**
> - 下次运行时自动使用缓存的 Cookie，无需重复登录
> - 如果已有 Cookie（配置区填入或缓存），则直接使用，不会弹出浏览器
>
> **Cookie 存储位置**：`scripts/<platform>/.cookie_cache/`（相对路径，位于工作区内）

## Cookie 处理规则（极其重要 — AI 必须严格遵守）

### 第一步：运行前先检查 Cookie 缓存状态

**在运行任何平台的采集脚本之前**，AI 必须先检查该平台的 Cookie 缓存文件是否存在：

| 平台 | Cookie 缓存文件路径（相对于 `$SKILL_DIR`） |
|------|------------------------------------------|
| B 站 | `scripts/bilibili/.cookie_cache/bili_cookies.json` |
| 抖音 | `scripts/douyin/.cookie_cache/douyin_cookies.json` |
| 小红书 | `scripts/xiaohongshu/.cookie_cache/xhs_cookies.json` |

**检查方法**：使用 `read_file` 或 `list_directory` 检查对应的 `.cookie_cache` 目录下是否有缓存文件。

### 第二步：根据检查结果决定下一步

**情况 A：Cookie 缓存存在** → 直接运行脚本，无需询问用户。

**情况 B：Cookie 缓存不存在** → **不要直接运行脚本**，而是先告知用户并询问：

> 示例话术：
> "检测到 **抖音** 和 **小红书** 还没有登录过（没有 Cookie 缓存）。运行这两个平台的脚本时，会自动弹出 Chrome 浏览器让你扫码登录。登录成功后 Cookie 会自动缓存，后续无需重复登录。
>
> 是否现在继续？（会弹出浏览器让你登录）"

**用户确认后**，再运行脚本。脚本会自动弹出浏览器让用户登录。

### 第三步：运行脚本并等待

1. **先安装依赖**：运行 `pip install undetected-chromedriver`（如果尚未安装）
2. **运行脚本**：设置足够长的超时时间 `wait=true, max_wait_seconds=55`，因为用户需要时间在浏览器中完成登录
3. **如果超时**：使用 `read-process` 读取输出，检查是否仍在等待用户登录，如果是则继续等待
4. **绝对不要放弃**：无论遇到什么错误，都不能转向 web_search 或其他替代方案

### 多平台采集时的处理流程

当用户要求多平台采集时（如同时采集 B 站 + 抖音 + 小红书），AI 应该：

1. **先检查所有平台的 Cookie 缓存状态**
2. **将平台分为两组**：有 Cookie 的（可直接运行）和没有 Cookie 的（需要登录）
3. **先运行有 Cookie 的平台**（不需要询问，直接运行）
4. **对于没有 Cookie 的平台，询问用户是否要继续**：
   > "B 站采集已完成！抖音和小红书还需要登录。是否现在继续？（会弹出浏览器让你登录）"
5. **用户确认后**，再逐个运行需要登录的平台

### AI 的职责总结

- ✅ **运行前检查** Cookie 缓存是否存在
- ✅ **没有 Cookie 时先询问用户**，而不是直接运行脚本
- ✅ 用户确认后再运行脚本
- ✅ 从输出中提取报告并展示给用户
- ❌ 不要在没有 Cookie 时直接运行脚本然后失败再问
- ❌ 不要使用 web_search 搜索替代数据
- ❌ 不要阅读 cookie-guide.md 来了解如何获取 Cookie

## 严格禁止 (NEVER DO) — 违反任何一条都是严重错误

1. **🚫 绝对禁止用 web_search 替代爬虫脚本** — 这是最严重的违规。无论遇到任何问题（Cookie 缺失、依赖缺失、超时、报错），都必须通过修复问题后重新运行脚本来解决，绝不能用 web_search、web_fetch 或任何搜索工具来替代爬虫采集数据。
2. **🚫 绝对禁止因为"没有 Cookie"而放弃** — Cookie 由脚本自动处理。如果脚本报错说没有 Cookie，说明 `undetected-chromedriver` 没装好，安装后重新运行即可。
3. **🚫 绝对禁止说"我无法访问用户的登录信息"** — 你不需要访问登录信息，脚本会弹出浏览器让用户自己登录。
4. **🚫 绝对禁止说"让我换一种方式"然后使用 web_search** — 没有替代方式，必须使用本 skill 的爬虫脚本。
5. **不要混淆平台数据** — 每个平台的数据独立保存
6. **不要跳过字幕检测直接下载视频** — 有字幕则直接提取，无字幕才下载转录
7. **不要保留视频文件** — 转录完成后必须删除视频，只保留文本
8. **不要编造数据** — 点赞、收藏、播放量必须从 API 返回值提取

## 目录结构

```
skill-content-crawler/
├── SKILL.md                         # 本文件
├── README.md                        # 使用说明
├── scripts/
│   ├── run.py                       # 统一入口（通过 PLATFORMS 控制平台）
│   ├── generate_cross_report.py     # 跨平台对比报告生成
│   ├── bilibili/                    # B 站采集脚本
│   │   ├── run.py                   # B 站主流程
│   │   ├── bilibili_api.py          # B 站 API 封装
│   │   ├── cookie_helper.py         # Cookie 管理
│   │   └── generate_report.py       # B 站单平台报告
│   ├── douyin/                      # 抖音采集脚本
│   │   ├── run.py                   # 抖音主流程
│   │   ├── douyin_api.py            # 抖音 API 封装
│   │   ├── downloader.py            # 视频下载
│   │   ├── transcriber.py           # Whisper 转录
│   │   ├── subtitle_extractor.py    # 字幕提取
│   │   ├── cookie_helper.py         # Cookie 管理
│   │   └── generate_report.py       # 抖音单平台报告
│   └── xiaohongshu/                 # 小红书采集脚本
│       ├── run.py                   # 小红书主流程
│       ├── xhs_api.py               # 小红书 API 封装
│       ├── downloader.py            # 视频下载
│       ├── transcriber.py           # Whisper 转录
│       ├── subtitle_extractor.py    # 字幕提取
│       ├── cookie_helper.py         # Cookie 管理
│       └── generate_report.py       # 小红书单平台报告
└── references/
    ├── cookie-guide.md              # Cookie 获取指南
    └── dependencies.md              # 依赖安装说明
```

## 环境准备

```bash
# Python 依赖
pip install selenium undetected-chromedriver demucs openai-whisper torch torchaudio soundfile scipy

# 系统依赖
# ffmpeg: Windows: choco install ffmpeg | macOS: brew install ffmpeg
# Chrome 浏览器: 抖音和小红书必须
```

## 核心工作流

### 使用方式 1：多平台同时采集

```python
# 修改 $SKILL_DIR/scripts/run.py 配置区

# 选择平台（全部三个）
PLATFORMS = ["bilibili", "douyin", "xiaohongshu"]

# 关键词列表
KEYWORDS = ["openclaw", "openclaw教程", "openclaw测评", "openclaw怎么用", "openclaw开源"]

# 每平台保留数量
MAX_ITEMS = 10
MAX_COMMENTS = 30

# 执行
# cd "$SKILL_DIR/scripts" && python run.py
```

### 使用方式 2：单平台采集

```python
# 只爬 B 站
PLATFORMS = ["bilibili"]

# 只爬抖音
PLATFORMS = ["douyin"]

# 只爬小红书
PLATFORMS = ["xiaohongshu"]
```

### 使用方式 3：直接运行单平台脚本

```bash
# 直接运行 B 站脚本（使用脚本内配置区）
cd "$SKILL_DIR/scripts/bilibili" && python run.py

# 直接运行抖音脚本
cd "$SKILL_DIR/scripts/douyin" && python run.py

# 直接运行小红书脚本
cd "$SKILL_DIR/scripts/xiaohongshu" && python run.py
```

## 报告展示（重要）

脚本运行完成后，报告内容会**自动打印到控制台输出中**（在 `📋 以下是完整的分析报告内容：` 和 `📋 报告内容结束` 之间）。

**AI 必须执行以下步骤：**

1. 脚本运行结束后，从控制台输出中提取 `📋 以下是完整的分析报告内容：` 到 `📋 报告内容结束` 之间的 Markdown 报告内容
2. 将提取到的报告内容**直接在对话中展示给用户**（使用 Markdown 格式渲染）
3. 如果控制台输出被截断导致报告不完整，使用 `read_file` 读取报告文件路径（在输出中会显示 `✅ 报告已生成: <路径>`），然后将文件内容展示给用户
4. 展示报告后，基于报告数据给出简要的**个性化洞察和建议**

**禁止**：只告诉用户"报告已生成在某个路径"而不展示内容。用户期望在对话中直接看到完整报告。

## 配置说明

### 统一入口配置（scripts/run.py）

| 配置项 | 类型 | 说明 |
|--------|------|------|
| `PLATFORMS` | list | 要采集的平台列表 |
| `KEYWORDS` | list | 搜索关键词列表（AI 自动拓展） |
| `MAX_ITEMS` | int | 每平台保留的 Top N 数量 |
| `MAX_COMMENTS` | int | 每条内容最多抓取的评论数 |
| `SEARCH_PER_KEYWORD` | int | 每个关键词搜索返回的结果数 |
| `VIDEO_URLS` | list | URL 直接分析模式（非空时跳过搜索） |
| `BILI_COOKIE` | str | B 站 Cookie（留空时自动弹出浏览器登录） |
| `DOUYIN_COOKIE` | str | 抖音 Cookie（留空时自动弹出浏览器登录） |
| `XHS_COOKIE` | str | 小红书 Cookie（留空时自动弹出浏览器登录） |

### 多关键词搜索策略

AI 根据用户提供的核心关键词，自动拓展为 5 个相关搜索词：
1. 逐个关键词搜索
2. 合并所有搜索结果
3. 按标题去重（保留点赞更高的）
4. 按点赞数排序，取 Top N

## 输出结构

```
scripts/<platform>/output/<keyword>/
├── results.json          # 汇总数据
├── video_1_xxx/          # 单条内容数据
│   ├── data.json
│   ├── transcript.txt    # 转录文本
│   └── content.txt       # 正文（图文）
└── report/
    └── report_xxx.md     # 单平台分析报告

scripts/output/
└── cross_platform_report_xxx.md  # 跨平台对比报告（多平台时生成）
```

## 错误处理

1. **Cookie 过期**: 提示用户重新获取对应平台 Cookie
2. **某平台失败**: 继续执行其他平台，记录失败原因
3. **视频下载失败**: 跳过该内容继续处理下一个
4. **转录失败**: 检查 ffmpeg/demucs/whisper 安装情况
5. **验证码**: 抖音可能弹出验证码，等待用户手动完成

## 详细参考

- [references/cookie-guide.md](./references/cookie-guide.md) — Cookie 获取指南
- [references/dependencies.md](./references/dependencies.md) — 依赖安装和环境配置
