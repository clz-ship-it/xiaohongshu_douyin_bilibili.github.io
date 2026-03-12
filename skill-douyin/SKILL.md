---
name: skill-douyin
description: |
  抖音爆款内容分析器。搜索抖音关键词下的高赞视频，提取字幕或转录视频内容，抓取热门评论，生成爆款分析报告。
  当用户提到"抖音分析"、"抖音爆款"、"douyin 分析"、"抖音搜索"、"抖音评论"、"抖音字幕"、"分析抖音视频"时使用。
  即使用户只说"帮我看看抖音上某个话题的热门内容"也应触发此 skill。
  当用户提供抖音视频 URL 时也应触发此 skill。
---

# 抖音爆款内容分析器

## Overview

搜索 **抖音** 关键词下的高赞视频，自动提取字幕或转录视频内容、抓取热门评论，生成 **爆款分析报告**。

| 功能 | 说明 |
|------|------|
| 关键词搜索 | 按点赞数排序，取 Top N 视频（undetected_chromedriver） |
| 内容提取 | 四级降级：抖音字幕→yt-dlp→必剪ASR→Whisper转录 |
| 评论抓取 | API 优先 + 三级降级（API→源码正则→DOM 解析） |
| 报告生成 | 自动生成 Markdown 爆款分析报告 |

## 严格禁止 (NEVER DO)

1. **不要在没有 Cookie 时运行** — 抖音搜索和评论都需要登录态 Cookie，必须先向用户索取
2. **不要使用 headless 模式** — 抖音检测 headless 极严，必须可见浏览器模式
3. **不要编造数据** — 点赞、评论数据必须从返回值提取
4. **不要跳过报告生成** — 数据采集完成后必须自动生成分析报告
5. **不要修改 Cookie 变量名** — run.py 第 2 行 DOUYIN_COOKIE 是唯一的 Cookie 配置入口

## Cookie 要求

抖音搜索和评论 API 需要登录态 Cookie 才能正常返回数据。获取方式参见 [references/cookie-guide.md](./references/cookie-guide.md)。

## 脚本总览

| 脚本 | 用途 | 说明 |
|------|------|------|
| `scripts/run.py` | 主入口 | 配置区：KEYWORDS, MAX_VIDEOS, MAX_COMMENTS, DOUYIN_COOKIE |
| `scripts/douyin_api.py` | 搜索 + 评论抓取 | API 优先三级降级评论抓取，undetected_chromedriver |
| `scripts/subtitle_extractor.py` | 字幕提取（三级降级） | 抖音专属→yt-dlp→必剪 ASR |
| `scripts/downloader.py` | 视频下载 | 浏览器提取 video src 地址 |
| `scripts/transcriber.py` | Whisper 语音转录 | 从视频提取音频→Whisper tiny 转录 |
| `scripts/bcut_asr.py` | 必剪云端 ASR | 免费中文语音识别，无需 GPU |
| `scripts/generate_report.py` | 爆款分析报告生成 | 读取 JSON 数据，生成 Markdown 报告 |
| `scripts/html_structure_detector.py` | HTML 结构检测 | 检测抖音页面结构变化 |
| `scripts/config.py` | 配置 | 浏览器 UA、超时等 |

## 核心工作流

```python
# 1. 向用户索取抖音 Cookie
# 打开 douyin.com → F12 → Application → Cookies → 复制全部

# 2. 修改 run.py 配置区
DOUYIN_COOKIE = "用户提供的 Cookie"   # 第 2 行
KEYWORDS = "用户指定的关键词"          # 第 21 行
VIDEO_URLS = []  # URL 直接分析模式（可选）
# 示例: VIDEO_URLS = ["https://www.douyin.com/video/7615202845574302986"]
MAX_VIDEOS = 10
MAX_COMMENTS = 30

# 3. 执行采集脚本
# cd "$SKILL_DIR/scripts" && python run.py

# 4. 脚本自动完成以下步骤:
#    Step 0: HTML 结构检测（对比历史版本，标记变化）
#    Step 1: 初始化浏览器并注入 Cookie
#    Step 2: 搜索视频（按点赞排序取 Top N）或直接分析指定 URL
#    Step 3: 对每个视频：下载→转录→抓取评论
#    Step 4: 保存汇总 results.json
#    Step 5: 生成爆款分析报告
#    保存 → output/<关键词>/results.json + report.md

# 5. 读取报告，输出分析结果
```

## 两种输入模式

| 模式 | 配置 | 说明 |
|------|------|------|
| 关键词搜索 | `KEYWORDS = "xxx"` | 搜索关键词下的高赞视频（默认模式） |
| URL 直接分析 | `VIDEO_URLS = ["url1", "url2"]` | 直接分析指定的视频 URL，跳过搜索 |

URL 模式优先级高于关键词模式：当 VIDEO_URLS 非空时自动使用 URL 模式。

