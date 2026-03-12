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
DOUYIN_COOKIE = "enter_pc_once=1; UIFID_TEMP=1095a6dff7695ad7d7bcf6d11c9f5d2a106aea3524d1e5d99f3ea5d6bdd896178c5bde004efde2f5cffad85b6cd6ff15f6f560b88a9ee909a718522ad4a95ac9bf831f29c309470f71f58c70bb65c8c136b178d91bbd5671e1dd4bb0cd6e5c46c3ea142c09986f2cbbda507f5a565f22; s_v_web_id=verify_mminfg7l_bgcXyFGA_tMXH_4aMH_B4fV_9Un52dW2JdLJ; hevc_supported=true; my_rd=2; fpk1=U2FsdGVkX1+xsECEOSteeJ6YUgRq0pOe0thicwkKMmB9doEqziJ7wWOjgOtHvakG1nb5Dhjm19cP7wzfknc5/Q==; fpk2=7c73ef5b8d3235ae0606f2e84e457ff5; bd_ticket_guard_client_web_domain=2; passport_csrf_token=7c1dfa4cbe60cb58b35d8ec88c0e2c07; passport_csrf_token_default=7c1dfa4cbe60cb58b35d8ec88c0e2c07; is_staff_user=false; __security_server_data_status=1; UIFID=1095a6dff7695ad7d7bcf6d11c9f5d2a106aea3524d1e5d99f3ea5d6bdd896178c5bde004efde2f5cffad85b6cd6ff15f6f560b88a9ee909a718522ad4a95ac990296f020010ce8fdbf7a34ea790073ca741bcafa2560e4271f04389f1c21438e57c643ccb7dc53fd353673cbf2e85c423e4b90cd85ae8111cfe03737334f042a9dd71c05102d55f727c8fe161b84db8c5bdec0b95215b8e28ef795568346cb2a3b9b560c6e08718054da57ccf0203a8; publish_badge_show_info=%221%2C0%2C0%2C1773043433451%22; SEARCH_RESULT_LIST_TYPE=%22single%22; is_dash_user=1; volume_info=%7B%22isUserMute%22%3Afalse%2C%22isMute%22%3Afalse%2C%22volume%22%3A0.5%7D; passport_auth_status=b2fd36951200fc75b6511f0ad0c6cbb9%2C4eef16b1c8d9bd89b8d477bdc86f8d6b; passport_auth_status_ss=b2fd36951200fc75b6511f0ad0c6cbb9%2C4eef16b1c8d9bd89b8d477bdc86f8d6b; FOLLOW_LIVE_POINT_INFO=%22MS4wLjABAAAA2U9OF7Io2RBFHwv7R18ejuTOx4aFAoRONCC8YQRWYVU-IHmP5Fjh2E3dX8gonXsW%2F1773158400000%2F0%2F1773144197958%2F0%22; dy_swidth=1280; dy_sheight=800; passport_mfa_token=CjXtl16orniOxfvsjv3oB4UnMdY%2BxGPRT4GGvN3cACYF0eCdpu3V73qbZRWnS9EL7ceRUW38rRpKCjwAAAAAAAAAAAAAUCurlAwG5jzYi4BJAmjFi3YljKUxIiv5tTRi6ajlJkeLwWbaDWyVqwIc434pvgbXzJcQieaLDhj2sdFsIAIiAQM2TJNv; d_ticket=99aa9ae6b1d4c53defd98f73314d57166c37b; SelfTabRedDotControl=%5B%7B%22id%22%3A%227333932749230704694%22%2C%22u%22%3A332%2C%22c%22%3A0%7D%2C%7B%22id%22%3A%227568800446595565606%22%2C%22u%22%3A385%2C%22c%22%3A0%7D%2C%7B%22id%22%3A%227479760741633886247%22%2C%22u%22%3A33%2C%22c%22%3A0%7D%2C%7B%22id%22%3A%227589108197408016426%22%2C%22u%22%3A28%2C%22c%22%3A0%7D%2C%7B%22id%22%3A%227588599788099078159%22%2C%22u%22%3A3%2C%22c%22%3A0%7D%2C%7B%22id%22%3A%227431176122497009676%22%2C%22u%22%3A100%2C%22c%22%3A0%7D%5D; playRecommendGuideTagCount=2; totalRecommendGuideTagCount=2; download_guide=%222%2F20260311%2F0%22; passport_assist_user=CkEfzPhX7DJ3ibxwvMm9mjewtF2j01py798HUBcb7953My7hSz9KyhPcAv7sOZQRhCcrplWO1h9y5sq0AQz9xDa9oBpKCjwAAAAAAAAAAAAAUCvtwK-nQKyV5n-GLACCGKb84hUGcqie0LXTNNGNumBxRYr04GXODt5Ar82xwAOQ-1kQy-aLDhiJr9ZUIAEiAQN0LSzs; n_mh=u4ouUiQkslW-wd1qgsZLm7gevbDYo4kFtePJPCyefuI; sid_guard=c61e3962479406670b6e82664131ea24%7C1773218200%7C5184000%7CSun%2C+10-May-2026+08%3A36%3A40+GMT; uid_tt=59104c434cccdc47940a5a38d7bf1aa7; uid_tt_ss=59104c434cccdc47940a5a38d7bf1aa7; sid_tt=c61e3962479406670b6e82664131ea24; sessionid=c61e3962479406670b6e82664131ea24; sessionid_ss=c61e3962479406670b6e82664131ea24; session_tlb_tag=sttt%7C10%7Cxh45YkeUBmcLboJmQTHqJP________-lJ1qdOgYpMK4tAsc7IndxPmqjmWDjRdLfA6h_DbFEkQQ%3D; sid_ucp_v1=1.0.0-KDhiYmNhYTEwYTE5NDViNjM2NWE0MmU4MWE0NTIxOGI3MmQ5MWRkNGMKIQiL_NCX8czmBhCY08TNBhjvMSAMMN_fxKsGOAdA9AdIBBoCbGYiIGM2MWUzOTYyNDc5NDA2NjcwYjZlODI2NjQxMzFlYTI0; ssid_ucp_v1=1.0.0-KDhiYmNhYTEwYTE5NDViNjM2NWE0MmU4MWE0NTIxOGI3MmQ5MWRkNGMKIQiL_NCX8czmBhCY08TNBhjvMSAMMN_fxKsGOAdA9AdIBBoCbGYiIGM2MWUzOTYyNDc5NDA2NjcwYjZlODI2NjQxMzFlYTI0; _bd_ticket_crypt_cookie=3ae94295cf69df0399f1dcdb7b214d34; __security_mc_1_s_sdk_sign_data_key_web_protect=e1a49b13-4a7d-8c9e; __security_mc_1_s_sdk_cert_key=0627f87a-4e36-af36; __security_mc_1_s_sdk_crypt_sdk=6ab78ec8-4952-99ad; login_time=1773218201587; ttwid=1%7Cj4sggxjTs2hOLECNkfNe4zUptZLo9X3Xp4o-J6R-fjI%7C1773218206%7Caa3a0cf58d5fe12a73c86681e7040312eb50fd7abdb53808b0645bc77c8fc432; __ac_nonce=069b22c28003108a3106d; __ac_signature=_02B4Z6wo00f01.FMbYgAAIDCpctNz1onlZ.xbGkAAJXq25; stream_recommend_feed_params=%22%7B%5C%22cookie_enabled%5C%22%3Atrue%2C%5C%22screen_width%5C%22%3A1280%2C%5C%22screen_height%5C%22%3A800%2C%5C%22browser_online%5C%22%3Atrue%2C%5C%22cpu_core_num%5C%22%3A22%2C%5C%22device_memory%5C%22%3A8%2C%5C%22downlink%5C%22%3A10%2C%5C%22effective_type%5C%22%3A%5C%224g%5C%22%2C%5C%22round_trip_time%5C%22%3A100%7D%22; FOLLOW_NUMBER_YELLOW_POINT_INFO=%22MS4wLjABAAAA2U9OF7Io2RBFHwv7R18ejuTOx4aFAoRONCC8YQRWYVU-IHmP5Fjh2E3dX8gonXsW%2F1773331200000%2F0%2F1773284397858%2F0%22; IsDouyinActive=true; home_can_add_dy_2_desktop=%220%22; odin_tt=1fe8fb0792ccef4e806806b4e4ef882c7925e5dd03c12e8cdf076453b588472a804131f4ced2733b817a41b16e9c7ead6c4ddda61f2ff22aadc7a319b93a6ff1; bd_ticket_guard_client_data=eyJiZC10aWNrZXQtZ3VhcmQtdmVyc2lvbiI6MiwiYmQtdGlja2V0LWd1YXJkLWl0ZXJhdGlvbi12ZXJzaW9uIjoxLCJiZC10aWNrZXQtZ3VhcmQtcmVlLXB1YmxpYy1rZXkiOiJCR2JSTS9kY1daU0NNNlRzUk5wckcvd2t3djk1bk16L2JQQW1HTnlKc3BOS3NIOE51MHhhWjNtZU1BeFlKRVl4TGUrVXU3S0M4V1VuODhXVWRMYVl5SU09IiwiYmQtdGlja2V0LWd1YXJkLXdlYi12ZXJzaW9uIjoyfQ%3D%3D; bd_ticket_guard_client_data_v2=eyJyZWVfcHVibGljX2tleSI6IkJHYlJNL2RjV1pTQ002VHNSTnByRy93a3d2OTVuTXovYlBBbUdOeUpzcE5Lc0g4TnUweGFaM21lTUF4WUpFWXhMZStVdTdLQzhXVW44OFdVZExhWXlJTT0iLCJ0c19zaWduIjoidHMuMi43NWFmOWFhNGQ1NTBlODY4NDFkNDE1ZDlhNDUyZDk5YjI2YWI4OTcwMjc1NGE4YjdhZjIyM2RiYmNlZDk5YzAxYzRmYmU4N2QyMzE5Y2YwNTMxODYyNGNlZGExNDkxMWNhNDA2ZGVkYmViZWRkYjJlMzBmY2U4ZDRmYTAyNTc1ZCIsInJlcV9jb250ZW50Ijoic2VjX3RzIiwicmVxX3NpZ24iOiJnMEl0K2FVcXVDRkFhUkRoVEpVVFhsQ3AxY0JNSVR1WTRaNjM1MXQyUTE4PSIsInNlY190cyI6IiM2VzZqaWc1SStZdU1EWjAwZ3MybFlPMlFYVTZLaStUcnFzR2dJNGNWck1RK3pkZ0l0eUhMOXU2cHB5OVYifQ%3D%3D"
# =====================================================

