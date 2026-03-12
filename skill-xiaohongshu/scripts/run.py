# -*- coding: utf-8 -*-
"""
小红书爆款拆解器 - 主入口脚本
搜索 → 判断图文/视频 → 下载视频或提取图文 → 转录 → 抓评论 → 保存数据（供AI分析）
"""

import json
import sys
import io
import time
from datetime import datetime
from pathlib import Path

# 修复 Windows 控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ========== 配置区（由 AI 根据用户输入修改） ==========
KEYWORDS = "openclaw"
NOTE_URLS = []  # URL 直接分析模式：填入小红书笔记 URL 列表，非空时跳过搜索
# 示例: NOTE_URLS = ["https://www.xiaohongshu.com/explore/6xxx"]
MAX_NOTES = 10
MAX_COMMENTS = 30
XHS_COOKIE = ""  # 请填入你的小红书 Cookie（获取方式：打开 xiaohongshu.com → F12 → Application → Cookies → 复制全部）
# =====================================================

sys.path.insert(0, str(Path(__file__).parent))

from xhs_api import (
    search, fetch_note_content, fetch_comments, create_browser,
    _navigate_to_detail_page, _extract_content_from_detail_page, _extract_comments_from_detail_page,
    _go_back_to_search, find_and_click_next_note,
    extract_video_src_from_detail_page,
)
from downloader import download_xiaohongshu, download_video_by_url
from transcriber import process_video
from subtitle_extractor import try_extract_subtitles
import random
import re

OUTPUT_DIR = Path(__file__).parent / "output" / (KEYWORDS if not NOTE_URLS else "url_analysis")


def run():
    """小红书爆款拆解器主流程"""
    print("=" * 70)
    print(f"  📕 小红书爆款拆解器")
    print(f"  关键词: {KEYWORDS}")
    print(f"  笔记数: {MAX_NOTES} | 每笔记评论数: {MAX_COMMENTS}")
    print("=" * 70)

    if not XHS_COOKIE:
        print("\n  ✗ 错误：请先在配置区填入小红书 Cookie")
        print("  获取方式：打开小红书网页版 → F12 → Application → Cookies → 复制所有 Cookie")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 创建共享浏览器实例（避免反复创建触发反爬）
    print(f"\n[Step 0] 初始化浏览器...")
    driver = create_browser(cookie_string=XHS_COOKIE)
    print(f"  ✓ 浏览器已就绪（全程复用同一实例）")

    try:
        _run_with_driver(driver)
    finally:
        driver.quit()
        print(f"\n  ✓ 浏览器已关闭")

