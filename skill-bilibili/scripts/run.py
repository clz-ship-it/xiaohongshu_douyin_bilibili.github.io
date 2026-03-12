# -*- coding: utf-8 -*-
"""B 站关键词搜索 + 字幕提取 + 高赞评论爬虫（字幕提取需要 Cookie）"""

import json
import os
import re
import time
from datetime import datetime

script_dir = os.path.dirname(os.path.abspath(__file__))

import bilibili_api as bilibili

# ========== 配置区 ==========
KEYWORDS = "openclaw"    # 搜索关键词
MAX_VIDEOS = 10          # 抓取点赞最高的视频数量
MAX_COMMENTS = 30        # 每个视频最多抓取的评论数量（按热度/点赞排序）
MAX_PAGES = 2            # 每个视频最多抓取的评论页数（每页最多 20 条）

# URL 直接分析模式：填入B站视频 URL 列表，非空时跳过搜索
# 示例: VIDEO_URLS = ["https://www.bilibili.com/video/BV1xxx"]
VIDEO_URLS = []

# Cookie 配置（需要用户手动提供）
# 获取方式：打开 bilibili.com → F12 → Application → Cookies → 复制全部 Cookie 字符串
# 将 Cookie 粘贴到下方引号内
BILI_COOKIE = ""  # 请填入你的 B站 Cookie（获取方式：打开 bilibili.com → F12 → Application → Cookies → 复制全部）
# ============================

