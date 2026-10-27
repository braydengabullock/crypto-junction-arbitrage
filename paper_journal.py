"""Read-only timestamped paper trade journal; does not contact exchanges.

The entry records assumptions, not real fills. Settlement is an explicit, separately
documented observation. Never automatically infer a win from projected ROI.
"""
import argparse
import json
import sqlite3
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

def iso(value):
    v=datetime.fromisoformat(str(value).replace("Z","+00:00"))
    if v.tzinfo is None:
        raise ValueError("Timestamp must contain timezone")
    return v.astimezone(timezone.utc).isoformat()

def decimal(value):
    v=Decimal(str(value))
    if not v.is_finite() or v<0:
        raise ValueError("Invalid nonnegative amount")
    return v

def connect(path):
    db=sqlite3.connect(path)
    db.execute("""CREATE TABLE IF NOT EXISTS paper_trades (
        trade_id TEXT PRIMARY KEY, detected_at TEXT NOT NULL,
        entry_json TEXT NOT NULL, settlement_json TEXT, added_at TEXT NOT NULL)""")
    return db

def record(db, trade_id, candidate, review, detected_at):
    if review.get("status")!="PAPER_REVIEW":
        raise ValueError("Only complete paper reviews may be recorded")
    if not trade_id or not isinstance(trade_id,str):
        raise ValueError("Trade ID required")
    parsed=iso(detected_at)
    if not isinstance(candidate,dict):
        raise ValueError("Candidate must be object")
    entry={
        "trade_id":trade_id,"detected_at":parsed,"candidate":candidate,
        "review":review,
        "fill_status":"HYPOTHETICAL_ONLY",
        "data_type":"USER_SUPPLIED_NOT_VERIFIED",
    }
    db.execute("INSERT INTO paper_trades VALUES (?,?,?,?,?)",
        (trade_id,parsed,json.dumps(entry,sort_keys=True),None,
         datetime.now(timezone.utc).isoformat()))
    db.commit()
    return entry

def settle(db, trade_id, *, observed_at, payout_a, payout_b,
           source_a, source_b, notes=""):
    date=iso(observed_at)
    row=db.execute("SELECT entry_json,settlement_json FROM paper_trades WHERE trade_id=?",
                   (trade_id,)).fetchone()
    if not row:
        raise ValueError("Unknown paper trade")
    if row[1] is not None:
        raise ValueError("Already settled; journal is append-once")
    entry=json.loads(row[0])
    if date < entry["detected_at"]:
        raise ValueError("Settlement observation predates entry")
    if not source_a or not source_b:
        raise ValueError("Both resolution sources required")
    p_a,p_b=decimal(payout_a),decimal(payout_b)
    expected=Decimal(str(entry["review"]["pair"]["total_cost"])) + Decimal(
        str(entry["review"]["pair"]["estimated_net_usd"]))
    # Typical complementary hedged pair settles at the original integer
    # contract quantity. This is checked, not assumed to have happened.
    actual=p_a+p_b
    initial=Decimal(str(entry["review"]["pair"]["capital_usd"]))
    result={
        "observed_at":date,"source_a":source_a,"source_b":source_b,
        "payout_a_usd":str(p_a),"payout_b_usd":str(p_b),
        "total_payout_usd":str(actual),"cost_usd":str(initial),
        "realized_hypothetical_profit_usd":str(actual-initial),
        "settlement_consistent_with_model":actual==expected,
        "notes":notes,
        "caveat":"Payouts are user-supplied; the entry was not actually filled. Not realized trading profit.",
    }
    db.execute("UPDATE paper_trades SET settlement_json=? WHERE trade_id=?",
               (json.dumps(result,sort_keys=True),trade_id))
    db.commit()
    return result

def report(db):
    result=[]
    for trade_id,entry_json,settlement_json in db.execute(
            "SELECT trade_id,entry_json,settlement_json FROM paper_trades ORDER BY detected_at"):
        entry=json.loads(entry_json)
        result.append({
            "trade_id":trade_id,
            "detected_at":entry["detected_at"],
            "mode":"HYPOTHETICAL_ONLY",
            "projected_net_usd":entry["review"]["pair"]["estimated_net_usd"],
            "settlement":json.loads(settlement_json) if settlement_json else None,
        })
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--database",default="local_paper_trades.sqlite3")
    sub=p.add_subparsers(dest="cmd",required=True)
    r=sub.add_parser("record")
    r.add_argument("--id",required=True)
    r.add_argument("--candidate",required=True)
    r.add_argument("--balances",required=True)
    r.add_argument("--timestamp",required=True)
    s=sub.add_parser("settle")
    s.add_argument("--id",required=True)
    s.add_argument("--timestamp",required=True)
    s.add_argument("--payout-a",required=True)
    s.add_argument("--payout-b",required=True)
    s.add_argument("--source-a",required=True)
    s.add_argument("--source-b",required=True)
    sub.add_parser("report")
    args=p.parse_args()
    with connect(args.database) as db:
        if args.cmd=="record":
            from paper_review import review
            candidate=json.loads(Path(args.candidate).read_text())
            balances=json.loads(Path(args.balances).read_text())
            evaluated=review(candidate,balances,now=datetime.fromisoformat(
                args.timestamp.replace("Z","+00:00")))
            if evaluated["status"]!="PAPER_REVIEW":
                print(json.dumps({"status":"BLOCKED","reasons":evaluated["reasons"]},indent=2))
                raise SystemExit(1)
            output=record(db,args.id,candidate,evaluated,args.timestamp)
        elif args.cmd=="settle":
            output=settle(db,args.id,observed_at=args.timestamp,
                          payout_a=args.payout_a,payout_b=args.payout_b,
                          source_a=args.source_a,source_b=args.source_b)
        else:
            output=report(db)
        print(json.dumps(output,indent=2))

if __name__=="__main__":
    main()
