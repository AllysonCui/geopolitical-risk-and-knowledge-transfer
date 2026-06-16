"""
Parse Yale CELI tracker snapshots to build a firm-level exit panel.

Outputs:
  data/collected/firms_exit_panel.csv  — one row per firm, exit status + action text
  data/collected/firms_exiters.csv     — Grade A/B firms only (the main sample)

Yale grade legend:
  A = Clean break (suspended + announced exit)
  B = Suspension / scaling back
  C = Reducing activity
  D = Buying time / minimal compliance
  F = Business as usual / still operating
"""

import csv
import os
import re
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
OUT_DIR = DATA_DIR / "collected"
OUT_DIR.mkdir(exist_ok=True)

# Use the two chronological endpoints: earliest and latest snapshot
SNAPSHOTS = {
    "2022-12-24": DATA_DIR / "221224.csv",
    "2025-05-21": DATA_DIR / "250521.csv",
}
LATEST = DATA_DIR / "250521.csv"

# ── Action-text classifiers ────────────────────────────────────────────────

SOLD_PATTERNS = re.compile(
    r"\b(sold|sale|divest(iture|ed|ing)?|handover|handed over|"
    r"transfer(red)? (business|assets|stake|operations)|"
    r"sell (off|all|its|the)|selling (its|all|off|operations)|"
    r"wind(ing)? down|withdraw(al|n|ing)?|withdrew|"
    r"exited?|exit(ing)? (russia|market|operations)|"
    r"full(y)? exit|cut ties|leave (the )?russian market|"
    r"clos(e|ed|ing) (offices|operations|business)|liquidat)\b",
    re.IGNORECASE,
)
WRITEDOWN_PATTERNS = re.compile(
    r"\b(write[- ]?down|impairment|written[- ]?off|write[- ]?off|charge|loss(es)?)\b",
    re.IGNORECASE,
)
NATIONALIZED_PATTERNS = re.compile(
    r"\b(seiz(ed|ure)|national(is|iz)(ed|ation)|expropriat|confiscat|government (took|assumed))\b",
    re.IGNORECASE,
)
SUSPENDED_PATTERNS = re.compile(
    r"\b(suspend(ed)?|halt(ed)?|pause(d)?|stop(ped)?|ceas(ed)?|discontinu)\b",
    re.IGNORECASE,
)


def classify_action(action: str) -> str:
    action = action or ""
    if SOLD_PATTERNS.search(action):
        return "sold"
    if NATIONALIZED_PATTERNS.search(action):
        return "nationalized"
    if WRITEDOWN_PATTERNS.search(action):
        return "writedown_mentioned"
    if SUSPENDED_PATTERNS.search(action):
        return "suspended"
    return "other"


def load_snapshot(path: Path) -> dict:
    """Return {name: row_dict} from a snapshot CSV."""
    firms = {}
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["name"].strip()
            if name:
                firms[name] = row
    return firms


# ── Build firm-level panel ─────────────────────────────────────────────────

latest_firms = load_snapshot(LATEST)
early_firms = load_snapshot(SNAPSHOTS["2022-12-24"])

panel_rows = []
for name, row in latest_firms.items():
    grade = (row.get("yaleGrade") or "").strip()
    action = (row.get("action") or "").strip()
    industry = (row.get("industry") or "").strip()
    country = (row.get("country") or "").strip()

    early_row = early_firms.get(name, {})
    early_grade = (early_row.get("yaleGrade") or "").strip()

    action_type = classify_action(action)

    panel_rows.append(
        {
            "name": name,
            "country": country,
            "industry": industry,
            "grade_latest": grade,
            "grade_dec2022": early_grade,
            "action_text": action,
            "action_type": action_type,
            "in_dec2022_snapshot": "yes" if name in early_firms else "no",
        }
    )

# Sort by grade then name
grade_order = {"A": 0, "B": 1, "C": 2, "D": 3, "F": 4, "": 5}
panel_rows.sort(key=lambda r: (grade_order.get(r["grade_latest"], 5), r["name"]))

# ── Write full panel ───────────────────────────────────────────────────────

panel_out = OUT_DIR / "firms_exit_panel.csv"
fields = ["name", "country", "industry", "grade_latest", "grade_dec2022",
          "action_type", "in_dec2022_snapshot", "action_text"]

with open(panel_out, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(panel_rows)

print(f"Full panel: {len(panel_rows)} firms → {panel_out}")

# ── Write exiters-only file (Grade A + B) ─────────────────────────────────

exiters = [r for r in panel_rows if r["grade_latest"] in ("A", "B")]
exiters_out = OUT_DIR / "firms_exiters.csv"

with open(exiters_out, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(exiters)

print(f"Exiters (Grade A+B): {len(exiters)} firms → {exiters_out}")

# ── Summary stats ─────────────────────────────────────────────────────────

grade_counts = {}
action_counts = {}
for r in panel_rows:
    grade_counts[r["grade_latest"]] = grade_counts.get(r["grade_latest"], 0) + 1
    action_counts[r["action_type"]] = action_counts.get(r["action_type"], 0) + 1

print("\nGrade distribution (latest snapshot):")
for g in ["A", "B", "C", "D", "F", ""]:
    if g in grade_counts:
        print(f"  Grade {g or 'missing'}: {grade_counts[g]}")

print("\nAction-type classification (all firms):")
for k, v in sorted(action_counts.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}")

print("\nAction-type classification (Grade A exiters only):")
a_counts = {}
for r in panel_rows:
    if r["grade_latest"] == "A":
        a_counts[r["action_type"]] = a_counts.get(r["action_type"], 0) + 1
for k, v in sorted(a_counts.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}")
