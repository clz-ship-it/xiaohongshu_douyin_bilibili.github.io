# -*- coding: utf-8 -*-
"""
抖音爆款拆解器 - 主入口脚本
搜索 → 下载视频 → 转录 → 抓评论 → 保存数据（供AI分析）
"""

import json
import sys
import io
from datetime import datetime
from pathlib import Path

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# =====================================================
# 配置区：请在这里填入你的抖音 Cookie 和搜索关键词
# =====================================================
KEYWORDS = "openclaw"  # 搜索关键词
VIDEO_URLS = []  # URL 直接分析模式：填入抖音视频 URL 列表，非空时跳过搜索
# 示例: VIDEO_URLS = ["https://www.douyin.com/video/7615202845574302986"]
MAX_VIDEOS = 10  # 最多分析多少个视频（减少数量降低反爬风险）
MAX_COMMENTS = 30  # 每个视频抓取多少条评论

# 抖音 Cookie（从浏览器开发者工具复制）
# 获取方式：打开抖音网页版 → F12 → Application → Cookies → 复制所有 Cookie
DOUYIN_COOKIE = ""  # 请填入你的抖音 Cookie（获取方式：打开抖音网页版 → F12 → Application → Cookies → 复制全部）
# =====================================================

sys.path.insert(0, str(Path(__file__).parent))

from douyin_api import search_with_driver, fetch_comments_with_driver
from downloader import init_browser, download_douyin_with_driver, download_douyin
from transcriber import process_video
from subtitle_extractor import try_extract_subtitles
from generate_report import generate_and_save_report
from html_structure_detector import detect_and_report, HTMLStructureDetector

OUTPUT_DIR = Path(__file__).parent / "output" / ("url_analysis" if VIDEO_URLS else KEYWORDS)


