"""
Parse the repeated Yale CELI tracker snapshots.

The primary new output keeps one row per company and snapshot so the project
can study movement from continued operation to an unresolved exit process and
then to a reported completed outcome. Classification is deliberately
conservative: generic statements that a company plans to leave do not count
as evidence that a sale or closure has been completed.

The older one-row-per-company outputs are retained so existing scripts remain
reproducible while the new state-transition analysis is developed.

Outputs:
  data/analysis/firm_snapshot_states.csv — one row per firm and Yale snapshot
                                          with a provisional state
  data/analysis/firms_exit_panel.csv  — one row per firm, exit status + action
                                        text + exit-timing columns
  data/analysis/firms_exiters.csv     — Grade A/B firms only (the main sample)

Yale grade legend:
  A = Clean break (suspended + announced exit)
  B = Suspension / scaling back
  C = Reducing activity
  D = Buying time / minimal compliance
  F = Business as usual / still operating
"""

import csv
import re
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
YALE_DIR = DATA_DIR / "raw" / "yale"
OUT_DIR = DATA_DIR / "analysis"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def snapshot_date(path: Path) -> str:
    """Filename YYMMDD.csv → ISO date string."""
    stem = path.stem
    return f"20{stem[:2]}-{stem[2:4]}-{stem[4:6]}"


SNAPSHOT_FILES = sorted(YALE_DIR.glob("*.csv"), key=lambda p: p.stem)
SNAPSHOT_DATES = [snapshot_date(p) for p in SNAPSHOT_FILES]
LATEST = SNAPSHOT_FILES[-1]
EARLIEST = SNAPSHOT_FILES[0]

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
    r"\b(seiz(ed|ure)|national(is|iz)(ed|ation)|expropriat|confiscat|"
    r"government (took|assumed)|temporary (state )?management|"
    r"presidential decree.{0,30}(shares|stake|control))\b",
    re.IGNORECASE,
)
SUSPENDED_PATTERNS = re.compile(
    r"\b(suspend(ed)?|halt(ed)?|pause(d)?|stop(ped)?|ceas(ed)?|discontinu)\b",
    re.IGNORECASE,
)

# Conservative patterns for the new snapshot-level state file. Unlike the
# legacy SOLD_PATTERNS, these do not treat a general withdrawal announcement
# as proof of a completed transaction.
COMPLETED_SALE_PATTERNS = re.compile(
    r"\b(sold|sale completed|completed (the )?sale|divested|divestiture completed|"
    r"transferred (its |the )?(business|assets|stake|operations|ownership)|"
    r"handed over (its |the )?(business|assets|operations)|"
    r"new owner|management buyout)\b",
    re.IGNORECASE,
)
COMPLETED_CLOSURE_PATTERNS = re.compile(
    r"\b(liquidated|liquidation completed|dissolved|wound up|"
    r"closed (all |its |the )?(offices|operations|business|subsidiar)|"
    r"ceased (all |its |the )?(operations|business))\b",
    re.IGNORECASE,
)
EXIT_PROCESS_PATTERNS = re.compile(
    r"\b(announc(ed|es|ing)?.{0,40}(exit|leave|withdraw)|"
    r"plans? to (exit|leave|withdraw)|seeking (a )?buyer|"
    r"sale process|negotiat(ing|ions?).{0,30}(sale|buyer)|"
    r"suspend(ed|ing)?|halt(ed|ing)?|paus(ed|ing)?|"
    r"wind(ing)? down|withdraw(ing|al)?|exit(ing)?)\b",
    re.IGNORECASE,
)

# Firms whose Russian assets were placed under state "temporary management"
# or otherwise seized. The action text often reads like a sale or exit, so
# the regex misclassifies them; these overrides force the seized code, which
# downstream scripts treat as a separate competing risk (dropped from the
# sell-vs-walk margin). Hand-checked against press coverage; extend as the
# KSE LeaveRussia validation (see README) proceeds.
SEIZED_OVERRIDES = {
    "Danone",
    "Carlsberg",
    "Fortum",
    "Uniper",
    "Baltika",
}


def classify_action(action: str, firm_name: str = "") -> str:
    action = action or ""
    if firm_name in SEIZED_OVERRIDES:
        return "seized"
    # Seizure takes priority: seized firms' action text usually also matches
    # exit/sale language, but the transfer was involuntary — it is a distinct
    # competing risk, not a chosen exit mode.
    if NATIONALIZED_PATTERNS.search(action):
        return "seized"
    if SOLD_PATTERNS.search(action):
        return "sold"
    if WRITEDOWN_PATTERNS.search(action):
        return "writedown_mentioned"
    if SUSPENDED_PATTERNS.search(action):
        return "suspended"
    return "other"


