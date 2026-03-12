---
name: skill-xiaohongshu
description: |
  小红书爆款内容拆解器。使用 undetected-chromedriver 模拟真实用户浏览行为，在搜索结果页逐个点击笔记卡片进入详情页，从 DOM 提取标题、正文、互动数据（点赞/收藏/评论/分享）和高赞评论，自动生成 Markdown 格式爆款拆解分析报告。
  当用户提到"小红书爆款"、"小红书分析"、"小红书拆解"、"小红书笔记"、"小红书评论"、"小红书选题"、"xhs"或提供小红书笔记URL时使用。
  即使用户只说"分析小红书"或"小红书搜一下xxx"或提供笔记URL也应触发。不要在B站、抖音场景时触发。
---

# 小红书爆款内容拆解器

## Overview

使用 **undetected-chromedriver** 模拟真实用户浏览行为，搜索小红书关键词下的高赞爆款笔记。核心策略是**在搜索结果页逐个点击笔记卡片封面链接**（带 xsec_token），进入详情页后从 DOM 提取标题、正文、互动数据和高赞评论。自动生成 Markdown 格式爆款拆解报告。**小红书必须提供 Cookie**。

## 反爬策略（重要）

小红书有严格的 sec 网关反爬机制，以下是已验证的绕过方案：

1. **使用 undetected-chromedriver**（而非普通 selenium），自动隐藏 webdriver 特征
2. **禁止 `driver.get()` 直接导航到详情页**，会被 sec 网关拦截（error_code=300031）
3. **必须点击搜索结果页的 `a.cover` 封面链接**进入详情页，链接自带 `xsec_token` 验证参数
4. **搜索结果页是瀑布流懒加载**，从详情页返回后页面重新渲染，之前滚动加载的卡片不在 DOM 中
5. **按页面卡片出现顺序逐个点击**，用 `processed_note_ids` 集合跟踪已处理的笔记，避免重复

## 严格禁止 (NEVER DO)

1. **不要在没有 Cookie 时运行脚本** — 小红书必须 Cookie 登录态，否则搜索和内容获取全部失败
2. **不要使用 `driver.get()` 直接导航到详情页** — 会被 sec 网关拦截，必须通过点击卡片进入
3. **不要编造笔记数据** — 点赞、收藏、评论数必须从 DOM 提取，不可猜测
4. **不要合并多条笔记的评论** — 每条笔记的评论独立分析，不可混淆
5. **不要按排序后的列表查找特定 note_id** — 必须按页面上卡片出现顺序逐个点击

## 脚本总览

| 脚本 | 用途 | 关键函数/入参 |
|------|------|--------------|
| `scripts/run.py` | 主入口：搜索→逐个点击卡片→提取详情→评论→生成报告 | 配置区: KEYWORDS, MAX_NOTES, MAX_COMMENTS, XHS_COOKIE |
| `scripts/xhs_api.py` | 核心引擎：浏览器管理、搜索、卡片点击导航、DOM 提取 | create_browser(), search(), find_and_click_next_note(), _extract_content_from_detail_page(), _extract_comments_from_detail_page(), _go_back_to_search() |
| `scripts/downloader.py` | 小红书视频下载（仅视频笔记需要） | download_xiaohongshu(note_url, output_dir, cookie_string) |
| `scripts/transcriber.py` | Whisper 转录（仅视频笔记需要） | process_video(video_dir, skip_vocal_separation=True) |
| `scripts/subtitle_extractor.py` | 字幕检测与提取（仅视频笔记需要） | try_extract_subtitles(video_url, output_dir, platform, cookie_string) |
| `scripts/generate_report.py` | Markdown 报告生成 | generate_and_save_report(json_path) |
| `scripts/config.py` | 配置和日志 | 日志格式、平台配置 |

## 意图判断

用户提到"小红书/xhs/红书":
- "搜一下/分析/爆款/选题" → 先要 Cookie，再执行完整工作流
- 提供笔记 URL → 先要 Cookie，再执行 URL 模式分析
- "评论" → 需 Cookie + 完整流程（评论在详情页提取）
- "图文/正文/文案" → 需 Cookie + 完整流程

用户提供了 Cookie:
- 写入 run.py 配置区的 XHS_COOKIE
- 或写入 `~/.aone_copilot/skills/.env` 文件中的 `XHS_COOKIE=...`

关键区分:
- 小红书需 Cookie + undetected-chromedriver
- 抖音需 Cookie + undetected-chromedriver
- B站不需 Cookie

## 前置依赖

