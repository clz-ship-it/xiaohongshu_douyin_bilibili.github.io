# 🦞 多平台爆款内容分析工具集

基于 [Aone Copilot](https://copilot.code.alibaba-inc.com) Skill 框架开发的三合一爆款内容分析工具，支持**小红书**、**抖音**、**B站**三大平台的内容抓取与分析。

## ✨ 核心特性

- **🔍 关键词搜索** — 输入关键词，自动搜索三大平台的相关内容
- **📊 爆款分析** — 提取点赞、收藏、评论等互动数据，分析爆款特征
- **📝 字幕提取** — 自动提取视频字幕/语音转文字，获取完整内容
- **💬 评论抓取** — 抓取热门评论，分析用户反馈和舆情
- **📋 报告生成** — 自动生成结构化的爆款内容分析报告
- **🔐 Cookie 自动获取** — 首次运行自动弹出浏览器登录，Cookie 自动缓存，无需手动配置

## 📁 项目结构

```
├── README.md                    # 本文件
├── skill-xiaohongshu/           # 小红书爆款分析 Skill
│   ├── SKILL.md                 # Skill 配置文件
│   ├── scripts/
│   │   ├── run.py               # 主入口脚本
│   │   ├── cookie_helper.py     # Cookie 自动获取模块
│   │   ├── xhs_api.py           # 小红书 API 封装
│   │   ├── downloader.py        # 图片/视频下载器
│   │   ├── transcriber.py       # 语音转文字
│   │   ├── subtitle_extractor.py # 字幕提取
│   │   ├── generate_report.py   # 报告生成
│   │   └── config.py            # 配置文件
│   ├── references/              # 参考文档
│   └── example_report.md        # 示例报告
│
├── skill-douyin/                # 抖音爆款分析 Skill
│   ├── SKILL.md
│   ├── scripts/
│   │   ├── run.py               # 主入口脚本
│   │   ├── cookie_helper.py     # Cookie 自动获取模块
│   │   ├── douyin_api.py        # 抖音 API 封装
│   │   ├── bcut_asr.py          # 必剪 ASR 语音识别
│   │   ├── downloader.py        # 视频下载器
│   │   ├── transcriber.py       # 语音转文字
│   │   ├── subtitle_extractor.py # 字幕提取
│   │   ├── generate_report.py   # 报告生成
│   │   ├── html_structure_detector.py # 页面结构检测
│   │   └── config.py            # 配置文件
│   ├── references/              # 参考文档
│   └── example_report.md        # 示例报告
│
├── skill-bilibili/              # B站爆款分析 Skill
│   ├── SKILL.md
│   ├── scripts/
│   │   ├── run.py               # 主入口脚本
│   │   ├── cookie_helper.py     # Cookie 自动获取模块
│   │   ├── bilibili_api.py      # B站 API 封装
│   │   ├── generate_report.py   # 报告生成
│   │   ├── test_bili_api.py     # API 测试脚本
│   │   └── debug_subtitle.py    # 字幕调试工具
│   ├── references/              # 参考文档
│   └── example_report.md        # 示例报告
```

## 🚀 快速开始

### 环境要求

- **Python 3.9+**
- **Chrome 浏览器**（用于自动登录获取 Cookie）

### 安装依赖

```bash
pip install requests beautifulsoup4 undetected-chromedriver yt-dlp
```

### 使用方式

每个 Skill 都可以独立运行。进入对应的 `scripts/` 目录，编辑 `run.py` 顶部的配置区，然后运行：

```bash
# 小红书
cd skill-xiaohongshu/scripts
python run.py

# 抖音
cd skill-douyin/scripts
python run.py

# B站
cd skill-bilibili/scripts
python run.py
```

### 配置说明

每个 `run.py` 顶部都有一个配置区，可以设置：

```python
KEYWORD = "openclaw"     # 搜索关键词
MAX_NOTES = 10           # 最多抓取笔记/视频数量
MAX_COMMENTS = 30        # 每条内容最多抓取评论数
```

## 🔐 Cookie 自动获取

三个 Skill 都内置了 **Cookie 自动获取功能**，采用三级策略：

1. **硬编码 Cookie** — 如果在 `run.py` 配置区填入了 Cookie，优先使用
2. **缓存文件** — 从 `.cookie_cache/` 目录读取上次保存的 Cookie
3. **浏览器登录** — 自动弹出 Chrome 浏览器，打开平台登录页面，用户扫码/输入密码登录后，脚本自动提取 Cookie 并缓存

> 💡 首次运行时会自动弹出浏览器让你登录，登录成功后 Cookie 会被缓存，后续运行无需重复登录。

### 登录状态检测

| 平台 | 检测 Cookie | 登录页面 |
|------|------------|---------|
| 小红书 | `web_session` | `xiaohongshu.com` |
| 抖音 | `sessionid` | `douyin.com` |
| B站 | `SESSDATA` | `passport.bilibili.com/login` |

## 📊 输出说明

运行后，数据保存在各 Skill 的 `scripts/output/` 目录下：

```
output/
├── search_results.json      # 搜索结果
├── subtitles/               # 字幕文件
├── comments/                # 评论数据
└── report.md                # 分析报告
```

## 🔧 作为 Aone Copilot Skill 使用

这三个工具也可以作为 [Aone Copilot](https://copilot.code.alibaba-inc.com) 的 Skill 使用。将对应的 `skill-*` 目录复制到 `~/.aone_copilot/skills/` 下即可注册为 Skill，之后在 Copilot 对话中直接说"分析小红书/抖音/B站上关于 XXX 的爆款内容"即可触发。

## ⚠️ 注意事项

1. **合规使用** — 仅用于个人学习和研究，请遵守各平台的使用条款
2. **频率限制** — 脚本内置了请求延迟，避免对平台造成压力
3. **版权尊重** — 尊重内容创作者的版权，不要用于商业用途
4. **数据安全** — Cookie 仅保存在本地，不会上传到任何第三方服务

## 📄 License

MIT License
