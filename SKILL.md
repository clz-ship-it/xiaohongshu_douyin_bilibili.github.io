---
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

> **Cookie 存储**：所有 Cookie 统一存放在 `~/.aone_copilot/skills/.env` 文件中，格式为 `XHS_COOKIE=xxx`、`DOUYIN_COOKIE=xxx` 和 `BILI_COOKIE=xxx`。脚本会自动读取。

## 严格禁止 (NEVER DO)

1. **不要在没有 Cookie 时运行小红书/抖音** — 必须先向用户索取对应 Cookie
2. **不要混淆平台数据** — 每个平台的数据独立保存
3. **不要跳过字幕检测直接下载视频** — 有字幕则直接提取，无字幕才下载转录
4. **不要保留视频文件** — 转录完成后必须删除视频，只保留文本
5. **不要编造数据** — 点赞、收藏、播放量必须从 API 返回值提取

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
| `BILI_COOKIE` | str | B 站 Cookie（留空自动获取） |
| `DOUYIN_COOKIE` | str | 抖音 Cookie（留空自动获取） |
| `XHS_COOKIE` | str | 小红书 Cookie（留空自动获取） |

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
