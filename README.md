# Retail Supply Chain Route Efficiency & Lead-Time Analytics

**Tech Stack:** SQL, Python, Tableau-style dashboard (Plotly), MS Excel-compatible CSV outputs

A simulated logistics analytics project that analyzes supplier-to-warehouse fulfillment data
to surface cycle-time patterns, vendor lead-time variability, carrier performance/OTIF, and
operational bottlenecks worth escalating to carrier-evaluation discussions.

> **Note on data:** this project uses a synthetically generated 2-year, 6,000-shipment dataset
> (`src/generate_data.py`) across 12 suppliers, 4 warehouses, and 4 carriers, with realistic
> per-supplier lead-time profiles and per-carrier reliability/cost/OTIF differences, so the full
> pipeline can be reproduced end-to-end.

## What it does

1. **Cycle-time & transit-delay analysis** — aggregates shipment-level data by
   supplier→warehouse route to find average planned vs. actual transit time and delay patterns.
2. **Vendor lead-time variance** — computes the coefficient of variation of transit time per
   supplier, flagging the least predictable vendors (highest risk to safety-stock planning).
3. **Carrier performance & OTIF** — compares carriers on on-time rate, in-full rate, combined
   OTIF, delay, and cost, to support carrier-mix decisions.
4. **Operational bottleneck detection** — flags specific route × carrier combinations that fall
   below the median OTIF rate *and* above the median delay, i.e. the combinations most worth a
   process-improvement or carrier-reassignment conversation.

## Key results (from this run)

| Metric | Value |
|---|---|
| Total shipments analyzed | 6,000 |
| Overall OTIF rate | **58.2%** |
| Best-performing carrier (OTIF) | Carrier A |
| Weakest-performing carrier (OTIF) | Carrier C |
| Highest lead-time-variance supplier | Supplier-04 (61.0% CV) |
| Bottleneck route × carrier combos flagged | 55 (34% of shipment volume) |

## Project structure

```
data/                       generated & derived CSVs (shipments, route stats, carrier perf, bottlenecks)
src/generate_data.py        synthetic 2-year shipment generator (12 suppliers x 4 carriers x 4 DCs)
src/analysis.py             cycle-time, lead-time variance, carrier OTIF, bottleneck detection
src/load_to_sqlite.py       loads CSV into SQLite and runs sql/queries.sql
sql/queries.sql             cycle-time, CV, OTIF, bottleneck, and monthly-trend SQL views
src/build_dashboard.py      builds the interactive HTML/Plotly dashboard
dashboard/dashboard.html    self-contained interactive dashboard (open directly in a browser)
```

## How to run

```bash
pip install -r requirements.txt
python src/generate_data.py       # 1. generate synthetic shipment data
python src/analysis.py            # 2. run cycle-time / variance / OTIF / bottleneck analysis
python src/load_to_sqlite.py      # 3. (optional) run the SQL views
python src/build_dashboard.py     # 4. build dashboard/dashboard.html
```

Then open `dashboard/dashboard.html` in any browser — it's fully self-contained.

## Why a Plotly dashboard instead of a `.twbx` file?

The dashboard reproduces the same core views a Tableau workbook would have (carrier OTIF and
cost, supplier variability, worst-delay routes, on-time vs. in-full comparison), as a portable
HTML file viewable without Tableau Desktop installed. The underlying `data/*.csv` files are
Tableau/Excel-ready if you want to load them into an actual `.twbx` workbook.

## Methodology notes

- **OTIF** = On-Time AND In-Full. On-time is measured against a 10% tolerance on planned
  transit days; in-full is modeled as a carrier-specific fill-rate probability.
- **Coefficient of variation (CV)** = `std(transit_days) / mean(transit_days) * 100` — used to
  rank suppliers by lead-time unpredictability rather than just average speed.
- **Bottleneck flag** = route × carrier combination with `OTIF < median(OTIF)` AND
  `avg_delay_days > median(avg_delay_days)`, restricted to combinations with ≥5 shipments to
  avoid flagging statistically thin samples.
