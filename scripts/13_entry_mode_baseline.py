"""Build a preliminary entry-mode file and a transaction baseline.

The firm-level file combines conservative evidence from Yale action text and
Orbis ownership fields. It does not infer a distributor relationship from the
absence of an Orbis match. The transaction file describes Bloomberg records
after 24 February 2022. Its stake categories are transaction characteristics,
not pre-2022 entry modes.

Inputs
------
data/raw/bloomberg/bloomberg_data_russia.csv
data/analysis/firms_exit_panel.csv
data/analysis/orbis_subsidiaries.csv

Outputs
-------
data/analysis/entry_mode_review_queue.csv
data/analysis/bloomberg_post_rupture_transactions.csv
data/analysis/results_13_entry_mode_baseline.txt
"""

import csv
import html
import math
import re
import statistics
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ANALYSIS = DATA / "analysis"
BLOOMBERG = DATA / "raw" / "bloomberg" / "bloomberg_data_russia.csv"
YALE = ANALYSIS / "firms_exit_panel.csv"
ORBIS = ANALYSIS / "orbis_subsidiaries.csv"

REVIEW_OUT = ANALYSIS / "entry_mode_review_queue.csv"
DEALS_OUT = ANALYSIS / "bloomberg_post_rupture_transactions.csv"
RESULTS_OUT = ANALYSIS / "results_13_entry_mode_baseline.txt"

RUPTURE_DATE = date(2022, 2, 24)
LEGAL_SUFFIXES = {
    "AB", "AG", "AS", "ASA", "BV", "CO", "CORP", "CORPORATION",
    "GMBH", "INC", "JSC", "LIMITED", "LLC", "LTD", "NV", "OAO",
    "OOO", "OYJ", "PJSC", "PLC", "SA", "SE", "SPA", "ZAO",
}

JV_PATTERN = re.compile(r"\bjoint venture(?:s)?\b|\bJ\.?V\.?\b", re.I)
CONTRACT_PATTERN = re.compile(
    r"\bdistribut(?:or|ion|orship)\b|"
    r"\blicen[cs](?:e|ed|ing|ee|or)\b|"
    r"\bfranchis(?:e|ed|ing|ee|or)\b",
    re.I,
)


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        return list(csv.DictReader(f))


def normalize_name(value):
    """Normalize a name for strict, one-to-one matching."""
    value = html.unescape(value or "").upper().replace("/THE", " ")
    tokens = re.sub(r"[^A-Z0-9]+", " ", value).split()
    while tokens and tokens[-1] in LEGAL_SUFFIXES:
        tokens.pop()
    return " ".join(tokens)


def parse_float(value, lower=None, upper=None):
    try:
        number = float((value or "").strip().replace(",", ""))
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    if lower is not None and number < lower:
        return None
    if upper is not None and number > upper:
        return None
    return number


def parse_date(value):
    try:
        return date.fromisoformat((value or "").strip())
    except ValueError:
        return None


def unique_name_index(rows, field):
    """Keep normalized names that identify exactly one original name."""
    candidates = defaultdict(set)
    for row in rows:
        original = (row.get(field) or "").strip()
        normalized = normalize_name(original)
        if normalized:
            candidates[normalized].add(original)
    return {
        normalized: next(iter(originals))
        for normalized, originals in candidates.items()
        if len(originals) == 1
    }


def classify_orbis_parent(subsidiaries):
    """Use reported direct stakes; do not treat missing stakes as zero."""
    stakes = []
    for row in subsidiaries:
        stake = parse_float(row.get("guo_direct_pct"), lower=0, upper=100)
        if stake is not None and stake > 0:
            stakes.append(stake)

    if not stakes:
        return "", ""

    has_shared = any(10 <= stake < 95 for stake in stakes)
    has_full = any(stake >= 95 for stake in stakes)
    if has_shared and has_full:
        category = "mixed_equity_stakes"
    elif has_shared:
        category = "shared_ownership"
    elif has_full:
        category = "wholly_owned"
    else:
        category = "minority_below_10_percent"
    return category, ";".join(f"{stake:g}" for stake in sorted(set(stakes)))


