# -*- coding: utf-8 -*-
"""
HidenCloud 自动续期 Telegram 推送定制外挂
作用：
1. 自动劫持 Telegram 消息通知：
   - 自动将开头的 🎉 替换为对应国旗（根据 SERVER_FLAG、SERVER_NAME 或 GitHub 仓库名自动识别）
   - 将全角冒号转换为半角冒号加空格（到期: 、时间: ），对齐精简版排版样式
   - 自动清理多余的服务器行，保持排版极简美观
2. 自动环境变量桥接：
   - 自动在 EMAIL <-> HIDENCLOUD_EMAIL 以及 PASSWORD <-> HIDENCLOUD_PASSWORD 之间互通
3. 上游无感兼容：
   - 本文件属于独立外挂，上游仓库无此文件，以后同步更新上游代码时绝不冲突、绝不覆盖。
"""

import os
import requests

# 1. 自动环境变量桥接
if not os.environ.get("HIDENCLOUD_EMAIL") and os.environ.get("EMAIL"):
    os.environ["HIDENCLOUD_EMAIL"] = os.environ["EMAIL"]
elif not os.environ.get("EMAIL") and os.environ.get("HIDENCLOUD_EMAIL"):
    os.environ["EMAIL"] = os.environ["HIDENCLOUD_EMAIL"]

if not os.environ.get("HIDENCLOUD_PASSWORD") and os.environ.get("PASSWORD"):
    os.environ["HIDENCLOUD_PASSWORD"] = os.environ["PASSWORD"]
elif not os.environ.get("PASSWORD") and os.environ.get("HIDENCLOUD_PASSWORD"):
    os.environ["PASSWORD"] = os.environ["HIDENCLOUD_PASSWORD"]


def get_country_flag():
    """根据 SERVER_FLAG、SERVER_NAME 或 GitHub 仓库名自动获取国旗"""
    if os.environ.get("SERVER_FLAG"):
        return os.environ.get("SERVER_FLAG").strip()

    server_name = os.environ.get("SERVER_NAME", "")
    for char in server_name:
        if ord(char) > 0x1F1E5:
            return server_name.split()[0]

    flag_map = {
        "AE": "🇦🇪", "阿联酋": "🇦🇪", "UAE": "🇦🇪",
        "AU": "🇦🇺", "澳大利亚": "🇦🇺", "AUSTRALIA": "🇦🇺",
        "FR": "🇫🇷", "法国": "🇫🇷", "FRANCE": "🇫🇷",
        "IN": "🇮🇳", "印度": "🇮🇳", "INDIA": "🇮🇳",
        "MX": "🇲🇽", "墨西哥": "🇲🇽", "MEXICO": "🇲🇽",
        "SG": "🇸🇬", "新加坡": "🇸🇬", "SINGAPORE": "🇸🇬",
        "US": "🇺🇸", "美国": "🇺🇸", "USA": "🇺🇸",
        "JP": "🇯🇵", "日本": "🇯🇵", "JAPAN": "🇯🇵",
        "HK": "🇭🇰", "香港": "🇭🇰", "HONGKONG": "🇭🇰",
        "TW": "🇹🇼", "台湾": "🇹🇼", "TAIWAN": "🇹🇼",
        "KR": "🇰🇷", "韩国": "🇰🇷", "KOREA": "🇰🇷",
        "DE": "🇩🇪", "德国": "🇩🇪", "GERMANY": "🇩🇪",
        "GB": "🇬🇧", "UK": "🇬🇧", "英国": "🇬🇧",
        "CA": "🇨🇦", "加拿大": "🇨🇦", "CANADA": "🇨🇦",
        "NL": "🇳🇱", "荷兰": "🇳🇱", "NETHERLANDS": "🇳🇱",
        "RU": "🇷🇺", "俄罗斯": "🇷🇺", "RUSSIA": "🇷🇺",
        "MY": "🇲🇾", "马来西亚": "🇲🇾", "MALAYSIA": "🇲🇾",
    }
    
    combined = f"{os.environ.get('GITHUB_REPOSITORY', '')} {server_name}".upper()
    
    import re
    match = re.search(r"[-_]([A-Z]{2})\b", combined)
    if match and match.group(1) in flag_map:
        return flag_map[match.group(1)]

    for key, flag in flag_map.items():
        if key in combined:
            return flag

    return "🎉"


# 2. 动态劫持 requests.post 拦截并美化 Telegram 消息
_orig_post = requests.post


def _hooked_post(url, *args, **kwargs):
    if "api.telegram.org" in str(url) and "json" in kwargs:
        payload = kwargs["json"]
        if isinstance(payload, dict) and "text" in payload:
            raw_text = payload["text"]
            flag = get_country_flag()

            # 1. 替换开头的图标为国旗
            if "🎉" in raw_text:
                text = raw_text.replace("🎉", flag)
            elif not raw_text.startswith(flag):
                text = f"{flag} " + raw_text.lstrip()
            else:
                text = raw_text

            # 2. 格式化冒号
            text = text.replace("到期：", "到期: ").replace("时间：", "时间: ")

            # 3. 剔除服务器备注行，保留纯净国旗卡片风格
            lines = text.splitlines()
            filtered_lines = [l for l in lines if not ("🖥️" in l and "服务器" in l)]
            text = "\n".join(filtered_lines)

            payload["text"] = text

    return _orig_post(url, *args, **kwargs)


requests.post = _hooked_post
