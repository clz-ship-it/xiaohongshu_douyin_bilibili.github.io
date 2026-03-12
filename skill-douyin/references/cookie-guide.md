# 抖音 Cookie 获取指南

## 为什么需要 Cookie

抖音的搜索和评论功能需要登录态才能正常返回数据。没有 Cookie 的情况下：
- 搜索页面会被反爬机制拦截，无法获取视频列表
- 评论抓取会失败，返回 0 条评论
- 浏览器可能频繁弹出验证码

## 获取步骤

### Chrome 浏览器

1. 打开 [douyin.com](https://www.douyin.com) 并**登录**你的账号
2. 按 `F12` 打开开发者工具
3. 切换到 **Application**（应用程序）标签页
4. 在左侧找到 **Storage → Cookies → https://www.douyin.com**
5. 你会看到一个 Cookie 列表，包含 `sessionid`、`ttwid`、`odin_tt` 等字段

### 复制 Cookie 字符串

**方法一：从 Network 面板复制（推荐）**

1. 在开发者工具中切换到 **Network**（网络）标签页
2. 刷新页面，随便点击一个请求
3. 在请求详情的 **Headers** 中找到 `Cookie` 字段
4. 右键复制整个 Cookie 值

**方法二：使用 EditThisCookie 插件**

1. 安装 Chrome 插件 EditThisCookie
2. 访问 douyin.com 并登录
3. 点击插件图标 → 导出 Cookie

### 重要字段说明

| 字段 | 作用 | 必须 |
|------|------|------|
| `sessionid` | 登录凭证，最重要 | ✅ |
| `ttwid` | 设备标识 | ✅ |
| `odin_tt` | 安全令牌 | ✅ |
| `sid_tt` | 会话 ID | ✅ |
| `passport_csrf_token` | CSRF Token | 推荐 |
| `UIFID` | 用户指纹 | 推荐 |

## Cookie 有效期

- 抖音 Cookie 通常有效期为 **24 小时**左右，比 B 站短很多
- 如果脚本运行时搜索无结果或评论返回 0 条，大概率是 Cookie 过期
- 建议每次使用前重新获取 Cookie

## 使用方式

将复制的 Cookie 字符串写入 `scripts/run.py` 第 2 行：

```python
DOUYIN_COOKIE = "enter_pc_once=1; sessionid=xxx; ttwid=xxx; ..."
```

## 安全提示

- Cookie 等同于你的登录凭证，**不要分享给他人**
- 仅在本地环境使用，不要上传到公开仓库
- 使用完毕后可以在浏览器中退出登录使 Cookie 失效
