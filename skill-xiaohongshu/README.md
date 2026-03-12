# 小红书爆款内容拆解器

使用 **undetected-chromedriver** 模拟真实用户浏览行为，搜索小红书关键词下的高赞爆款笔记，在搜索结果页**逐个点击笔记卡片**进入详情页，从 DOM 提取标题、正文、互动数据和高赞评论，**自动生成 Markdown 格式爆款拆解报告**。

## 核心特点

- **🔐 需要 Cookie**，使用 undetected-chromedriver + Cookie 注入绕过反爬
- **🛡️ 反爬绕过**：点击搜索结果页卡片封面链接（带 xsec_token）进入详情页，避免 sec 网关拦截
- **📝 DOM 提取**：从详情页 DOM 直接提取标题、正文、互动数据（点赞/收藏/评论/分享）
- **💬 每笔记抓取高赞评论**（默认 30 条）
- **📊 自动生成报告**：Markdown 格式爆款拆解分析报告
- **🔄 智能卡片遍历**：按页面卡片出现顺序逐个点击，自动跳过已处理笔记

## 工作原理

```
搜索结果页                          详情页
┌─────────────────┐    点击卡片    ┌─────────────────┐
│  note-item 1 ✓  │──────────────→│  #detail-title   │
│  note-item 2    │               │  #detail-desc    │
│  note-item 3    │    返回搜索    │  .comment-item   │
│  ...            │←──────────────│  .like-wrapper   │
└─────────────────┘               └─────────────────┘
```

1. 创建 undetected-chromedriver 浏览器，注入 Cookie
2. 导航到搜索结果页，提取笔记列表（按点赞排序）
3. 在搜索结果页逐个点击卡片封面链接（`a.cover`，带 xsec_token）
4. 进入详情页后，从 DOM 提取：标题、正文、互动数据、评论
5. 返回搜索结果页，继续点击下一个未处理的卡片
6. 保存数据并生成 Markdown 爆款分析报告

## 快速开始

1. **安装依赖**:
   ```bash
   pip install undetected-chromedriver selenium
   ```

2. **获取小红书 Cookie**:
   - 打开 xiaohongshu.com → 登录账号
   - F12 → Application → Cookies → 复制所有 Cookie
   - 或 Network 面板找到任意请求，复制 Cookie 头

3. **修改配置**:
   编辑 `scripts/run.py` 顶部配置区:
   ```python
   KEYWORDS = "你的关键词"      # 例如: "openclaw"
   MAX_NOTES = 10               # 抓取笔记数量
   MAX_COMMENTS = 30            # 每笔记评论数
   XHS_COOKIE = "你的Cookie"    # 粘贴复制的Cookie
   ```

4. **运行采集**:
   ```bash
   cd scripts && python run.py
   ```

5. **查看结果**:
   - 数据文件: `output/<关键词>/results.json`
   - **报告文件**: `output/report/xhs_report_<关键词>_<时间戳>.md`

## 文件结构

```
skill-xiaohongshu/
├── SKILL.md                  # AI 指令 (Agent 读取)
├── package.json              # 包信息
├── README.md                 # 说明文档
├── scripts/
│   ├── run.py                # 主入口：搜索→逐个点击卡片→提取详情→评论→生成报告
│   ├── xhs_api.py            # 核心引擎：浏览器管理、搜索、卡片点击导航、DOM 提取
│   ├── downloader.py         # 视频下载（仅视频笔记需要）
│   ├── transcriber.py        # Whisper 转录（仅视频笔记需要）
│   ├── subtitle_extractor.py # 字幕检测与提取（仅视频笔记需要）
│   ├── generate_report.py    # Markdown 报告生成
│   └── config.py             # 配置和日志
└── references/
    ├── report-format.md      # 报告输出格式模板
    └── dependencies.md       # 依赖安装说明
```

## 报告输出格式

自动生成 Markdown 格式爆款拆解报告，包含：

| 章节 | 内容 |
|------|------|
| **📊 数据总览** | 笔记数、视频/图文分布、总点赞、总收藏、平均点赞、内容提取成功率、总评论数 |
| **🏆 Top 笔记排行** | 按点赞排序的笔记列表，含作者、类型、互动数据、内容摘要、热门评论 Top 5 |
| **💬 评论区深度分析** | 全网最热评论 Top 10、评论高频关键词 Top 20 |
| **📝 内容分析** | 笔记内容高频主题词 Top 20 |
| **🎯 爆款特征总结** | 标题特征（长度、Emoji、标点使用）、标题关键词、互动数据特征 |
| **🔑 可复制的爆款公式** | 基于数据的创作建议（标题策略、内容定位、用户关注点、互动策略） |

## 注意事项

- **Cookie 必需**: 小红书必须登录态，否则搜索和内容获取全部失败
- **Cookie 有效期**: 通常 1-7 天，过期需重新获取
- **禁止 `driver.get()` 直接导航**: 会被 sec 网关拦截（error_code=300031），必须通过点击卡片进入详情页
- **瀑布流懒加载**: 搜索结果页返回后会重新渲染，脚本自动处理此问题