def classify_snapshot_state(action: str, grade: str, firm_name: str = "") -> tuple[str, str]:
    """Return (state, ambiguous_flag) for the new transition skeleton.

    The action text is given priority for explicit completed outcomes. Grades
    A and B without explicit completion evidence are treated as unresolved,
    because the Yale grade records withdrawal posture rather than legal title.
    """
    action = action or ""
    if firm_name in SEIZED_OVERRIDES or NATIONALIZED_PATTERNS.search(action):
        return "state_imposed_loss_of_control", "no"
    if COMPLETED_SALE_PATTERNS.search(action):
        return "sale_completed", "no"
    if COMPLETED_CLOSURE_PATTERNS.search(action):
        return "closure_completed", "no"
    if grade in ("A", "B") or EXIT_PROCESS_PATTERNS.search(action):
        # Grade A can describe a clean break without establishing how or when
        # ownership changed. Preserve that uncertainty for later review.
        return "exit_announced_unresolved", "yes" if grade == "A" else "no"
    if grade in ("C", "D", "F"):
        return "still_operating", "no"
    return "unclassified", "yes"


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


# ── Load all snapshots chronologically ─────────────────────────────────────

snapshots = []  # list of (iso_date, {name: row})
for path in SNAPSHOT_FILES:
    snapshots.append((snapshot_date(path), load_snapshot(path)))

latest_firms = snapshots[-1][1]
early_firms = snapshots[0][1]

print(f"Snapshots loaded: {len(snapshots)} ({SNAPSHOT_DATES[0]} … {SNAPSHOT_DATES[-1]})")

# ── Build the snapshot-level state skeleton ───────────────────────────────

snapshot_state_rows = []
absorbing_state_by_firm = {}
for snap_date, firms in snapshots:
    for name, row in firms.items():
        grade = (row.get("yaleGrade") or "").strip()
        action = (row.get("action") or "").strip()
        state, ambiguous = classify_snapshot_state(action, grade, name)
        prior_terminal = absorbing_state_by_firm.get(name)
        if state == "state_imposed_loss_of_control":
            # Later state intervention supersedes an earlier reported status.
            absorbing_state_by_firm[name] = state
        elif prior_terminal:
            # A completed outcome remains completed even if a later Yale
            # description no longer repeats the transaction or closure text.
            state, ambiguous = prior_terminal, "no"
        elif state in ("sale_completed", "closure_completed"):
            absorbing_state_by_firm[name] = state
        snapshot_state_rows.append({
            "snapshot_date": snap_date,
            "name": name,
            "country": (row.get("country") or "").strip(),
            "industry": (row.get("industry") or "").strip(),
            "yale_grade": grade,
            "provisional_state": state,
            "ambiguous": ambiguous,
            "action_text": action,
        })

snapshot_states_out = OUT_DIR / "firm_snapshot_states.csv"
snapshot_state_fields = [
    "snapshot_date", "name", "country", "industry", "yale_grade",
    "provisional_state", "ambiguous", "action_text",
]
with open(snapshot_states_out, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=snapshot_state_fields)
    writer.writeheader()
    writer.writerows(snapshot_state_rows)

print(f"Snapshot states: {len(snapshot_state_rows)} rows → {snapshot_states_out}")

# ── Build firm-level panel with exit timing ────────────────────────────────

panel_rows = []
for name, row in latest_firms.items():
    grade = (row.get("yaleGrade") or "").strip()
    action = (row.get("action") or "").strip()
    industry = (row.get("industry") or "").strip()
    country = (row.get("country") or "").strip()

    early_row = early_firms.get(name, {})
    early_grade = (early_row.get("yaleGrade") or "").strip()

    action_type = classify_action(action, name)

    # Exit timing: first snapshot at which the firm carries Grade A
    # (completed exit) and first at which it carries Grade A or B.
    # Firms already at that grade in the earliest snapshot are left-censored:
    # the true event date is somewhere in Feb–Dec 2022.
    first_a_date = ""
    first_ab_date = ""
    for snap_date, firms in snapshots:
        g = (firms.get(name, {}).get("yaleGrade") or "").strip()
        if not first_ab_date and g in ("A", "B"):
            first_ab_date = snap_date
        if not first_a_date and g == "A":
            first_a_date = snap_date
        if first_a_date and first_ab_date:
            break

    left_censored = "yes" if (first_a_date == SNAPSHOT_DATES[0]) else "no"

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
            "first_grade_a_date": first_a_date,
            "first_grade_ab_date": first_ab_date,
            "timing_left_censored": left_censored,
        }
    )

# Sort by grade then name
grade_order = {"A": 0, "B": 1, "C": 2, "D": 3, "F": 4, "": 5}
panel_rows.sort(key=lambda r: (grade_order.get(r["grade_latest"], 5), r["name"]))

# ── Write full panel ───────────────────────────────────────────────────────

panel_out = OUT_DIR / "firms_exit_panel.csv"
fields = ["name", "country", "industry", "grade_latest", "grade_dec2022",
          "action_type", "in_dec2022_snapshot",
          "first_grade_a_date", "first_grade_ab_date", "timing_left_censored",
          "action_text"]

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

n_lc = sum(1 for r in panel_rows if r["timing_left_censored"] == "yes")
n_timed = sum(1 for r in panel_rows if r["first_grade_a_date"])
print(f"\nExit timing: {n_timed} firms with a first-Grade-A date "
      f"({n_lc} left-censored at {SNAPSHOT_DATES[0]})")