def _run_with_driver(driver):
    """使用共享浏览器执行采集流程"""
    # Step 1: 搜索或 URL 直接分析
    if NOTE_URLS:
        print(f"\n[Step 1] URL 直接分析模式: {len(NOTE_URLS)} 个笔记")
        notes = []
        for url in NOTE_URLS:
            # 从 URL 中提取 note_id（匹配最后一段路径）
            note_id = re.search(r'/([^/]+)$', url)
            if note_id:
                note_id = note_id.group(1)
                # 构造与搜索结果格式一致的 note 字典
                notes.append({
                    "note_id": note_id,
                    "url": url,
                    "title": f"笔记 {note_id[:8]}...",  # 初始占位标题，后续会更新
                    "author": "",
                    "like_count": 0,
                    "is_video": False,  # 初始假设，后续会更新
                    "detail": {}
                })
                print(f"    ✓ 已添加: {url}")
            else:
                print(f"    ✗ 无效 URL: {url}")
        
        if not notes:
            print("  ✗ 未找到有效的笔记 URL")
            return
    else:
        print(f"\n[Step 1] 搜索小红书关键词: {KEYWORDS}")
        search_result = search(KEYWORDS, page_size=MAX_NOTES, cookie_string=XHS_COOKIE, driver=driver)
        notes = search_result.get("items", [])
        if not notes:
            print("  ✗ 未找到笔记")
            return

        print(f"  ✓ 找到 {len(notes)} 条高赞笔记")
        for idx, note in enumerate(notes, 1):
            content_type_label = "📹视频" if note.get("is_video") else "📝图文"
            print(f"    {idx}. [{note.get('like_count', 0)} 赞] [{content_type_label}] {note.get('title', '')[:40]}")

    # 构造搜索结果页 URL（用于 404 恢复）
    search_url = f"https://www.xiaohongshu.com/search_result?keyword={KEYWORDS}&source=web_search_result_notes"

    # Step 2-4: 在搜索结果页上按顺序逐个点击卡片，提取详情
    # 核心策略：不按排序后的列表查找特定 note_id，而是按页面上卡片出现顺序逐个点击
    # 原因：小红书搜索结果页是瀑布流懒加载，返回后页面重新渲染，之前滚动加载的卡片不在 DOM 中
    all_results = []
    processed_note_ids = set()
    # 构建 note_id -> 搜索结果数据 的映射，用于合并搜索阶段已获取的信息
    search_notes_map = {note.get("note_id", ""): note for note in notes}

    consecutive_failures = 0
    for idx in range(1, MAX_NOTES + 1):
        print(f"\n{'─' * 60}")
        print(f"  [{idx}/{MAX_NOTES}] 查找并点击下一条笔记...")
        print(f"{'─' * 60}")

        # 在搜索结果页找到下一个未处理的卡片并点击进入详情页
        try:
            clicked_note_id = find_and_click_next_note(driver, processed_note_ids)
        except Exception as click_err:
            print(f"    ✗ 查找笔记卡片异常: {click_err}")
            consecutive_failures += 1
            if consecutive_failures >= 3:
                print(f"    ⚠️ 连续 {consecutive_failures} 次失败，停止采集")
                break
            # 尝试恢复：切回可用窗口，重新导航到搜索页
            try:
                remaining = driver.window_handles
                if remaining:
                    driver.switch_to.window(remaining[0])
                driver.get(search_url)
                time.sleep(4)
            except Exception:
                print(f"    ⚠️ 浏览器无法恢复，停止采集")
                break
            continue

        if not clicked_note_id:
            print(f"    ⚠️ 没有更多可点击的笔记卡片，已处理 {len(all_results)} 条")
            break

        consecutive_failures = 0
        processed_note_ids.add(clicked_note_id)

        # 合并搜索阶段已获取的数据（如果有）
        search_note = search_notes_map.get(clicked_note_id, {})
        search_detail = search_note.get("detail", {})
        is_video = search_note.get("is_video", False)

        # 提取详情页正文和互动数据
        print(f"\n  [2] 提取详情页内容...")
        detail_content = _extract_content_from_detail_page(driver)
        title = detail_content.get("title", "") or search_note.get("title", f"笔记 {clicked_note_id[:8]}...")

        note_info = {
            "title": title,
            "author": detail_content.get("author", "") or search_note.get("author", ""),
            "url": f"https://www.xiaohongshu.com/explore/{clicked_note_id}",
            "note_id": clicked_note_id,
            "like_count": detail_content.get("like_count", 0) or search_note.get("like_count", 0),
            "collect_count": detail_content.get("collect_count", 0),
            "comment_count": detail_content.get("comment_count", 0),
            "share_count": detail_content.get("share_count", 0),
            "is_video": detail_content.get("is_video", is_video),
            "content_type": detail_content.get("content_type", "video" if is_video else "image_text"),
        }

        content_type_label = "📹视频" if note_info["is_video"] else "📝图文"
        print(f"    [{content_type_label}] {title[:40]}")
        print(f"    ✓ {note_info['author']} | 👍{note_info['like_count']} ⭐{note_info['collect_count']} 💬{note_info['comment_count']}")

        note_dir = OUTPUT_DIR / f"note_{idx}_{clicked_note_id}"
        note_dir.mkdir(parents=True, exist_ok=True)

        # 提取正文
        transcript_text = ""
        note_text_content = detail_content.get("content", "")
        if note_text_content:
            print(f"    ✓ 提取正文完成，字数: {len(note_text_content)}")
            content_path = note_dir / "content.txt"
            with open(content_path, "w", encoding="utf-8") as content_file:
                content_file.write(f"标题：{title}\n\n正文：\n{note_text_content}")
        else:
            print("    ℹ️ 未能提取到正文内容")

        # 视频处理：如果是视频笔记，提取视频地址 → 下载 → 字幕检测 → 转录
        if note_info["is_video"]:
            print(f"\n  [2.5] 视频笔记处理...")
            note_url = note_info["url"]

            # Step 1: 从当前详情页 DOM 提取视频地址（不创建新浏览器）
            video_src = extract_video_src_from_detail_page(driver)
            if video_src:
                # Step 2: 下载视频
                video_path = download_video_by_url(video_src, note_dir, cookie_string=XHS_COOKIE)
                if video_path:
                    # Step 3: 尝试字幕检测（不下载视频，仅提取字幕）
                    print(f"    尝试提取字幕...")
                    subtitle_result = try_extract_subtitles(
                        note_url, note_dir,
                        platform="xiaohongshu", cookie_string=XHS_COOKIE
                    )
                    if subtitle_result.get("success"):
                        transcript_text = subtitle_result.get("subtitle_text", "")
                        print(f"    ✓ 字幕提取成功（{subtitle_result.get('subtitle_type', 'unknown')}），字数: {len(transcript_text)}")
                    else:
                        # Step 4: 没有字幕，走 Whisper 转录
                        print(f"    ℹ️ 无可用字幕，启动 Whisper 转录...")
                        transcribe_result = process_video(note_dir, skip_vocal_separation=True)
                        if transcribe_result.get("success"):
                            transcript_text = transcribe_result.get("transcript", "")
                            print(f"    ✓ Whisper 转录完成，字数: {len(transcript_text)}")
                        else:
                            print(f"    ✗ 转录失败: {transcribe_result.get('error', '未知错误')}")

                    # 保存转录文本
                    if transcript_text:
                        transcript_path = note_dir / "transcript.txt"
                        with open(transcript_path, "w", encoding="utf-8") as transcript_file:
                            transcript_file.write(f"标题：{title}\n\n口播转录：\n{transcript_text}")
            else:
                print(f"    ⚠️ 未能从详情页提取到视频地址，跳过视频处理")

        # 提取评论（当前已在详情页）
        print(f"  [3] 提取评论...")
        comments = _extract_comments_from_detail_page(driver, MAX_COMMENTS)
        if comments:
            print(f"    ✓ 获取 {len(comments)} 条评论")
            for comment_idx, comment in enumerate(comments[:5], 1):
                content = comment.get("content", "")[:50].replace("\n", " ")
                print(f"      {comment_idx}. [{comment.get('like_count', 0)} 赞] {content}")
            if len(comments) > 5:
                print(f"      ... 还有 {len(comments) - 5} 条评论")
        else:
            print(f"    ℹ️ 未能获取评论")

        # 返回搜索结果页
        _go_back_to_search(driver, search_url)

        # 保存单条笔记数据
        note_result = {
            "note_info": note_info,
            "transcript": transcript_text,
            "text_content": note_text_content,
            "comments": comments,
        }
        all_results.append(note_result)

        single_path = note_dir / "data.json"
        with open(single_path, "w", encoding="utf-8") as output_file:
            json.dump(note_result, output_file, ensure_ascii=False, indent=2)

        # 笔记间随机延迟
        delay = random.uniform(1, 2)
        print(f"    ⏳ 等待 {delay:.1f}s 后继续...")
        time.sleep(delay)

    # Step 5: 保存汇总数据
    video_count = sum(1 for r in all_results if r["note_info"].get("is_video"))
    image_text_count = len(all_results) - video_count

    summary = {
        "keyword": KEYWORDS,
        "platform": "xiaohongshu",
        "total_notes": len(all_results),
        "video_count": video_count,
        "image_text_count": image_text_count,
        "max_comments_per_note": MAX_COMMENTS,
        "generated_at": datetime.now().isoformat(),
        "notes": all_results,
    }

    results_path = OUTPUT_DIR / "results.json"
    with open(results_path, "w", encoding="utf-8") as output_file:
        json.dump(summary, output_file, ensure_ascii=False, indent=2)

    # Step 6: 生成爆款分析报告
    print(f"\n[Step 6] 生成爆款分析报告...")
    try:
        from generate_report import generate_and_save_report
        report_path = generate_and_save_report(str(results_path))
        print(f"  ✅ 报告已生成: {report_path}")
    except Exception as e:
        print(f"  ⚠️ 报告生成失败: {e}")

    print(f"\n{'=' * 70}")
    print(f"  ✅ 小红书爆款拆解数据采集完成！")
    print(f"  关键词: {KEYWORDS}")
    print(f"  笔记数: {len(all_results)}（📹视频 {video_count} + 📝图文 {image_text_count}）")
    print(f"  数据文件: {results_path}")
    if 'report_path' in locals():
        print(f"  分析报告: {report_path}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    run()