def build_review_queue(yale_rows, orbis_rows):
    orbis_names = unique_name_index(orbis_rows, "guo_name")
    subsidiaries_by_parent = defaultdict(list)
    for row in orbis_rows:
        subsidiaries_by_parent[(row.get("guo_name") or "").strip()].append(row)

    output = []
    for row in yale_rows:
        text = html.unescape(row.get("action_text") or "")
        normalized = normalize_name(row.get("name"))
        matched_parent = orbis_names.get(normalized, "")
        orbis_class, stakes = classify_orbis_parent(
            subsidiaries_by_parent.get(matched_parent, [])
        )

        explicit_jv = bool(JV_PATTERN.search(text))
        explicit_contract = bool(CONTRACT_PATTERN.search(text))
        has_equity = bool(orbis_class)

        if explicit_contract and (explicit_jv or has_equity):
            provisional_mode = "mixed"
        elif explicit_jv or orbis_class in {"shared_ownership", "mixed_equity_stakes"}:
            provisional_mode = "joint_venture"
        elif explicit_contract:
            provisional_mode = "contractual"
        elif orbis_class == "wholly_owned":
            provisional_mode = "wholly_owned"
        else:
            provisional_mode = "unclassified"

        evidence = []
        if explicit_jv:
            evidence.append("Yale text explicitly mentions a joint venture")
        if explicit_contract:
            evidence.append("Yale text explicitly mentions a distribution, license, or franchise arrangement")
        if matched_parent:
            evidence.append("strict normalized name match to Orbis parent")
        if orbis_class:
            evidence.append(f"Orbis direct-stake category: {orbis_class}")

        output.append({
            "firm_name": row.get("name", ""),
            "home_country": row.get("country", ""),
            "industry": row.get("industry", ""),
            "provisional_entry_mode": provisional_mode,
            "requires_manual_review": "yes",
            "evidence_summary": "; ".join(evidence),
            "orbis_parent_match": matched_parent,
            "orbis_direct_stakes_pct": stakes,
            "reported_action_type": row.get("action_type", ""),
            "first_reported_exit_date": row.get("first_grade_a_date", ""),
            "first_reported_reduction_or_exit_date": row.get("first_grade_ab_date", ""),
            "timing_left_censored": row.get("timing_left_censored", ""),
            "yale_action_text": text,
        })
    return output


def is_russian_target(row):
    if (row.get("Target Country/Region ISO Code") or "").strip() == "RU":
        return True
    text = " ".join([
        row.get("Target Name") or "",
        row.get("Deal Description") or "",
    ]).lower()
    return "russia" in text or "russian" in text


def build_transaction_sample(rows):
    output = []
    for row in rows:
        announced = parse_date(row.get("Announce Date"))
        seller_country = (row.get("Seller Country/Region ISO Code") or "").strip()
        if (
            announced is None
            or announced < RUPTURE_DATE
            or not seller_country
            or seller_country == "RU"
            or not is_russian_target(row)
        ):
            continue

        percent_sought = parse_float(row.get("Percent Sought"), lower=0, upper=100)
        if percent_sought is None or percent_sought == 0:
            stake_category = "unclassified"
        elif percent_sought >= 95:
            stake_category = "full_interest_offered"
        else:
            stake_category = "shared_interest_offered"

        resolved = parse_date(row.get("Completion/Termination Date"))
        rupture_days = ""
        announcement_days = ""
        if resolved is not None and resolved >= RUPTURE_DATE:
            rupture_days = (resolved - RUPTURE_DATE).days
            if resolved >= announced:
                announcement_days = (resolved - announced).days

        value = parse_float(row.get("Current/Completed Total Value"), lower=0)
        value_source = "Current/Completed Total Value"
        if value is None:
            value = parse_float(row.get("Announced Total Value (mil.)"), lower=0)
            value_source = "Announced Total Value (mil.)" if value is not None else ""

        output.append({
            "action_id": row.get("Action ID", ""),
            "seller_name": row.get("Seller Name", ""),
            "seller_country_iso": seller_country,
            "target_name": row.get("Target Name", ""),
            "acquirer_name": row.get("Acquirer Name", ""),
            "announce_date": announced.isoformat(),
            "completion_or_termination_date": resolved.isoformat() if resolved else "",
            "deal_status": row.get("Deal Status", "").strip(),
            "deal_type": row.get("Deal Type", "").strip(),
            "percent_sought": "" if percent_sought is None else f"{percent_sought:g}",
            "transaction_stake_category": stake_category,
            "days_from_rupture_to_recorded_resolution": rupture_days,
            "days_from_announcement_to_recorded_resolution": announcement_days,
            "reported_value_millions": "" if value is None else f"{value:g}",
            "reported_value_currency": row.get("Currency of Deal", "").strip(),
            "reported_value_source": value_source,
            "deal_description": row.get("Deal Description", ""),
        })
    return output