if __name__ == "__main__":
    total_start_time = time.time()

    # 判断使用哪种模式
    use_url_mode = bool(VIDEO_URLS)

    print(f"\n{'=' * 60}")
    if use_url_mode:
        print(f"  B站爬虫 - URL 直接分析 + 字幕提取 + 评论")
        print(f"  模式: URL 直接分析")
        print(f"  视频数量: {len(VIDEO_URLS)} | 每个视频评论: {MAX_COMMENTS}")
    else:
        print(f"  B站爬虫 - 搜索 + 字幕提取 + 评论")
        print(f"  关键词: {KEYWORDS}")
        print(f"  最多视频: {MAX_VIDEOS} | 每个视频评论: {MAX_COMMENTS}")
    print(f"  Cookie: {'已配置' if BILI_COOKIE else '未配置（无法获取AI字幕）'}")
    print(f"{'=' * 60}")
    print()

    # Step 1: 搜索视频 或 从 URL 获取视频详情
    step1_start = time.time()

    if use_url_mode:
        # URL 直接分析模式
        print("[Step 1] 从 URL 获取视频详情...")
        videos = []

        for url_idx, url in enumerate(VIDEO_URLS, 1):
            # 从 URL 中提取 BV 号
            match = re.search(r'/video/(BV\w+)', url)
            if not match:
                print(f"  ✗ URL {url_idx}: 无法提取 BV 号 - {url}")
                continue

            bvid = match.group(1)
            print(f"  [{url_idx}/{len(VIDEO_URLS)}] 获取视频详情: {bvid}")

            # 获取视频详情
            video_detail = bilibili.get_video_detail(bvid)

            if not video_detail:
                print(f"    ✗ 获取视频详情失败")
                continue

            # 构造与搜索结果相同格式的视频对象
            video = {
                "bvid": bvid,
                "aid": video_detail.get("aid", 0),
                "title": video_detail.get("title", ""),
                "author": video_detail.get("author", ""),
                "like_count": video_detail.get("like_count", 0),
                "url": url
            }
            videos.append(video)

            title = video.get("title", "")[:80]
            author = video.get("author", "") or "unknown"
            like_count = video.get("like_count", 0)
            print(f"    ✓ [{like_count} 赞] {title}")
            print(f"       Author: {author} | BVID: {bvid}")
            print()

        step1_elapsed = time.time() - step1_start
        print(f"\n  成功获取 {len(videos)} 个视频详情 (耗时 {step1_elapsed:.1f}s)\n")

        if not videos:
            print("  未成功获取任何视频详情。请检查 URL 是否正确。")
            exit(0)

    else:
        # 关键词搜索模式（原有逻辑）
        print("[Step 1] 搜索视频...")
        search_result = bilibili.search(
            keywords=KEYWORDS,
            page_size=MAX_VIDEOS,
        )

        videos = search_result.get("items", [])
        step1_elapsed = time.time() - step1_start
        print(f"\n  找到 {len(videos)} 个视频 (耗时 {step1_elapsed:.1f}s):\n")
        for idx, video in enumerate(videos, 1):
            title = video.get("title", "")[:80]
            author = video.get("author", "") or "unknown"
            bvid = video.get("bvid", "")
            like_count = video.get("like_count", 0)
            print(f"  {idx}. [{like_count} 赞] {title}")
            print(f"     Author: {author} | BVID: {bvid}")
            print(f"     URL: {video.get('url', '')}")
            print()

        if not videos:
            print("  未找到视频。请检查网络连接或更换关键词。")
            exit(0)

    # Step 2: 为每个视频提取字幕（使用 B站官方 API + Cookie）
    step2_start = time.time()
    subtitle_success_count = 0
    subtitle_fail_count = 0
    print(f"\n[Step 2] 提取 {min(len(videos), MAX_VIDEOS)} 个视频的字幕...\n")

    subtitle_results = {}
    for idx, video in enumerate(videos[:MAX_VIDEOS], 1):
        bvid = video.get("bvid", "")
        title = video.get("title", "")[:50]
        print(f"  [{idx}/{min(len(videos), MAX_VIDEOS)}] {title} ({bvid})")

        subtitle_result = bilibili.fetch_subtitles(bvid=bvid, cookie_string=BILI_COOKIE)

        if subtitle_result.get("success"):
            subtitle_count = subtitle_result.get("subtitle_count", 0)
            subtitle_language = subtitle_result.get("subtitle_language", "")
            subtitle_text = subtitle_result.get("subtitle_text", "")
            print(f"    ✓ 字幕获取成功: {subtitle_count} 条 ({subtitle_language}), {len(subtitle_text)} 字符")
            print(f"    📝 前100字: {subtitle_text[:100].replace(chr(10), ' ')}...")
            subtitle_success_count += 1
            subtitle_results[bvid] = subtitle_result
        else:
            error_message = subtitle_result.get("error", "未知错误")
            print(f"    ✗ 字幕获取失败: {error_message}")
            subtitle_fail_count += 1
            subtitle_results[bvid] = subtitle_result

        if idx < min(len(videos), MAX_VIDEOS):
            time.sleep(0.5)

    step2_elapsed = time.time() - step2_start
    print(f"\n  字幕提取完成 (耗时 {step2_elapsed:.1f}s): 成功 {subtitle_success_count} / 失败 {subtitle_fail_count}")

    # Step 3: 为每个视频抓取评论（sort=2 按热度排序）
    step3_start = time.time()
    print(f"\n[Step 3] 抓取 {min(len(videos), MAX_VIDEOS)} 个视频的评论...\n")
    all_results = []

    for idx, video in enumerate(videos[:MAX_VIDEOS], 1):
        bvid = video.get("bvid", "")
        aid = video.get("aid", 0)
        title = video.get("title", "")[:50]
        like_count = video.get("like_count", 0)

        print(f"  {'=' * 55}")
        print(f"  [{idx}/{min(len(videos), MAX_VIDEOS)}] [{like_count} 赞] {title}")
        print(f"  {'=' * 55}")

        comment_result = bilibili.fetch_comments_for_video(
            bvid=bvid,
            aid=int(aid) if aid else 0,
            max_pages=MAX_PAGES,  # 抓取 MAX_PAGES 页评论
            sort=1,  # 1 = 按点赞数排序（sort=2 是热度模式，仅返回3条热评）
            cookie_string=BILI_COOKIE,  # 传入 Cookie 才能获取更多评论
        )

        all_comments = comment_result.get("comments", [])
        all_comments.sort(key=lambda comment: comment.get("like_count", 0), reverse=True)
        comments = all_comments[:MAX_COMMENTS]

        video_title = comment_result.get("video_title", title)
        print(f"  标题: {video_title}")
        print(f"  评论数: {len(comments)}\n")

        for cidx, comment in enumerate(comments[:10], 1):
            author = comment.get("author", "匿名")
            content = comment.get("content", "")[:80].replace("\n", " ")
            likes = comment.get("like_count", 0)
            print(f"    {cidx:>3}. {content}")
            print(f"         by {author} | 赞 {likes}")

        if len(comments) > 10:
            print(f"\n    ... 还有 {len(comments) - 10} 条评论")

        # 合并字幕数据到结果中
        video_subtitle = subtitle_results.get(bvid, {})
        all_results.append({
            "bvid": bvid,
            "aid": aid,
            "video_title": video_title,
            "video_url": video.get("url", ""),
            "author": video.get("author", ""),
            "like_count": like_count,
            "subtitle_success": video_subtitle.get("success", False),
            "subtitle_text": video_subtitle.get("subtitle_text", ""),
            "subtitle_count": video_subtitle.get("subtitle_count", 0),
            "subtitle_language": video_subtitle.get("subtitle_language", ""),
            "comments": comments,
            "comment_count": len(comments),
        })

        if idx < min(len(videos), MAX_VIDEOS):
            print(f"\n  等待 2s 后继续下一个视频...")
            time.sleep(2)

    step3_elapsed = time.time() - step3_start

    # 保存结果
    output_dir = os.path.join(script_dir, "output", "json")
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    
    # 根据模式选择文件名
    if use_url_mode:
        output_path = os.path.join(output_dir, f"bili_url_analysis_{timestamp}.json")
    else:
        output_path = os.path.join(output_dir, f"bili_{KEYWORDS}_{timestamp}.json")

    with open(output_path, "w", encoding="utf-8") as output_file:
        json.dump(all_results, output_file, ensure_ascii=False, indent=2)

    # Step 4: 生成爆款分析报告
    step4_start = time.time()
    print(f"\n[Step 4] 生成爆款分析报告...\n")

    from generate_report import generate_and_save_report
    report_path = generate_and_save_report(output_path, output_dir=os.path.join(script_dir, "output", "report"))
    step4_elapsed = time.time() - step4_start
    print(f"  ✅ 报告已生成: {report_path} (耗时 {step4_elapsed:.1f}s)")

    total_elapsed = time.time() - total_start_time
    total_comments = sum(item["comment_count"] for item in all_results)
    total_subtitles = sum(1 for item in all_results if item["subtitle_success"])

    print(f"\n{'=' * 60}")
    print(f"  ✅ 全部完成！")
    print(f"  📊 视频: {len(all_results)} 个")
    print(f"  📝 字幕: {total_subtitles}/{len(all_results)} 个视频成功提取")
    print(f"  💬 评论: {total_comments} 条")
    print(f"  💾 数据文件: {output_path}")
    print(f"  📄 分析报告: {report_path}")
    print(f"  ⏱️  耗时统计:")
    print(f"     Step 1 搜索:   {step1_elapsed:.1f}s")
    print(f"     Step 2 字幕:   {step2_elapsed:.1f}s")
    print(f"     Step 3 评论:   {step3_elapsed:.1f}s")
    print(f"     Step 4 报告:   {step4_elapsed:.1f}s")
    print(f"     总耗时:        {total_elapsed:.1f}s")
    print(f"{'=' * 60}")