| 依赖 | 说明 | 安装方式 |
|------|------|----------|
| **Python 3.8+** | 脚本运行环境 | [python.org](https://www.python.org/downloads/) |
| **Chrome 浏览器** | undetected-chromedriver 自动管理 | [google.com/chrome](https://www.google.com/chrome/) |
| **undetected-chromedriver** | 绕过反爬检测的浏览器自动化 | `pip install undetected-chromedriver` |
| **selenium** | WebDriver 基础库 | `pip install selenium` |
| **ffmpeg** | 音频处理（仅视频笔记需要） | Windows: `choco install ffmpeg` / macOS: `brew install ffmpeg` |
| **openai-whisper** | 语音转录（仅视频笔记需要） | `pip install openai-whisper` |

一键安装核心依赖：
```bash
pip install undetected-chromedriver selenium
```

> 图文笔记只需 undetected-chromedriver + selenium，视频笔记额外需要 whisper 相关依赖。

详细依赖说明见 [references/dependencies.md](./references/dependencies.md)

## 核心工作流

```
搜索结果页                          详情页
┌─────────────────┐    点击卡片    ┌─────────────────┐
│  note-item 1    │──────────────→│  #detail-title   │
│  note-item 2    │               │  #detail-desc    │
│  note-item 3    │    返回搜索    │  .comment-item   │
│  ...            │←──────────────│  .like-wrapper   │
└─────────────────┘               └─────────────────┘
```

```python
# 1. 向用户索取: 关键词 + 小红书 Cookie
# Cookie 获取: 打开 xiaohongshu.com → F12 → Application → Cookies → 复制

# 2. 修改 run.py 配置区
KEYWORDS = "用户提供的关键词"
XHS_COOKIE = "用户提供的Cookie"

# 3. 执行采集脚本
# cd "$SKILL_DIR/scripts" && python run.py

# 4. 脚本自动完成:
#    a. 创建 undetected-chromedriver 浏览器，注入 Cookie
#    b. 导航到搜索结果页，提取笔记列表（按点赞排序）
#    c. 在搜索结果页逐个点击卡片封面链接（a.cover，带 xsec_token）
#    d. 进入详情页后，从 DOM 提取：标题、正文、互动数据、评论
#    e. 返回搜索结果页，继续点击下一个未处理的卡片
#    f. 保存 → output/<关键词>/results.json
#    g. 生成 Markdown 爆款分析报告

# 5. 报告自动生成到 output/report/xhs_report_<关键词>_<时间戳>.md
```

## DOM 选择器参考（已验证）

| 元素 | 选择器 | 说明 |
|------|--------|------|
| 笔记卡片 | `section.note-item` | 搜索结果页的每个笔记卡片 |
| 封面链接 | `a.cover` | 卡片上的可点击封面，href 带 xsec_token |
| 笔记标题 | `#detail-title` | 详情页标题 |
| 笔记正文 | `#detail-desc` | 详情页正文内容 |
| 作者名 | `span.username` | 详情页作者名 |
| 点赞数 | `span.like-wrapper span.count` | 详情页点赞数 |
| 收藏数 | `span.collect-wrapper span.count` | 详情页收藏数 |
| 评论数 | `span.chat-wrapper span.count` | 详情页评论数 |
| 评论项 | `div[class*='comment-item']` | 评论列表中的每条评论 |

## 上下文传递规则

| 步骤 | 函数 | 提取数据 | 用于 |
|------|------|----------|------|
| 搜索 | `search()` | note_id, title, author, like_count, is_video | 笔记列表排序 |
| 点击卡片 | `find_and_click_next_note()` | clicked_note_id | 跟踪已处理笔记 |
| 提取详情 | `_extract_content_from_detail_page()` | title, content, author, like/collect/comment/share_count | 报告数据 |
| 提取评论 | `_extract_comments_from_detail_page()` | 评论列表(author, content, like_count) | 评论分析 |
| 返回搜索 | `_go_back_to_search()` | 恢复搜索结果页 | 继续下一条 |

## 错误处理

1. **Cookie 过期**: 提示用户重新获取 Cookie
2. **sec 网关拦截**: 确认使用 undetected-chromedriver 且通过点击卡片导航
3. **卡片不可见**: 自动滚动页面加载更多卡片（最多滚动 15 次）
4. **详情页加载失败**: 跳过该笔记继续处理下一个
5. **评论抓取为空**: 部分笔记关闭评论或评论数为 0，记录并跳过
6. 遇到未知错误 → 报告给用户，不要自行替代

## 报告输出格式

自动生成 Markdown 格式爆款拆解报告：

| 章节 | 内容 |
|------|------|
| **📊 数据总览** | 笔记数、视频/图文分布、总点赞、总收藏、平均点赞、内容提取成功率、总评论数 |
| **🏆 Top 笔记排行** | 按点赞排序的笔记列表，含作者、类型、互动数据、内容摘要、热门评论 Top 5 |
| **💬 评论区深度分析** | 全网最热评论 Top 10、评论高频关键词 Top 20 |
| **📝 内容分析** | 笔记内容高频主题词 Top 20 |
| **🎯 爆款特征总结** | 标题特征（长度、Emoji、标点使用）、标题关键词、互动数据特征 |
| **🔑 可复制的爆款公式** | 基于数据的创作建议（标题策略、内容定位、用户关注点、互动策略） |

报告文件保存位置: `output/report/xhs_report_<关键词>_<时间戳>.md`

## 详细参考 (按需读取)

- [references/report-format.md](./references/report-format.md) — 完整报告输出格式模板
- [references/dependencies.md](./references/dependencies.md) — 依赖安装和环境配置
