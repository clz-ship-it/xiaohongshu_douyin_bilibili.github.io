---
name: skill-bilibili
description: |
  B 站爆款内容分析器。搜索 B 站关键词下的高赞视频，提取 AI 字幕，抓取热门评论，生成爆款分析报告。
  当用户提到"B站分析"、"B站爆款"、"bilibili 分析"、"B站搜索"、"B站评论"、"B站字幕"、"分析B站视频"时使用。
  当用户提供B站视频 URL 时也应触发此 skill。
  即使用户只说"帮我看看B站上某个话题的热门内容"也应触发此 skill。
---

# B 站爆款内容分析器

## Overview

搜索 **B 站** 关键词下的高赞视频，自动提取 AI 字幕、抓取热门评论，生成 **爆款分析报告**。

| 功能 | 说明 |
|------|------|
| 关键词搜索 | 按点赞数排序，取 Top N 视频 |
| 字幕提取 | 通过 Player API 获取 AI 自动字幕（需 Cookie） |
| 评论抓取 | 支持多页抓取，按点赞排序（需 Cookie） |
| 报告生成 | 自动生成 Markdown 爆款分析报告 |

## 严格禁止 (NEVER DO)

1. **不要在没有 Cookie 时运行** — 字幕和评论 API 都需要 B 站登录态 Cookie，必须先向用户索取
2. **不要编造数据** — 点赞、评论数据必须从 API 返回值提取
3. **不要跳过报告生成** — 数据采集完成后必须自动生成分析报告

## Cookie 要求

B 站字幕和评论 API 需要登录态 Cookie 才能正常返回数据。**必须手动提供 Cookie**。

获取方式：
1. 打开 bilibili.com 并登录
2. 按 F12 打开开发者工具
3. 进入 Application → Cookies → https://www.bilibili.com
4. 复制全部 Cookie 字符串
5. 粘贴到 `scripts/run.py` 的 `BILI_COOKIE` 配置项中

参见 [references/cookie-guide.md](./references/cookie-guide.md)。

## 脚本总览

| 脚本 | 用途 | 说明 |
|------|------|------|
| `scripts/run.py` | 主入口：搜索→字幕→评论→报告 | 配置区：KEYWORDS, MAX_VIDEOS, MAX_COMMENTS, BILI_COOKIE（需手动粘贴） |
| `scripts/bilibili_api.py` | B 站 API 封装 | 搜索、字幕、评论、视频详情 |
| `scripts/generate_report.py` | 爆款分析报告生成 | 读取 JSON 数据，生成 Markdown 报告 |

## 核心工作流

```python
# 1. 向用户索取：关键词/URL + B 站 Cookie
# Cookie 获取：打开 bilibili.com → F12 → Application → Cookies → 复制全部

# 2. 修改 run.py 配置区
KEYWORDS = "用户提供的关键词"  # 关键词搜索模式
VIDEO_URLS = []  # URL 直接分析模式（可选）
# 示例: VIDEO_URLS = ["https://www.bilibili.com/video/BV1xxx"]
BILI_COOKIE = "用户提供的 Cookie"

# 3. 执行采集脚本
# cd "$SKILL_DIR/scripts" && python run.py

# 4. 脚本自动完成四个步骤:
#    Step 1: 搜索视频（按点赞排序取 Top N）
#    Step 2: 提取 AI 字幕（需要 Cookie）
#    Step 3: 抓取热门评论（多页抓取，按点赞排序）
#    Step 4: 生成爆款分析报告
#    保存 → output/<关键词>/data.json + report.md

# 5. 读取报告，输出分析结果
```

## 两种输入模式

| 模式 | 配置 | 说明 |
|------|------|------|
| 关键词搜索 | `KEYWORDS = "xxx"` | 搜索关键词下的高赞视频（默认模式） |
| URL 直接分析 | `VIDEO_URLS = ["url1", "url2"]` | 直接分析指定的视频 URL，跳过搜索 |

URL 模式优先级高于关键词模式：当 VIDEO_URLS 非空时自动使用 URL 模式。

## 输出结构

```
output/<关键词>/
├── data.json              # 采集的原始数据（视频+字幕+评论）
└── report.md              # 爆款分析报告
```

## 报告内容

报告包含以下板块：

1. **📊 数据总览** — 视频数、总点赞、平均点赞、字幕成功率、评论数
2. **🏆 Top 视频排行** — 每个视频的详情、字幕摘要、热门评论 Top 5
3. **💬 评论区深度分析** — 全网最热评论 Top 10、评论高频关键词
4. **📝 字幕内容分析** — 视频内容高频主题词
5. **🎯 爆款特征总结** — 标题特征、互动数据、标题关键词
6. **🔑 可复制的爆款公式** — 标题策略、内容定位、用户关注点、创作建议

## 数据格式

采集的 JSON 数据为数组，每个元素包含：

```json
{
  "bvid": "BV1xxx",
  "aid": 123456,
  "video_title": "视频标题",
  "video_url": "https://www.bilibili.com/video/BV1xxx",
  "author": "UP主名称",
  "like_count": 12345,
  "subtitle_success": true,
  "subtitle_text": "字幕全文...",
  "subtitle_count": 310,
  "subtitle_language": "中文",
  "comments": [
    {
      "author": "评论者",
      "content": "评论内容",
      "like_count": 48,
      "reply_count": 5,
      "publish_time": "2026-03-08 15:30:00"
    }
  ],
  "comment_count": 30
}
```

## API 说明

`scripts/bilibili_api.py` 封装了以下 B 站公开 API：

| 函数 | API | 用途 |
|------|-----|------|
| `search()` | `/x/web-interface/search/type` | 关键词搜索视频 |
| `get_video_detail()` | `/x/web-interface/view` | 获取视频详情 |
| `fetch_subtitles()` | `/x/player/v2` | 获取 AI 字幕（需 Cookie） |
| `fetch_comments()` | `/x/v2/reply` | 获取评论（需 Cookie） |
| `fetch_comments_for_video()` | 组合调用 | 多页抓取视频评论 |

所有 API 使用 Python 标准库 `urllib`，无需安装第三方依赖。

## 前置依赖

运行前需确保以下环境已就绪：

| 依赖 | 说明 | 安装方式 |
|------|------|----------|
| **Python 3.6+** | 脚本运行环境 | [python.org](https://www.python.org/downloads/) |

本 skill 仅使用 Python 标准库（`urllib`、`json`、`re` 等），**无需安装任何第三方 pip 包**。

## 错误处理

1. **Cookie 过期**: 提示用户重新获取 B 站 Cookie
2. **字幕不可用**: 部分视频无 AI 字幕，跳过继续处理
3. **评论获取失败**: 记录错误，继续处理下一个视频
4. **搜索无结果**: 提示用户更换关键词
5. **请求限流**: 脚本内置 0.5-1s 请求间隔

## 详细参考

- [references/cookie-guide.md](./references/cookie-guide.md) — B 站 Cookie 获取指南
