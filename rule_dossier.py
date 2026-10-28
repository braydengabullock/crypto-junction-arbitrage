"""Conservative cross-venue resolution-rule dossier.

A title match is never a verified complement. This module prepares human
review and rejects mismatches in the documented event specification. Even a
passed dossier is not legal eligibility, exchange confirmation or an alert.
"""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

FIELDS = (
    "underlying_event", "precise_question", "measurement_source",
    "threshold_and_units", "observation_start_utc", "observation_end_utc",
    "resolution_condition", "exceptions_and_cancellation",
    "dispute_and_correction_policy", "payout_currency", "payout_per_contract",
)
def _stamp(value):
    t=datetime.fromisoformat(str(value).replace("Z","+00:00"))
    if t.tzinfo is None:
        raise ValueError("Timestamp missing timezone")
    return t.astimezone(timezone.utc)

def _text(value):
    return " ".join(str(value).strip().casefold().split())

def review_rules(a, b):
    """Fail-closed dossier comparison; returns only manual review classification."""
    reasons=[]
    if not isinstance(a,dict) or not isinstance(b,dict):
        return {"status":"BLOCKED","reasons":["Two evidence records required"],
                "settlement_equivalence_verified":False}
    for label,record in (("A",a),("B",b)):
        missing=[k for k in FIELDS if not str(record.get(k) or "").strip()]
        if missing: reasons.append(label+" missing: "+", ".join(missing))
        if not str(record.get("official_rule_url","")).startswith("https://"):
            reasons.append(label+" missing official HTTPS rules link")
        if record.get("verified_by_human") is not True:
            reasons.append(label+" rules not independently reviewed")
    if reasons:
        return {"status":"BLOCKED","reasons":reasons,
                "settlement_equivalence_verified":False}
    for field in FIELDS:
        if field in ("observation_start_utc","observation_end_utc"):
            try:
                if _stamp(a[field]) != _stamp(b[field]):
                    reasons.append("Different "+field)
            except (ValueError,TypeError):
                reasons.append("Invalid timestamp: "+field)
        elif field=="payout_per_contract":
            try:
                va,vb=Decimal(str(a[field])),Decimal(str(b[field]))
                if not va.is_finite() or not vb.is_finite() or va!=vb or va<=0:
                    reasons.append("Non-equivalent or invalid payout")
            except (ValueError,InvalidOperation):
                reasons.append("Invalid payout amount")
        elif _text(a[field])!=_text(b[field]):
            reasons.append("Different "+field)
    if _text(a.get("selected_side")) not in ("yes","no") or _text(b.get("selected_side")) not in ("yes","no"):
        reasons.append("Both YES/NO selections required")
    elif _text(a["selected_side"])==_text(b["selected_side"]):
        reasons.append("Legs are not complementary YES/NO")
    return {
      "status":"BLOCKED" if reasons else "MANUAL_EVIDENCE_MATCH",
      "reasons":reasons,
      "settlement_equivalence_verified":False,
      "warning":"Matching user-supplied rule summaries do not independently establish legally equivalent outcomes. Obtain primary-source verification; no trade signal."
    }
