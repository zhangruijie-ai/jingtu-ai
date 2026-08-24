# -*- coding: utf-8 -*-
"""
警途AI 每日时政自动更新脚本
功能：抓取新闻源 → 调 DeepSeek 整理成申论素材 → 生成 daily-news.json
运行：python update_daily.py（需要环境变量 DEEPSEEK_API_KEY）
"""
import os
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

import requests

# ─────────────────────────────────────────
# 配置：新闻源（可自行增删）
# ─────────────────────────────────────────
RSS_SOURCES = [
    {
        "name": "人民网·时政",
        "url": "http://www.people.com.cn/rss/politics.xml",
        "limit": 15,
    },
    {
        "name": "人民网·社会",
        "url": "http://www.people.com.cn/rss/society.xml",
        "limit": 15,
    },
]

# 公安部官网"公安要闻"列表页（HTML 解析，失败则跳过）
MPS_NEWS_URL = "https://www.mps.gov.cn/n2255079/n2255079/n2255079/index.html"

DEEPSEEK_API = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0 Safari/537.36"
}


def fetch_rss(source):
    """抓取单个 RSS 源，返回 [(title, link, description)]"""
    items = []
    try:
        resp = requests.get(source["url"], headers=HEADERS, timeout=15)
        resp.encoding = "utf-8"
        root = ET.fromstring(resp.content)
        channel = root.find("channel")
        if channel is None:
            return items
        for item in channel.findall("item")[: source["limit"]]:
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            desc = item.findtext("description", "").strip()
            if title:
                items.append({"title": title, "link": link, "desc": desc})
    except Exception as e:
        print(f"[fetch_rss] {source['name']} 抓取失败: {e}")
    return items


def fetch_mps():
    """抓取公安部官网要闻（HTML 解析，容错）"""
    items = []
    try:
        resp = requests.get(MPS_NEWS_URL, headers=HEADERS, timeout=15)
        resp.encoding = "utf-8"
        html = resp.text
        # 匹配 <a ...>标题</a> 形式的新闻标题
        pattern = re.compile(r'<a[^>]*href="([^"]+)"[^>]*title="([^"]+)"')
        matches = pattern.findall(html)
        for link, title in matches[:10]:
            title = title.strip()
            if title and len(title) > 5:
                items.append({"title": title, "link": link, "desc": ""})
    except Exception as e:
        print(f"[fetch_mps] 公安部要闻抓取失败: {e}")
    return items


def build_prompt(raw_news):
    """构造 DeepSeek 的整理提示词"""
    news_text = "\n".join(
        f"{i+1}. [{n['title']}]" for i, n in enumerate(raw_news)
    )
    prompt = f"""你是一名资深的公安联考申论辅导老师，熟悉治安学、公安工作和时政热点。

下面是从人民日报、公安部官网等权威媒体抓取到的当日新闻标题（{len(raw_news)}条）：

{news_text}

请从中筛选出【与治安、公安、社会治理、法治、公共安全最相关】的 4 条新闻，并为每一条生成以下内容，最终输出一个严格的 JSON（不要输出任何 JSON 以外的文字，不要用 markdown 代码块）：

{{
  "items": [
    {{
      "source": "来源媒体（如：人民网）",
      "tag": "4字以内的主题标签（如：扫黑除恶/数据安全/基层治理/网络安全）",
      "title": "新闻标题（精炼，20字以内）",
      "summary": "一句话摘要（50字以内）",
      "shenlun": "申论转化：给出1个可用论点+2个对策（80字以内）",
      "security": "治安关联：这条新闻与治安学/公安工作的关系（60字以内）"
    }}
  ]
}}

要求：
1. 只选与治安/公安/法治/社会治理相关的，无关的（纯经济、纯科技、纯体育等）跳过
2. 语言要符合申论/公文的简洁规范，动词开头
3. 如果相关新闻不足4条，有几条输出几条
4. 必须是合法 JSON，可直接被 json.loads 解析"""
    return prompt


def call_deepseek(prompt):
    """调用 DeepSeek 整理"""
    if not API_KEY:
        print("[call_deepseek] 未配置 DEEPSEEK_API_KEY，跳过 AI 整理")
        return None
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 1500,
    }
    try:
        resp = requests.post(
            DEEPSEEK_API,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}",
            },
            json=payload,
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"].strip()
        # 去掉可能的 markdown 代码块包裹
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
        return json.loads(content)
    except Exception as e:
        print(f"[call_deepseek] 调用失败: {e}")
        return None


def fallback_items(raw_news):
    """DeepSeek 不可用时，用简单规则生成兜底内容"""
    def clean(text):
        # 去除 HTML 标签
        return re.sub(r"<[^>]+>", "", text).strip()

    items = []
    for n in raw_news[:4]:
        items.append({
            "source": "人民网",
            "tag": "时政",
            "title": clean(n["title"])[:20],
            "summary": clean(n["desc"])[:50] if n["desc"] else clean(n["title"])[:50],
            "shenlun": "论点：坚持法治思维推进社会治理。对策：强化责任落实、健全长效机制。",
            "security": "关注时政动态，积累申论与公安专业科目素材。",
        })
    return items


def main():
    # 1. 抓取
    raw_news = []
    for src in RSS_SOURCES:
        raw_news.extend(fetch_rss(src))
    mps_news = fetch_mps()
    if mps_news:
        raw_news.extend(mps_news)

    # 去重（按标题）
    seen = set()
    deduped = []
    for n in raw_news:
        if n["title"] not in seen:
            seen.add(n["title"])
            deduped.append(n)
    raw_news = deduped

    if not raw_news:
        print("[main] 未抓到任何新闻，退出")
        return

    print(f"[main] 共抓取 {len(raw_news)} 条新闻")

    # 2. AI 整理
    prompt = build_prompt(raw_news)
    result = call_deepseek(prompt)

    # 3. 兜底
    if not result or not result.get("items"):
        print("[main] AI 整理失败，使用兜底规则")
        items = fallback_items(raw_news)
    else:
        items = result["items"]

    # 4. 生成输出（北京时间）
    bj = timezone(timedelta(hours=8))
    now = datetime.now(bj)
    output = {
        "date": now.strftime("%Y-%m-%d"),
        "updated": now.strftime("%Y-%m-%d %H:%M"),
        "items": items[:4],
    }

    out_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "daily-news.json"
    )
    out_path = os.path.abspath(out_path)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"[main] 已生成 {out_path}，共 {len(items)} 条")


if __name__ == "__main__":
    main()