def run():
    """抖音爆款拆解器主流程"""
    print("=" * 70)
    print(f"  🎵 抖音爆款拆解器")
    print(f"  关键词：{KEYWORDS}")
    print(f"  视频数：{MAX_VIDEOS} | 每视频评论数：{MAX_COMMENTS}")
    print("=" * 70)

    if not DOUYIN_COOKIE:
        print("\n  ✗ 错误：请先在配置区填入抖音 Cookie")
        print("  获取方式：打开抖音网页版 → F12 → Application → Cookies → 复制所有 Cookie")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Step 0: HTML 结构检测（可选，用于检测抖音页面结构变化）
    print(f"\n[Step 0] 检测抖音 HTML 结构变化...")
    try:
        # 使用第一个视频 URL 进行检测（如果有历史记录）
        detector = HTMLStructureDetector(cookie_string=DOUYIN_COOKIE)
        
        # 检测搜索页面
        print(f"  - 检测搜索页面结构...")
        detector.detect_search_page(KEYWORDS)
        
        # 生成报告
        report_path = detector.save_report(OUTPUT_DIR / "structure_reports")
        print(f"  ✓ 结构检测报告：{report_path}")
        
        # 对比历史并显示变化
        changes = detector.compare_with_history()
        if changes:
            print(f"  ⚠️  检测到 {len(changes)} 处结构变化，请查看报告")
            for change in changes[:3]:  # 只显示前 3 个
                severity = change.get('severity', 'unknown')
                change_type = change.get('type', '')
                print(f"     - [{severity.upper()}] {change_type}")
            if len(changes) > 3:
                print(f"     ... 还有 {len(changes) - 3} 处变化")
        else:
            print(f"  ✓ 未检测到明显结构变化")
        
        # 更新历史记录
        detector.update_history()
        detector.close()
        
    except Exception as detect_error:
        print(f"  ⚠️  结构检测失败：{detect_error}（继续执行主流程）")

    # 初始化浏览器（只登录一次，全程复用）
    print(f"\n[Step 1] 初始化浏览器并登录...")
    driver = init_browser(DOUYIN_COOKIE)
    print(f"  ✓ 浏览器初始化完成，Cookie 已注入")

    # Step 2: 搜索或 URL 模式（复用浏览器）
    if VIDEO_URLS:
        # URL 直接分析模式
        print(f"\n[Step 2] URL 直接分析模式：共 {len(VIDEO_URLS)} 个视频")
        import re
        videos = []
        for url in VIDEO_URLS:
            # 从 URL 中提取 video_id
            match = re.search(r"/video/(\d+)", url)
            if not match:
                print(f"  ⚠️  跳过无效 URL：{url}")
                continue
            video_id = match.group(1)
            video_info = {
                "title": video_id,  # 暂时使用 video_id 作为 title
                "author": "",
                "url": url,
                "video_id": video_id,
                "like_count": 0,
                "comment_count": 0,
                "share_count": 0,
                "collect_count": 0,
                "play_count": 0,
            }
            videos.append(video_info)
        if not videos:
            print("  ✗ 未找到有效视频 URL")
            driver.quit()
            return
        print(f"  ✓ 找到 {len(videos)} 个视频")
    else:
        # 关键词搜索模式
        print(f"\n[Step 2] 搜索抖音关键词：{KEYWORDS}")
        search_result = search_with_driver(driver, KEYWORDS, page_size=MAX_VIDEOS)
        videos = search_result.get("items", [])
        if not videos:
            print("  ✗ 未找到视频")
            driver.quit()
            return

        print(f"  ✓ 找到 {len(videos)} 条高赞视频")
    for idx, video in enumerate(videos, 1):
        if VIDEO_URLS:
            print(f"    {idx}. {video.get('url', '')}")
        else:
            print(f"    {idx}. [{video.get('like_count', 0)} 赞] {video.get('title', '')[:50]}")

    # Step 3-5: 对每个视频执行 下载→转录→评论（复用浏览器实例）
    all_results = []

    for idx, video in enumerate(videos, 1):
        video_id = video.get("video_id", "")
        title = video.get("title", "")
        video_url = video.get("url", "")

        print(f"\n{'─' * 60}")
        print(f"  [{idx}/{len(videos)}] {title[:50]}")
        print(f"{'─' * 60}")

        video_dir = OUTPUT_DIR / f"video_{idx}_{video_id}"
        video_dir.mkdir(parents=True, exist_ok=True)

        video_info = {
            "title": title,
            "author": video.get("author", ""),
            "url": video_url,
            "video_id": video_id,
            "like_count": video.get("like_count", 0),
            "comment_count": video.get("comment_count", 0),
            "share_count": video.get("share_count", 0),
            "collect_count": video.get("collect_count", 0),
            "play_count": video.get("play_count", 0),
        }

        # 下载视频（复用浏览器实例）
        print(f"\n  [2] 下载视频并转录...")
        video_path = download_douyin_with_driver(driver, video_url, video_dir)

        transcript_text = ""
        if video_path:
            transcript_result = process_video(video_dir)
            if transcript_result.get("success"):
                transcript_text = transcript_result.get("transcript", "")
                print(f"    ✓ 转录完成，字数：{len(transcript_text)}")

                # 删除视频文件节省空间
                try:
                    video_path.unlink()
                    print(f"    ✓ 已删除视频文件")
                except Exception:
                    pass
            else:
                print(f"    ✗ 转录失败：{transcript_result.get('error', '')}")
        else:
            print("    ✗ 视频下载失败")

        # Step 3: 抓取评论（复用浏览器）
        print(f"\n  [3] 抓取 {MAX_COMMENTS} 条高赞评论...")
        comments = fetch_comments_with_driver(driver, video_url, max_comments=MAX_COMMENTS)
        print(f"    ✓ 获取 {len(comments)} 条评论")

        for comment_idx, comment in enumerate(comments[:5], 1):
            content = comment.get("content", "")[:50].replace("\n", " ")
            print(f"      {comment_idx}. [{comment.get('like_count', 0)} 赞] {content}")
        if len(comments) > 5:
            print(f"      ... 还有 {len(comments) - 5} 条评论")

        # 保存单个视频数据
        video_result = {
            "video_info": video_info,
            "transcript": transcript_text,
            "comments": comments,
        }
        all_results.append(video_result)

        single_path = video_dir / "data.json"
        with open(single_path, "w", encoding="utf-8") as output_file:
            json.dump(video_result, output_file, ensure_ascii=False, indent=2)

    # 关闭浏览器
    print(f"\n[Step 6] 关闭浏览器...")
    try:
        driver.quit()
        print(f"  ✓ 浏览器已关闭")
    except Exception:
        pass

    # Step 7: 保存汇总数据
    summary = {
        "keyword": KEYWORDS,
        "platform": "douyin",
        "total_videos": len(all_results),
        "max_comments_per_video": MAX_COMMENTS,
        "generated_at": datetime.now().isoformat(),
        "videos": all_results,
    }

    results_path = OUTPUT_DIR / "results.json"
    with open(results_path, "w", encoding="utf-8") as output_file:
        json.dump(summary, output_file, ensure_ascii=False, indent=2)

    # Step 8: 生成分析报告
    print(f"\n[Step 7] 生成爆款分析报告...")
    try:
        report_path = generate_and_save_report(str(results_path), str(OUTPUT_DIR))
        print(f"  ✓ 报告已生成：{report_path}")
    except Exception as report_error:
        print(f"  ✗ 报告生成失败：{report_error}")
        report_path = None

    print(f"\n{'=' * 70}")
    print(f"  ✅ 抖音爆款拆解全流程完成！")
    if VIDEO_URLS:
        print(f"  模式：URL 直接分析")
    else:
        print(f"  关键词：{KEYWORDS}")
    print(f"  视频数：{len(all_results)}")
    print(f"  数据保存：{results_path}")
    if report_path:
        print(f"  分析报告：{report_path}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    run()