sys.path.insert(0, str(Path(__file__).parent))

from douyin_api import search_with_driver, fetch_comments_with_driver
from downloader import init_browser, download_douyin_with_driver, download_douyin
from transcriber import process_video
from subtitle_extractor import try_extract_subtitles
from generate_report import generate_and_save_report
from html_structure_detector import detect_and_report, HTMLStructureDetector
from cookie_helper import get_cookie_or_login

OUTPUT_DIR = Path(__file__).parent / "output" / ("url_analysis" if VIDEO_URLS else KEYWORDS)


def run():
    """抖音爆款拆解器主流程"""
    print("=" * 70)
    print(f"  🎵 抖音爆款拆解器")
    print(f"  关键词：{KEYWORDS}")
    print(f"  视频数：{MAX_VIDEOS} | 每视频评论数：{MAX_COMMENTS}")
    print("=" * 70)

    # Step 0: 获取 Cookie（优先配置区 → 缓存 → 弹出浏览器登录）
    print(f"\n[Step 0] 获取 Cookie...")
    cookie_string = get_cookie_or_login("douyin", DOUYIN_COOKIE)
    if not cookie_string:
        print("\n  ✗ 错误：未能获取抖音 Cookie，无法继续")
        return
    # 更新全局变量供后续使用
    global DOUYIN_COOKIE
    DOUYIN_COOKIE = cookie_string

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