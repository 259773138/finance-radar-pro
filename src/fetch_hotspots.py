"""
融合引擎A - 全网热点抓取 (TrendRadar思想)
抓取 10+ 核心财经/政策源，支持容错和去重
"""
import requests, feedparser, json, time, re
from datetime import datetime

HEADERS = {"User-Agent": "Mozilla/5.0 FinanceRadarPro/1.0"}

SOURCES = [
    {"id": "cls_telegraph", "name": "财联社电讯", "type": "json", "url": "https://www.cls.cn/nodeapi/telegraphList?app=CailianpressWeb&os=web&sv=8.4.6"},
    {"id": "wallstreetcn_live", "name": "华尔街见闻", "type": "json", "url": "https://api-one-wscn.awtmt.com/apiv1/content/lives?channel=global-channel&limit=30"},
    {"id": "sina_finance", "name": "新浪财经", "type": "rss", "url": "https://rss.sina.com.cn/roll/finance/hot_roll.xml"},
    {"id": "eastmoney", "name": "东方财富", "type": "rss", "url": "https://rsshub.app/eastmoney/search/茅台"},
    {"id": "cls_hot", "name": "财联社热门", "type": "rss", "url": "https://rsshub.app/cls/hot"},
    {"id": "wallstreetcn_hot", "name": "华尔街见闻热门", "type": "rss", "url": "https://rsshub.app/wallstreetcn/hot"},
    {"id": "cctv_finance", "name": "央视财经", "type": "rss", "url": "https://rsshub.app/cctv/finance"},
    {"id": "gov_news", "name": "中国政府网政策", "type": "rss", "url": "https://www.gov.cn/rss/policy.xml"},
]

def fetch_json(source):
    try:
        r = requests.get(source["url"], headers=HEADERS, timeout=12)
        if r.status_code != 200:
            return []
        data = r.json()
        items = []
        # 财联社
        if source["id"] == "cls_telegraph":
            for d in data.get("data", {}).get("roll_data", [])[:20]:
                items.append({"title": d.get("title") or d.get("content","")[:80], "content": d.get("content",""), "url": f"https://www.cls.cn/detail/{d.get('id','')}", "time": d.get("ctime",""), "source": source["name"]})
        elif source["id"] == "wallstreetcn_live":
            for d in data.get("data", {}).get("items", [])[:20]:
                items.append({"title": d.get("title") or d.get("content_text","")[:80], "content": d.get("content_text",""), "url": d.get("uri",""), "time": str(d.get("display_time", "")), "source": source["name"]})
        return items
    except Exception as e:
        print(f"[WARN] {source['name']} json fetch failed: {e}")
        return []

def fetch_rss(source):
    try:
        d = feedparser.parse(source["url"])
        items=[]
        for e in d.entries[:15]:
            items.append({"title": e.get("title",""), "content": e.get("summary","")[:300], "url": e.get("link",""), "time": e.get("published",""), "source": source["name"]})
        return items
    except Exception as e:
        print(f"[WARN] {source['name']} rss failed: {e}")
        return []

def load_keywords():
    try:
        with open("config/keywords_comprehensive.txt", encoding="utf-8") as f:
            kws=[l.strip() for l in f if l.strip() and not l.strip().startswith("#")]
        return kws
    except:
        return ["降准","降息","AI","新能源"]

def filter_and_score(items, keywords):
    # 简单相关度评分：命中关键词越多分越高，政策类加权
    scored=[]
    for it in items:
        text = (it["title"]+" "+it["content"]).lower()
        hits = [k for k in keywords if k.lower() in text]
        score = len(hits)
        # 政策类关键词额外+2
        policy_boost = sum(1 for h in hits if h in ["降准","降息","国常会","政治局","证监会","央行","财政部"])
        score += policy_boost*2
        it["hits"]=hits[:5]
        it["score"]=score
        if score>0 or len(scored)<30:  # 保留高相关 + 兜底30条
            scored.append(it)
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:60]

def fetch_all():
    all_items=[]
    for s in SOURCES:
        if s["type"]=="json":
            all_items.extend(fetch_json(s))
        else:
            all_items.extend(fetch_rss(s))
        time.sleep(0.5)
    print(f"[INFO] raw fetched {len(all_items)} items")
    if len(all_items)<10:
        # 兜底 mock，保证页面不空
        all_items.extend([
            {"title":"央行开展逆回购操作 维护流动性合理充裕","content":"央行公告称开展操作...","url":"https://www.pbc.gov.cn","time":str(datetime.now()),"source":"兜底数据-央行"},
            {"title":"证监会就活跃资本市场答记者问","content":"证监会表示将...","url":"https://www.csrc.gov.cn","time":str(datetime.now()),"source":"兜底数据-证监会"},
            {"title":"华尔街见闻：美股科技股集体走强","content":"纳指...","url":"https://wallstreetcn.com","time":str(datetime.now()),"source":"兜底数据-华尔街见闻"},
        ])
    kws=load_keywords()
    filtered=filter_and_score(all_items, kws)
    # 去重 by title
    seen=set(); uniq=[]
    for it in filtered:
        t=it["title"][:30]
        if t not in seen:
            uniq.append(it); seen.add(t)
    print(f"[INFO] filtered {len(uniq)} items with {len(kws)} keywords")
    return uniq

if __name__=="__main__":
    res=fetch_all()
    print(json.dumps(res[:3], ensure_ascii=False, indent=2))