def fisher_two_sided(a, b, c, d):
    """Two-sided Fisher exact test for a 2-by-2 table."""
    total = a + b + c + d
    row_one = a + b
    col_one = a + c

    def probability(x):
        return (
            math.comb(col_one, x)
            * math.comb(total - col_one, row_one - x)
            / math.comb(total, row_one)
        )

    observed = probability(a)
    low = max(0, row_one - (total - col_one))
    high = min(row_one, col_one)
    return sum(
        probability(x)
        for x in range(low, high + 1)
        if probability(x) <= observed + 1e-15
    )


def summarize(review_rows, deal_rows):
    lines = []
    mode_counts = Counter(row["provisional_entry_mode"] for row in review_rows)
    lines.append("ENTRY-MODE REVIEW FILE")
    lines.append(f"Firms: {len(review_rows)}")
    for category in ["wholly_owned", "joint_venture", "contractual", "mixed", "unclassified"]:
        lines.append(f"  {category}: {mode_counts[category]}")
    lines.append("")
    lines.append("Every classification requires manual review. The Orbis export is not a")
    lines.append("historical ownership file, and Yale action descriptions were not designed")
    lines.append("to measure entry mode.")
    lines.append("")
    lines.append("BLOOMBERG TRANSACTION BASELINE")
    lines.append("Sample: foreign-seller transactions announced on or after 2022-02-24")
    lines.append("with a Russian target or an explicit Russia reference.")
    lines.append(f"Transactions: {len(deal_rows)}")
    lines.append(f"Unique sellers: {len(set(row['seller_name'] for row in deal_rows))}")

    stats = {}
    for category in ["full_interest_offered", "shared_interest_offered", "unclassified"]:
        sample = [row for row in deal_rows if row["transaction_stake_category"] == category]
        completed = [row for row in sample if row["deal_status"] == "Completed"]
        completed_days = [
            int(row["days_from_rupture_to_recorded_resolution"])
            for row in completed
            if row["days_from_rupture_to_recorded_resolution"] != ""
        ]
        disclosed = [row for row in sample if row["reported_value_millions"] != ""]
        stats[category] = (len(sample), len(completed))
        share = len(completed) / len(sample) if sample else float("nan")
        median = statistics.median(completed_days) if completed_days else float("nan")
        coverage = len(disclosed) / len(sample) if sample else float("nan")
        lines.append("")
        lines.append(f"{category}:")
        lines.append(f"  transactions: {len(sample)}")
        lines.append(f"  completed: {len(completed)} ({share:.1%})")
        lines.append(f"  median days from rupture to completion: {median:g}")
        lines.append(f"  reported-value coverage: {len(disclosed)} ({coverage:.1%})")

    full_n, full_completed = stats["full_interest_offered"]
    shared_n, shared_completed = stats["shared_interest_offered"]
    difference = shared_completed / shared_n - full_completed / full_n
    p_value = fisher_two_sided(
        full_completed,
        full_n - full_completed,
        shared_completed,
        shared_n - shared_completed,
    )
    lines.append("")
    lines.append("Unadjusted comparison:")
    lines.append(f"  shared-minus-full completion difference: {difference:.1%}")
    lines.append(f"  two-sided Fisher exact p-value: {p_value:.3f}")
    lines.append("")
    lines.append("INTERPRETATION")
    lines.append("This is a transaction-selection result, not an entry-mode effect. Percent")
    lines.append("sought is observed after the rupture. Firms without a sale attempt are")
    lines.append("absent, and distributor or license relationships generally do not appear.")
    lines.append("Reported values use different currencies and cannot be compared without")
    lines.append("date-specific conversion. The file does not report accounting write-downs.")
    return "\n".join(lines) + "\n"


def write_csv(path, rows):
    if not rows:
        raise ValueError(f"No rows generated for {path}")
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    review_rows = build_review_queue(read_csv(YALE), read_csv(ORBIS))
    deal_rows = build_transaction_sample(read_csv(BLOOMBERG))
    write_csv(REVIEW_OUT, review_rows)
    write_csv(DEALS_OUT, deal_rows)
    RESULTS_OUT.write_text(summarize(review_rows, deal_rows), encoding="utf-8")
    print(f"Wrote {len(review_rows)} firms to {REVIEW_OUT}")
    print(f"Wrote {len(deal_rows)} transactions to {DEALS_OUT}")
    print(f"Wrote baseline summary to {RESULTS_OUT}")


if __name__ == "__main__":
    main()
