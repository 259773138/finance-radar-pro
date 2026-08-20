"""
融合引擎B - 自选股/基金行情抓取 (daily_stock_analysis思想)
支持 A股/港股/美股/ETF，优先用 AkShare，失败用 mock 保证可用
"""
import json, traceback, time

def fetch_cn_stock(code):
    try:
        import akshare as ak
        # 尝试获取实时行情
        df = ak.stock_zh_a_spot_em()
        row = df[df["代码"]==code]
        if not row.empty:
            r=row.iloc[0]
            return {"code":code, "name":r.get("名称",code), "price": float(r.get("最新价",0)), "pct": float(str(r.get("涨跌幅","0")).replace("%","") or 0), "amount": str(r.get("成交额","-")), "source":"akshare"}
    except Exception as e:
        print(f"[WARN] ak cn {code} failed: {e}")
    return None

def fetch_hk_stock(code):
    # hk00700 -> 00700
    try:
        import akshare as ak
        pure = code.replace("hk","").replace("HK","")
        # ak.stock_hk_spot_em 较慢，简化用 mock + 尝试
        df = ak.stock_hk_spot_em()
        row = df[df["代码"]==pure]
        if not row.empty:
            r=row.iloc[0]
            return {"code":code, "name":r.get("名称",code), "price": float(r.get("最新价",0) or 0), "pct": float(str(r.get("涨跌幅","0")).replace("%","") or 0), "source":"akshare_hk"}
    except Exception as e:
        print(f"[WARN] hk {code} failed: {e}")
    return None

def fetch_us_stock(code):
    try:
        import akshare as ak
        # 用 yfinance 更稳
        import yfinance as yf
        t=yf.Ticker(code)
        hist=t.history(period="2d")
        if not hist.empty:
            price=float(hist["Close"].iloc[-1])
            prev=float(hist["Close"].iloc[-2]) if len(hist)>1 else price
            pct= round((price-prev)/prev*100,2) if prev else 0
            return {"code":code, "name":code, "price":price, "pct":pct, "source":"yfinance"}
    except Exception as e:
        print(f"[WARN] us {code} failed: {e}")
    return None

def mock_stock(code, name):
    import random
    price= round(random.uniform(8, 300),2)
    pct= round(random.uniform(-2.5, 3.5),2)
    return {"code":code, "name":name, "price":price, "pct":pct, "amount":"--", "source":"mock", "note":"演示数据(未配置真实行情源或网络受限)"}

def load_watchlist():
    # 优先读用户通过网页同步到仓库的 config/watchlist.json，否则用默认
    for p in ["config/watchlist.json", "config/stocks_default.json"]:
        try:
            with open(p, encoding="utf-8") as f:
                data=json.load(f)
                if isinstance(data, list) and data:
                    return data
        except: pass
    return [{"code":"510050","name":"50ETF","market":"CN"}]

def fetch_all():
    watchlist=load_watchlist()
    print(f"[INFO] watchlist {watchlist}")
    results=[]
    for item in watchlist:
        code=item.get("code",""); name=item.get("name",code); market=item.get("market","CN")
        res=None
        if market=="CN":
            res=fetch_cn_stock(code)
        elif market=="HK":
            res=fetch_hk_stock(code)
        elif market=="US":
            res=fetch_us_stock(code)
        if res is None:
            res=mock_stock(code, name)
        else:
            res["name"]=name  # 保持用户备注名
            res["market"]=market
        # 补充技术简评(简化版 daily_stock_analysis 的技术面)
        res["tech"] = "放量上攻" if res["pct"]>1.5 else "缩量整理" if abs(res["pct"])<0.8 else "承压回调"
        results.append(res)
        time.sleep(0.6)
    return results

if __name__=="__main__":
    print(json.dumps(fetch_all(), ensure_ascii=False, indent=2))
