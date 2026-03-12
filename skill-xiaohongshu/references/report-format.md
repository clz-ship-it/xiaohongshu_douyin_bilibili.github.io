# 小红书爆款拆解报告 — 输出格式模板

读取 `scripts/output/<关键词>/results.json` 后，按以下格式生成报告。

## 报告头部

```
# 🔥 小红书爆款内容拆解报告

**选题/关键词**：{keyword}
**渠道**：小红书（Xiaohongshu）
**分析笔记数**：{total_notes}（📹视频 {video_count} + 📝图文 {image_text_count}）
**生成时间**：{generated_at}
```

## 每条爆款笔记（循环输出 notes 数组）

```
---
## 第 N 条：{note_info.title}

### 基本信息
| 项目 | 内容 |
|------|------|
| **标题** | {note_info.title} |
| **类型** | {📹视频 / 📝图文} (根据 note_info.content_type 判断) |
| **原始链接** | {note_info.url} |
| **博主** | {note_info.author} |
| **点赞** | {note_info.like_count} |
| **收藏** | {note_info.collect_count} |
| **评论数** | {note_info.comment_count} |
| **转发** | {note_info.share_count} |

### 内容拆解

- 视频笔记: 基于 transcript 字段的转录文字进行分析
- 图文笔记: 基于 text_content 字段的正文内容进行分析

#### 1. 中心思想
分析笔记讨论的核心话题

#### 2. 行文结构
分析内容结构：开头如何吸引注意力、中间如何展开、结尾如何收束

#### 3. 语言习惯与金句
分析语言风格，提取3-5个有代表性的金句

### 评论区分析（30条高赞评论）

基于 comments 数组：

| 排名 | 评论者 | 评论内容 | 点赞数 | 二级评论数 |
|------|--------|----------|--------|-----------|
| 1 | {comments[0].author} | {comments[0].content} | {comments[0].like_count} | {comments[0].reply_count} |
| ... | ... | ... | ... | ... |

#### 评论区用户关注点分类
将30条评论按主题分类：认同/共鸣、质疑/反驳、补充信息、求助/提问、种草/求链接等
```

## 报告尾部：整体爆发逻辑分析

```
---
## 📊 整体爆发逻辑分析

### 内容核心
综合所有笔记，分析爆款内容的共同特征

### 图文 vs 视频对比
如果同时有图文和视频笔记，对比两种形式的互动数据差异和内容特点

### 评论区关注重点
综合所有评论区，分析用户最关心的问题

### 可复制的爆款公式
基于以上分析，总结可复制的爆款内容创作建议
```

## JSON 数据结构参考

```json
{
  "keyword": "关键词",
  "platform": "xiaohongshu",
  "total_notes": 10,
  "video_count": 3,
  "image_text_count": 7,
  "generated_at": "2026-03-09T16:00:00",
  "notes": [
    {
      "note_info": {
        "title": "笔记标题",
        "author": "博主",
        "url": "https://www.xiaohongshu.com/explore/xxx",
        "note_id": "xxx",
        "like_count": 12000,
        "collect_count": 5000,
        "comment_count": 800,
        "share_count": 200,
        "is_video": false,
        "content_type": "image_text"
      },
      "transcript": "视频笔记的转录文字（图文笔记为空）",
      "text_content": "图文笔记的正文内容（视频笔记为空）",
      "comments": [
        {
          "author": "评论者",
          "content": "评论内容",
          "like_count": 500,
          "reply_count": 20
        }
      ]
    }
  ]
}
```
