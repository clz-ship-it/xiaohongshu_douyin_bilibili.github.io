# -*- coding: utf-8 -*-
"""调试脚本：测试 B 站字幕 API，找出字幕获取失败的原因"""

import json
import ssl
from urllib.request import Request, urlopen
from urllib.parse import urlencode

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com",
}

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

COOKIE = "buvid3=D0DEBE11-0650-46BF-55D6-54CB925B3BAD74243infoc; b_nut=1768270974; _uuid=4588CB17-104C1-C3BB-10DB3-8C65F15A58AB78847infoc; buvid_fp=fba512b86de98fd6049cb85502e4cbe4; buvid4=2E0B6F5C-303B-B1BE-8F2B-F4084BBE6DD275071-026011310-6DOAWEMrnULsLgFCAOBpMK3etbBxfSLwL6UC1t6+tjj2/ylVXglFrWEUYlo/P1b3; CURRENT_QUALITY=0; rpdid=0zbeZV53Ww|QmlPeZ|N286h|3w1VIQMu; DedeUserID=2072893542; DedeUserID__ckMd5=3a8d80aeb9b97431; theme-tip-show=SHOWED; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzMyODA5NTMsImlhdCI6MTc3MzAyMTY5MywicGx0IjotMX0.OTm_r6saKd5nfKOaiywSHJ85Bi9lijOGHGd_3nGXui0; bili_ticket_expires=1773280893; home_feed_column=5; SESSDATA=60287840%2C1788662125%2C47ef8%2A31CjA8MwFlN-oydmyPNxMaNgntbIDMWiC2kxW5BB43AiIyeQZ9ONb1SqcNi5JkCExWBFESVnpES09xc2g2c2VibG02Wnp6NTZMQnVPUDlHOWFENDdCdjFuTWJjR1k4T2hUUDNzeWpLU2g1Ukw0eV8zS2s1X3RVRm1GTWpXeXZ0RGFLdVZUOXpuTWlBIIEC; bili_jct=bfebc14a6455650afa367ece53059634; theme-avatar-tip-show=SHOWED; bp_t_offset_2072893542=1177991464936800256; CURRENT_FNVAL=2000; browser_resolution=1799-1282; sid=7a08bulo; b_lsid=D5925458_19CD7B977EE"


def http_get_json(url, params, cookie=None):
    query_string = urlencode(params)
    full_url = f"{url}?{query_string}"
    req = Request(full_url)
    req.add_header("User-Agent", HEADERS["User-Agent"])
    req.add_header("Referer", HEADERS["Referer"])
    if cookie:
        req.add_header("Cookie", cookie)
    resp = urlopen(req, timeout=15, context=SSL_CTX)
    return json.loads(resp.read().decode("utf-8"))


def get_cid(bvid):
    """获取视频的 cid"""
    url = "https://api.bilibili.com/x/web-interface/view"
    data = http_get_json(url, {"bvid": bvid})
    if data.get("code") == 0:
        return data["data"]["cid"]
    return 0


def test_subtitle_apis(bvid):
    """测试多个可能的字幕 API"""
    print(f"\n{'='*60}")
    print(f"测试视频: {bvid}")
    print(f"{'='*60}")

    # 获取 cid
    cid = get_cid(bvid)
    print(f"CID: {cid}")
    if not cid:
        print("无法获取 CID，跳过")
        return

    # API 1: x/player/v2 (正确的字幕 API)
    print(f"\n--- API 1: x/player/v2 (带 Cookie) ---")
    try:
        url1 = "https://api.bilibili.com/x/player/v2"
        data1 = http_get_json(url1, {"bvid": bvid, "cid": cid}, cookie=COOKIE)
        print(f"  code: {data1.get('code')}")
        print(f"  message: {data1.get('message')}")
        if data1.get("code") == 0:
            subtitle_info = data1.get("data", {}).get("subtitle", {})
            subtitles = subtitle_info.get("subtitles", [])
            print(f"  subtitle_info: {json.dumps(subtitle_info, ensure_ascii=False, indent=2)[:500]}")
            print(f"  字幕数量: {len(subtitles)}")
            for s in subtitles:
                print(f"    - {s.get('lan')}: {s.get('lan_doc')} | url: {s.get('subtitle_url', '')[:80]}")
    except Exception as e:
        print(f"  错误: {e}")

    # API 2: x/player/v2 (不带 Cookie)
    print(f"\n--- API 2: x/player/v2 (不带 Cookie) ---")
    try:
        data2 = http_get_json(url1, {"bvid": bvid, "cid": cid}, cookie=None)
        print(f"  code: {data2.get('code')}")
        print(f"  message: {data2.get('message')}")
        if data2.get("code") == 0:
            subtitle_info2 = data2.get("data", {}).get("subtitle", {})
            subtitles2 = subtitle_info2.get("subtitles", [])
            print(f"  字幕数量: {len(subtitles2)}")
            for s in subtitles2:
                print(f"    - {s.get('lan')}: {s.get('lan_doc')} | url: {s.get('subtitle_url', '')[:80]}")
    except Exception as e:
        print(f"  错误: {e}")

    # API 3: x/player/wbi/playurl (当前代码使用的 API - 这是播放地址 API，不是字幕 API)
    print(f"\n--- API 3: x/player/wbi/playurl (当前代码使用的，这是播放地址API) ---")
    try:
        url3 = "https://api.bilibili.com/x/player/wbi/playurl"
        data3 = http_get_json(url3, {"bvid": bvid, "cid": cid}, cookie=COOKIE)
        print(f"  code: {data3.get('code')}")
        print(f"  message: {data3.get('message')}")
        if data3.get("code") == 0:
            player_data3 = data3.get("data", {})
            subtitle_info3 = player_data3.get("subtitle", {})
            print(f"  是否有 subtitle 字段: {'subtitle' in player_data3}")
            print(f"  subtitle_info: {subtitle_info3}")
    except Exception as e:
        print(f"  错误: {e}")


if __name__ == "__main__":
    # 先搜索一个 openclaw 视频来测试
    print("正在搜索 openclaw 视频...")
    search_url = "https://api.bilibili.com/x/web-interface/search/all"
    search_data = http_get_json(search_url, {"keyword": "openclaw", "search_type": "video", "page": 1, "page_size": 3})

    if search_data.get("code") == 0:
        result_data = search_data.get("data", {})
        # B站搜索 API 返回的 result 可能是列表套字典，也可能直接是列表
        results = result_data.get("result", [])
        video_results = []
        
        if isinstance(results, list):
            for r in results:
                if isinstance(r, dict):
                    if r.get("result_type") == "video":
                        video_results = r.get("data", [])
                        break
        
        # 如果上面没找到，尝试直接从 result 中获取视频
        if not video_results:
            # 尝试用搜索类型为 video 的 API
            search_data2 = http_get_json(
                "https://api.bilibili.com/x/web-interface/search/type",
                {"keyword": "openclaw", "search_type": "video", "page": 1, "page_size": 3}
            )
            if search_data2.get("code") == 0:
                video_results = search_data2.get("data", {}).get("result", [])

        if video_results:
            for v in video_results[:3]:
                if isinstance(v, dict):
                    bvid = v.get("bvid", "")
                    title = v.get("title", "").replace("<em class=\"keyword\">", "").replace("</em>", "")
                    print(f"\n视频: {title} ({bvid})")
                    test_subtitle_apis(bvid)
        else:
            print("未找到视频")
    else:
        print(f"搜索失败: {search_data.get('message')}")
