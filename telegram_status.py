"""Optional Telegram capture-status notice only. No opportunities or trade alerts."""
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

def status_message(snapshot_path):
    data=json.loads(Path(snapshot_path).read_text(encoding="utf-8"))
    if data.get("source")!="kalshi_public" or not data.get("research_only"):
        raise ValueError("Only read-only Kalshi snapshots supported")
    quality=data.get("data_quality",{})
    return ("Crypto Junction — Arbitrage Research Status\n"
            f"Kalshi snapshot: {data['observed_at']}\n"
            f"Open markets sampled: {quality.get('market_count',len(data.get('markets',[])))}\n"
            ("Data: Kalshi public quotes only; " +
             ("complete paginated retrieval." if quality.get("pagination", {}).get("complete")
              else "partial sampled retrieval.") + "\\n")

            "ForecastEx feed: NOT CONNECTED.\n"
            "Verified opportunities: NONE. No orders placed.")

def send_status(snapshot_path, *, sender=None):
    message=status_message(snapshot_path)
    token=os.environ.get("CJ_ARB_TELEGRAM_BOT_TOKEN")
    chat=os.environ.get("CJ_ARB_TELEGRAM_CHAT_ID")
    if not token or not chat:
        print("Telegram status disabled: configure BOTH CJ_ARB_TELEGRAM_BOT_TOKEN and CJ_ARB_TELEGRAM_CHAT_ID.")
        return False
    body=urllib.parse.urlencode({"chat_id":chat,"text":message}).encode("utf-8")
    request=urllib.request.Request(
        "https://api.telegram.org/bot"+token+"/sendMessage",
        data=body,headers={"Content-Type":"application/x-www-form-urlencoded"})
    transport=sender or urllib.request.urlopen
    with transport(request,timeout=15) as response:
        result=json.load(response)
    if not result.get("ok"):
        raise RuntimeError("Telegram delivery not confirmed")
    print("Telegram research status delivered.")
    return True

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--snapshot",required=True)
    opts=p.parse_args()
    send_status(opts.snapshot)
