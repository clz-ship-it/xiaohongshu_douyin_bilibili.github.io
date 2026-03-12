# -*- coding: utf-8 -*-
"""测试 B 站 API 返回的原始数据结构"""

import json
from urllib.request import Request, urlopen
import ssl

BILIBILI_SEARCH_API = "https://api.bilibili.com/x/web-interface/search/all"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com",
}

_SSL_CONTEXT = ssl.create_default_context()
_SSL_CONTEXT.check_hostname = False
_SSL_CONTEXT.verify_mode = ssl.CERT_NONE

def _http_get_json(url, params):
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    full_url = f"{url}?{query_string}"
    
    request = Request(full_url)
    for key, value in HEADERS.items():
        request.add_header(key, value)
    
    response = urlopen(request, timeout=15, context=_SSL_CONTEXT)
    response_body = response.read().decode("utf-8")
    return json.loads(response_body)

if __name__ == "__main__":
    print("测试 B 站搜索 API 返回的原始数据结构...")
    print("=" * 60)
    
    params = {
        "keyword": "openclaw",
        "page": 1,
        "search_type": "video",
    }
    
    try:
        data = _http_get_json(BILIBILI_SEARCH_API, params)
        
        print(f"返回类型：{type(data)}")
        print(f"\n完整 data['data'] 结构：")
        print(json.dumps(data.get("data", {}), ensure_ascii=False, indent=2)[:3000])
        print("\n" + "=" * 60)
        
        # 检查 result 字段
        result_list = data.get("data", {}).get("result", [])
        print(f"\nresult 类型：{type(result_list)}")
        
        if isinstance(result_list, dict):
            print(f"result 是字典，键：{result_list.keys()}")
            # 查找视频相关的键
            for key in result_list.keys():
                if 'video' in key.lower():
                    print(f"\n找到视频相关键：{key}")
                    print(f"{key} 的内容：{json.dumps(result_list[key], ensure_ascii=False, indent=2)[:1000]}")
        elif isinstance(result_list, list):
            print(f"result 是列表，长度：{len(result_list)}")
            if result_list:
                print(f"\n第一个 result 元素类型：{type(result_list[0])}")
                if isinstance(result_list[0], dict):
                    print(f"第一个 result 元素的键：{result_list[0].keys()}")
                    print(f"\n第一个 result 元素内容：")
                    print(json.dumps(result_list[0], ensure_ascii=False, indent=2)[:1500])
            
    except Exception as e:
        print(f"请求失败：{e}")
        import traceback
        traceback.print_exc()