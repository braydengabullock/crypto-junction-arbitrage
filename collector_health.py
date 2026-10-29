"""Read-only diagnostics for an optional on-server capture trial."""
import argparse
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from historical_snapshot_replay import timestamp

def inspect(root, *, as_of=None, max_age_minutes=5):
    base=Path(root)
    if not base.is_dir():
        return {"status":"DIRECTORY_MISSING","captures":0,"ready":False}
    now=as_of or datetime.now(timezone.utc)
    files=sorted(base.glob("*.json"))
    valid=[]
    invalid=0
    for file in files:
        try:
            doc=json.loads(file.read_text(encoding="utf-8"))
            if (doc.get("source_type")!="archived_public_orderbook_observations"
                or doc.get("research_only") is not True
                or doc.get("trade_allowed") is not False
                or not isinstance(doc.get("captures"),list)):
                raise ValueError("Invalid provenance")
            for c in doc["captures"]:
                at=timestamp(c["captured_at"])
                valid.append((at,len(c["rows"])))
        except (OSError,ValueError,TypeError,KeyError,OverflowError,AttributeError):
            invalid+=1
    last=max((at for at,_ in valid),default=None)
    age=(now-last).total_seconds()/60 if last else None
    ready=bool(last and 0<=age<=max_age_minutes and any(n>0 for _,n in valid))
    return {"status":"RECENT_OBSERVATION" if ready else "NO_RECENT_USABLE_OBSERVATION",
            "ready":ready,"files":len(files),"captures":len(valid),
            "invalid_files":invalid,"observed_market_rows":sum(n for _,n in valid),
            "latest_observation_at":last.isoformat() if last else None,
            "latest_observation_age_minutes":round(age,2) if age is not None else None,
            "research_only":True,"trade_allowed":False,
            "warning":"Healthy capture files do not prove synchronized prices, matched rules or profitable trades."}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--archive-dir",required=True)
    a=p.parse_args()
    print(json.dumps(inspect(a.archive_dir),indent=2))
if __name__=="__main__":main()
