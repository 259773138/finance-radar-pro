import json, os, datetime, pathlib
from fetch_hotspots import fetch_all as fetch_hotspots
from fetch_stocks import fetch_all as fetch_stocks
from ai_analyzer import call_llm, list_models_from_server, pick_best_qwen, MODELSCOPE_BASE

def main():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    date_str = now.strftime("%Y-%m-%d %H:%M")
    date_key = now.strftime("%Y-%m-%d")

    print(f"[START] generate report at {date_str}")
    hotspots = fetch_hotspots()
    stocks = fetch_stocks()

    # AI 分析
    analysis = call_llm("", hotspots, stocks)

    # 额外拉一次模型列表供前端选择
    api_key = os.getenv("MODELSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
    base_url = os.getenv("MODELSCOPE_BASE_URL") or MODELSCOPE_BASE
    models = list_models_from_server(base_url, api_key) if api_key else []
    best_qwen = pick_best_qwen(models) if models else "Qwen/Qwen2.5-72B-Instruct"

    report = {
        "generated_at": date_str,
        "date": date_key,
        "hotspots": hotspots,
        "stocks": stocks,
        "analysis": analysis,
        "meta": {
            "best_qwen": best_qwen,
            "available_models": models[:30],
            "hotspot_count": len(hotspots),
            "stock_count": len(stocks)
        }
    }

    # 写入 docs/data
    out_dir = pathlib.Path("docs/data")
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir/"latest.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    # 历史
    hist_dir = out_dir/"history"
    hist_dir.mkdir(parents=True, exist_ok=True)
    with open(hist_dir/f"{date_key}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    # 也写一份 models.json 供前端实时拉取模型
    with open(out_dir/"models.json", "w", encoding="utf-8") as f:
        json.dump({"best": best_qwen, "models": models}, f, ensure_ascii=False, indent=2)

    print(f"[DONE] report written to docs/data/latest.json with {len(hotspots)} hotspots, {len(stocks)} stocks, model={analysis.get('_meta',{}).get('model')}")

if __name__=="__main__":
    main()
