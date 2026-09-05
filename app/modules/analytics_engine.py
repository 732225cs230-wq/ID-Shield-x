"""
IDShield-X: Border Screening Analytics & Statistics Module (Step 9)
Smart India Hackathon 2026 | Problem Statement: SIH26188
Ministry of Home Affairs (MHA) | Sashastra Seema Bal (SSB)

Aggregates operational checkpoint screening statistics from minimal history metadata:
1. Total, Completed, and Flagged screenings count
2. Risk Tier Distribution (Low Concern, Review Required, High Concern)
3. Document Category Distribution (Passport, Visa, National ID, Driving License, Permit)
4. Transit clearance rates and secondary inspection referrals
5. Empty-data resilience (returns valid structured zeroes without crashing)

IMPORTANT NOTICE:
- DEMO / ACADEMIC PROTOTYPE ONLY.
- Does not represent real border checkpoint traffic or real government intelligence.
- Zero personal identity information is included in analytics aggregates.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core import config
from app.modules.audit_ledger import history_store


def compute_analytics_summary(records: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Computes statistical summaries across historical screening sessions.
    Handles empty records gracefully.
    """
    if records is None:
        records = history_store.records

    total = len(records)

    if total == 0:
        return {
            "total_screenings": 0,
            "completed_count": 0,
            "flagged_count": 0,
            "review_required_count": 0,
            "low_concern_count": 0,
            "high_concern_count": 0,
            "referral_rate_pct": 0.0,
            "document_distribution": {
                "passport": 0,
                "visa": 0,
                "national_id": 0,
                "driving_license": 0,
                "permit": 0
            },
            "risk_distribution": {
                "low_concern": {"count": 0, "pct": 0.0},
                "review_required": {"count": 0, "pct": 0.0},
                "high_concern": {"count": 0, "pct": 0.0}
            },
            "checkpoint_info": {
                "id": config.CHECKPOINT_ID,
                "name": config.CHECKPOINT_NAME,
                "operator": "Sub-Inspector on Duty"
            },
            "is_empty": True,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "disclaimer": "DEMO / ACADEMIC PROTOTYPE &bull; Statistics reflect synthetic demo sessions only."
        }

    # Count categories
    doc_dist: Dict[str, int] = {
        "passport": 0,
        "visa": 0,
        "national_id": 0,
        "driving_license": 0,
        "permit": 0
    }
    for r in records:
        dtype = r.get("document_type", "passport").lower()
        if dtype in doc_dist:
            doc_dist[dtype] += 1
        else:
            doc_dist[dtype] = 1

    # Count statuses
    low_cnt = sum(1 for r in records if r.get("risk_status") == "Low Concern")
    review_cnt = sum(1 for r in records if r.get("risk_status") == "Review Required")
    high_cnt = sum(1 for r in records if r.get("risk_status") == "High Concern")
    flagged_cnt = sum(1 for r in records if r.get("processing_status") == "FLAGGED")
    completed_cnt = total - flagged_cnt

    low_pct = round((low_cnt / total) * 100, 1)
    review_pct = round((review_cnt / total) * 100, 1)
    high_pct = round((high_cnt / total) * 100, 1)
    referral_rate = round(((review_cnt + high_cnt) / total) * 100, 1)

    return {
        "total_screenings": total,
        "completed_count": completed_cnt,
        "flagged_count": flagged_cnt,
        "review_required_count": review_cnt,
        "low_concern_count": low_cnt,
        "high_concern_count": high_cnt,
        "referral_rate_pct": referral_rate,
        "document_distribution": doc_dist,
        "risk_distribution": {
            "low_concern": {"count": low_cnt, "pct": low_pct},
            "review_required": {"count": review_cnt, "pct": review_pct},
            "high_concern": {"count": high_cnt, "pct": high_pct}
        },
        "recent_screenings": records[:5],
        "checkpoint_info": {
            "id": config.CHECKPOINT_ID,
            "name": config.CHECKPOINT_NAME,
            "operator": "Sub-Inspector on Duty"
        },
        "is_empty": False,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "disclaimer": "DEMO / ACADEMIC PROTOTYPE &bull; Statistics reflect synthetic demo sessions only."
    }