## 评论抓取策略（三级降级）

评论抓取采用 API 优先的三级降级策略，确保高质量数据：

| 级别 | 方式 | 说明 | 数据质量 |
|------|------|------|----------|
| 1 | **抖音评论 API** | 通过浏览器 JS fetch 调用 `/aweme/v1/web/comment/list/` 接口 | 最佳：精确的点赞数、用户名、评论内容 |
| 2 | **源码正则提取** | 从页面 HTML 源码中正则匹配评论 JSON 数据 | 良好：可获取大部分字段 |
| 3 | **DOM 元素解析** | 从渲染后的页面 DOM 中提取评论元素 | 一般：受页面结构变化影响 |

API 接口详情：
- **URL**: `https://www.douyin.com/aweme/v1/web/comment/list/`
- **参数**: `aweme_id`（视频ID）、`cursor`（分页）、`count`（数量）
- **认证**: 复用浏览器已有的 Cookie，无需额外配置
- **优势**: 不受前端 DOM 结构变化影响，数据准确稳定

## 内容提取降级策略

脚本按以下顺序尝试提取视频文字内容，每级失败自动降级：

| 级别 | 方式 | 说明 |
|------|------|------|
| 1 | 抖音专属字幕 | 从页面 SSR 数据中提取字幕 URL |
| 2 | yt-dlp 字幕 | 尝试提取人工/自动字幕 |
| 3 | 必剪 ASR | 下载音频，使用必剪云端免费 ASR |
| 4 | Whisper 转录 | 浏览器下载视频→moviepy 提取音频→Whisper tiny 转录 |

## 输出结构

```
output/<关键词>/
├── results.json                              # 采集的原始数据
├── douyin_report_<关键词>_<时间>.md           # 爆款分析报告
├── structure_reports/                        # HTML 结构检测报告
├── video_1_<video_id>/
│   ├── data.json                             # 单个视频数据
│   └── audio.wav                             # 音频文件（如有）
└── ...
```

## 报告内容

报告包含以下板块：

1. **📊 数据总览** — 视频数、总点赞、平均点赞、内容提取成功率、评论数
2. **🏆 Top 视频排行** — 每个视频的详情、转录摘要、热门评论 Top 5
3. **💬 评论区深度分析** — 全网最热评论 Top 10、评论高频关键词 Top 20
4. **📝 内容分析** — 视频内容高频主题词 Top 20
5. **🎯 爆款特征总结** — 标题特征、互动数据、标题关键词
6. **🔑 可复制的爆款公式** — 标题策略、内容定位、用户关注点、创作建议

## 数据格式

采集的 JSON 数据结构，每个视频包含：

```json
{
  "video_info": {
    "title": "视频标题",
    "author": "作者名称",
    "url": "https://www.douyin.com/video/xxx",
    "video_id": "7xxx",
    "like_count": 250000,
    "comment_count": 3000,
    "share_count": 500,
    "collect_count": 8000,
    "play_count": 0
  },
  "transcript": "视频转录全文...",
  "comments": [
    {
      "author": "评论者",
      "content": "评论内容",
      "like_count": 48,
      "reply_count": 5
    }
  ]
}
```

## 前置依赖

| 依赖 | 说明 | 安装方式 |
|------|------|----------|
| **Python 3.8+** | 脚本运行环境 | [python.org](https://www.python.org/downloads/) |
| **Chrome 浏览器** | undetected_chromedriver 自动匹配版本 | [google.com/chrome](https://www.google.com/chrome/) |
| **ffmpeg** | 音频提取和格式转换 | Windows: `choco install ffmpeg` / macOS: `brew install ffmpeg` |
| **undetected-chromedriver** | 绕过抖音反爬检测 | `pip install undetected-chromedriver` |
| **openai-whisper** | 语音转录（Whisper tiny 模型） | `pip install openai-whisper` |
| **moviepy** | 从视频中提取音频 | `pip install moviepy` |
| **yt-dlp** | 字幕提取 | `pip install yt-dlp` |
| **requests** | HTTP 请求 | `pip install requests` |

一键安装：
```bash
pip install undetected-chromedriver openai-whisper moviepy yt-dlp requests
```

## 错误处理

1. **Cookie 过期**: 提示用户重新获取抖音 Cookie（有效期约 24 小时）
2. **验证码弹出**: 脚本暂停等待，用户在浏览器中手动完成验证
3. **评论 API 失败**: 自动降级到源码正则，再降级到 DOM 解析
4. **内容提取失败**: 四级降级全部失败时跳过，继续处理下一个视频
5. **搜索无结果**: 提示用户更换关键词或检查 Cookie
6. **请求限流**: 脚本内置请求间隔延迟

## 详细参考

- [references/cookie-guide.md](./references/cookie-guide.md) — 抖音 Cookie 获取指南
- [example_report.md](./example_report.md) — 示例报告格式
