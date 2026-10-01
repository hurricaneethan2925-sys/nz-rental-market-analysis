"""Reproduce a descriptive MBIE rental bond analysis with pandas and SQLite."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PAGE = "https://www.tenancy.govt.nz/about-tenancy-services/data-and-statistics/rental-bond-data/"
CITIES = ("Auckland", "Wellington City", "Christchurch City")
COLOURS = ("#3957a5", "#d17830", "#168477")
COLUMNS = {
    "timeframe": "month", "locationid": "location_id", "location": "location",
    "lodgedbonds": "lodged_bonds", "activebonds": "active_bonds",
    "closedbonds": "closed_bonds", "medianrent": "median_rent",
    "geometricmeanrent": "geometric_mean_rent",
}
CAUTION = ("Provisional MBIE data: system migration and revisions can affect comparisons. "
           "These are new private tenancy rents, not rents paid by every tenant.")


def clean_data(path: Path):
    """Validate keys; retain missing numeric values rather than inventing zeroes."""
    raw = pd.read_csv(path, dtype=str, encoding="utf-8-sig", keep_default_na=False)
    renamed = {c: COLUMNS.get(re.sub(r"[^a-z0-9]", "", c.lower()), c) for c in raw}
    frame = raw.rename(columns=renamed)
    missing = set(COLUMNS.values()) - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}. Use the monthly TA CSV.")
    frame = frame[list(COLUMNS.values())].copy()
    if frame.columns.duplicated().any():
        raise ValueError("Ambiguous duplicate column names.")
    # The supplied release uses day/month/year. ISO dates are also accepted.
    values = frame["month"].str.strip()
    parsed = pd.to_datetime(values, format="%d/%m/%Y", errors="coerce")
    parsed = parsed.fillna(pd.to_datetime(values, format="%Y-%m-%d", errors="coerce"))
    if parsed.isna().any() or (parsed.dt.day != 1).any():
        raise ValueError("Dates must be valid month-start dates (D/M/YYYY or YYYY-MM-DD).")
    frame["month"] = parsed.dt.strftime("%Y-%m-%d")
    frame["location_id"] = pd.to_numeric(frame["location_id"], errors="raise")
    if (frame["location_id"] % 1 != 0).any():
        raise ValueError("Location IDs must be integers.")
    frame["location"] = frame["location"].str.strip()
    if frame.duplicated(["month", "location_id"]).any():
        raise ValueError("Duplicate location/month keys: investigate before aggregation.")
    numeric = ["lodged_bonds", "active_bonds", "closed_bonds", "median_rent", "geometric_mean_rent"]
    missing_tokens = {"", "..", "...", "-", "na", "n/a", "null", "suppressed", "s", "c"}
    for col in numeric:
        text = frame[col].str.strip().str.replace(",", "", regex=False)
        text = text.mask(text.str.lower().isin(missing_tokens))
        frame[col] = pd.to_numeric(text, errors="raise")
        if (frame[col].dropna() < 0).any():
            raise ValueError(f"Negative value in {col}.")
        if col.endswith("bonds") and (frame[col].dropna() % 1 != 0).any():
            raise ValueError(f"Non-integer count in {col}.")
    rent_cols = ["median_rent", "geometric_mean_rent"]
    zero_rents = int((frame[rent_cols] == 0).sum().sum())
    frame[rent_cols] = frame[rent_cols].replace(0, float("nan"))
    # ALL (-99) and unallocated (-1) would contaminate a TA ranking.
    keep = (frame.location_id > 0) & frame.location.ne("")
    cleaned = frame.loc[keep].sort_values(["location_id", "month"]).reset_index(drop=True)
    if cleaned.empty:
        raise ValueError("No named territorial-authority rows found.")
    quality = {
        "input_rows": len(raw), "retained_ta_rows": len(cleaned),
        "excluded_aggregate_or_unallocated_rows": int((~keep).sum()),
        "zero_rent_values_treated_as_missing": zero_rents,
        "duplicate_keys": 0,
        "missing_numeric_values": {k: int(v) for k, v in cleaned[numeric].isna().sum().items()},
        "min_month": cleaned.month.min(), "max_month": cleaned.month.max(),
        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    return cleaned, quality


def make_database(frame, path):
    """Replace generated data and views without touching the source CSV."""
    connection = sqlite3.connect(path)
    frame.to_sql("rental_monthly", connection, if_exists="replace", index=False)
    connection.execute("CREATE UNIQUE INDEX rental_key ON rental_monthly(location_id, month)")
    connection.executescript((ROOT / "sql/rental_analysis.sql").read_text(encoding="utf-8"))
    return connection


def finish_chart(fig, path):
    fig.text(0.09, 0.025, "Source: MBIE / Tenancy Services. Provisional data; migration may affect comparisons.",
             fontsize=8, color="#54616d")
    fig.savefig(path, dpi=180, facecolor="white")
    plt.close(fig)


def plot_results(trends, latest, directory):
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.titleweight": "bold", "axes.labelcolor": "#344454"})
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    for city, colour in zip(CITIES, COLOURS):
        subset = trends[trends.location.eq(city)].copy()
        subset.index = pd.to_datetime(subset.month)
        # Reindex to show a gap rather than bridge missing months.
        subset = subset.reindex(pd.date_range(trends.month.min(), trends.month.max(), freq="MS"))
        axes[0].plot(subset.index, subset.median_rent, color=colour, label=city, lw=2)
        axes[1].plot(subset.index, subset.lodged_bonds, color=colour, lw=1.6)
    axes[0].set(title="New tenancy rents across three NZ areas", ylabel="Median weekly rent (NZD)")
    axes[0].legend(frameon=False, ncol=3, fontsize=9)
    axes[1].set(title="Reported bond lodgements by tenancy start month", ylabel="Bonds (rounded counts)", xlabel="Month")
    for axis in axes:
        axis.grid(axis="y", alpha=0.18)
    fig.tight_layout(rect=(0, 0.055, 1, 1))
    finish_chart(fig, directory / "rent_trends.png")

    comparison = latest[latest.location.isin(CITIES)].sort_values("median_rent")
    fig, ax = plt.subplots(figsize=(9, 4.7))
    ax.barh(comparison.location, comparison.median_rent, color="#168477", height=0.55)
    for i, value in enumerate(comparison.median_rent):
        if pd.notna(value):
            ax.text(value + 8, i, f"${value:,.0f}", va="center", weight="bold")
    ax.set(xlabel="Median weekly rent (NZD)", title=f"New tenancy rent comparison | {latest.month.max()[:7]}")
    ax.set_xlim(0, comparison.median_rent.max() * 1.18)
    ax.grid(axis="x", alpha=0.15)
    ax.set_axisbelow(True)
    fig.tight_layout(rect=(0, 0.09, 1, 1))
    finish_chart(fig, directory / "latest_comparison.png")


def money(value):
    return "unavailable" if pd.isna(value) else f"NZ${value:,.0f}"


def write_report(latest, quality, out):
    lines = ["# NZ rental market findings", "", f"Snapshot: {quality['max_month'][:7]}. Input file: {quality['input_file']}.",
             "", f"> {CAUTION}", "", "## Three-area comparison", "",
             "| Area | Median weekly rent | Same month one year earlier | YoY change |",
             "| --- | ---: | ---: | ---: |"]
    for city in CITIES:
        row = latest[latest.location.eq(city)]
        if row.empty:
            lines.append(f"| {city} | unavailable | unavailable | unavailable |")
            continue
        row = row.iloc[0]
        change = "unavailable" if pd.isna(row.rent_yoy_pct) else f"{row.rent_yoy_pct:+.2f}%"
        lines.append(f"| {city} | {money(row.median_rent)} | {money(row.prior_year_median)} | {change} |")
    lines += ["", "## Interpretation", "",
              "These figures describe the mix of new private tenancies recorded in each area. "
              "Auckland covers a much larger territory than Wellington City or Christchurch City. "
              "Differences are not adjusted for bedrooms, dwelling type, inflation or income.", "",
              "The analysis does not establish why rents changed. Changes in the property mix, "
              "reporting or systems may contribute. Bond activity is not a direct measure of rental demand.", "",
              "## Validation", "", f"- Source rows: {quality['input_rows']:,}.",
              f"- Named TA rows retained: {quality['retained_ta_rows']:,}.",
              f"- National/unallocated rows excluded: {quality['excluded_aggregate_or_unallocated_rows']:,}.",
              "- Unique month/area keys validated; missing values are not replaced with zero.",
              "- Year-on-year comparisons join the same calendar month; incomplete years are labelled.", "",
              f"Data: [Ministry of Business, Innovation and Employment]({SOURCE_PAGE}). "
              "CC BY 3.0 NZ. Analysis and charts are derived outputs, not official MBIE conclusions."]
    (out / "findings.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data/raw/mbie_monthly_ta_2026-09.csv")
    parser.add_argument("--start-year", type=int, default=2020, help="First year for trend charts")
    args = parser.parse_args()
    frame, quality = clean_data(args.input)
    start = f"{args.start_year:04d}-01-01"
    trends = frame[frame.month.ge(start) & frame.location.isin(CITIES)]
    if trends.empty:
        raise ValueError("No city observations for the requested start year.")
    out, images = ROOT / "outputs", ROOT / "images"
    out.mkdir(exist_ok=True); images.mkdir(exist_ok=True)
    with make_database(frame, out / "rental.db") as connection:
        for view in ("monthly_yoy", "annual_activity", "latest_snapshot", "latest_growth_ranking"):
            result = pd.read_sql_query(f"SELECT * FROM {view}", connection)
            if view == "latest_growth_ranking":
                result = result.sort_values(["growth_rank", "location"])
            result.to_csv(out / f"{view}.csv", index=False)
        latest = pd.read_sql_query("SELECT * FROM latest_snapshot", connection)
    quality["input_file"] = args.input.name
    (out / "data_quality.json").write_text(json.dumps(quality, indent=2), encoding="utf-8")
    plot_results(trends, latest, images)
    write_report(latest, quality, out)
    print(f"Processed {len(frame):,} TA rows through {quality['max_month']}.")
    print(f"Results: {out}\nCharts: {images}\n{CAUTION}")


if __name__ == "__main__":
    main()
