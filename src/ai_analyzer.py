"""
AI大脑 - 融合分析 (ModelScope + OpenAI兼容)
特性：
1. 自动从服务器拉取模型列表 (GET /v1/models)
2. 默认选用魔搭最强的 Qwen 系列 (Qwen3 > Qwen2.5 > Qwen)
3. 支持 ModelScope 和任意 OpenAI 兼容 endpoint
"""
import os, requests, json, traceback

MODELSCOPE_BASE = "https://api-inference.modelscope.cn/v1"
DEFAULT_MODEL = "Qwen/Qwen2.5-72B-Instruct"  # 兜底，若拉取失败

def list_models_from_server(base_url, api_key):
    """从服务器拉取可用模型"""
    if not api_key:
        return []
    try:
        r = requests.get(f"{base_url.rstrip('/')}/models", headers={"Authorization": f"Bearer {api_key}"}, timeout=12)
        if r.status_code==200:
            data=r.json()
            models=[m["id"] for m in data.get("data",[])]
            print(f"[INFO] server models: {models[:10]}")
            return models
    except Exception as e:
        print(f"[WARN] list models failed: {e}")
    return []

def pick_best_qwen(models):
    """从列表里挑最好的 Qwen"""
    if not models:
        return DEFAULT_MODEL
    # 优先级：Qwen3-235B > Qwen3-32B > Qwen2.5-72B > Qwen2-72B > 任意 Qwen > 第一个
    priority = ["Qwen3-235", "Qwen3-32B", "Qwen3", "Qwen2.5-72B", "Qwen2.5-32B", "Qwen2-72B", "Qwen2", "Qwen"]
    for p in priority:
        for m in models:
            if p.lower() in m.lower():
                print(f"[INFO] pick model {m} by priority {p}")
                return m
    # fallback 找 qwen
    for m in models:
        if "qwen" in m.lower():
            return m
    return models[0]

def call_llm(prompt, hotspots, stocks):
    """
    调用 LLM 生成早报分析
    hotspots: list 热点
    stocks: list 股票
    """
    api_key = os.getenv("MODELSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
    base_url = os.getenv("MODELSCOPE_BASE_URL") or os.getenv("OPENAI_BASE_URL") or MODELSCOPE_BASE
    if "modelscope" in base_url:
        base_url = MODELSCOPE_BASE

    models = list_models_from_server(base_url, api_key)
    model = os.getenv("MODEL_NAME") or pick_best_qwen(models) if models else (os.getenv("MODEL_NAME") or DEFAULT_MODEL)
    # 若用户指定了 MODEL_NAME 且不在列表，尊重用户
    if os.getenv("MODEL_NAME"):
        model = os.getenv("MODEL_NAME")

    print(f"[INFO] using LLM base={base_url} model={model} has_key={bool(api_key)}")

    # 构造 prompt
    hotspot_text = "\n".join([f"- [{h['source']}] {h['title']} (命中:{','.join(h.get('hits',[])[:2])})" for h in hotspots[:20]])
    stock_text = "\n".join([f"- {s['name']}({s['code']}) 现价{s['price']} 涨跌{s['pct']}% 技术:{s.get('tech','')}" for s in stocks])

    system_prompt = """你是资深的A股+港美股首席策略分析师，擅长把宏观政策、行业热点和个股技术面融合分析。请基于提供的【全网热点】和【自选股行情】，生成一份精炼的《每日财经早报》。
要求：
1. 语言中文，专业但通俗，适合飞书/网页阅读
2. 输出严格 JSON，包含字段：core_conclusion(一句话核心结论), policy_radar(数组3-5条政策解读每条含title+impact), market_hot(3-5条市场热点), stock_advice(每只票的advice含code+name+score(0-100)+trend(看多/中性/看空)+support_resistance+action), risk_tips(风险提示)
3. 不要输出markdown，只输出JSON
"""

    user_prompt = f"【全网热点】\n{hotspot_text}\n\n【自选股行情】\n{stock_text}\n\n请生成今日早报JSON。"

    if not api_key:
        print("[WARN] no api_key, use mock analysis")
        return mock_analysis(hotspots, stocks)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role":"system","content": system_prompt},
                {"role":"user","content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2500,
        )
        content = resp.choices[0].message.content.strip()
        # 清理 ```json 包裹
        if content.startswith("```"):
            content = content.strip("`").replace("json","",1).strip()
        # 尝试解析
        data = json.loads(content[content.find("{"): content.rfind("}")+1])
        data["_meta"]={"model":model, "base":base_url}
        return data
    except Exception as e:
        print(f"[ERROR] LLM call failed: {e}\n{traceback.format_exc()}")
        return mock_analysis(hotspots, stocks, note=f"AI调用失败已降级: {e}")

def mock_analysis(hotspots, stocks, note="演示分析(未配置MODELSCOPE_API_KEY)"):
    return {
        "core_conclusion": f"政策面偏暖，热点聚焦AI与新能源；持仓整体 {stocks[0].get('tech','震荡')}，建议控制仓位、逢高兑现。",
        "policy_radar": [
            {"title": h["title"][:30], "impact": f"来源{h['source']}，命中关键词{','.join(h.get('hits',[])[:2])}，对大盘情绪偏正向"} for h in hotspots[:3]
        ],
        "market_hot": [
            {"title": h["title"][:30], "desc": h["content"][:60]} for h in hotspots[3:6]
        ],
        "stock_advice": [
            {"code": s["code"], "name": s["name"], "score": 65 if s["pct"]>0 else 45, "trend": "看多" if s["pct"]>1 else "中性", "support_resistance": "支撑位看5日线，压力位看前高", "action": "持有/观望" if abs(s["pct"])<2 else "逢高减仓"} for s in stocks
        ],
        "risk_tips": "美联储政策与汇率波动仍是外部风险，控制仓位，勿追高。",
        "_meta": {"model":"mock", "note": note}
    }
