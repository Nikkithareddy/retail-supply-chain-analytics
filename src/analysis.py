"""
Retail Supply Chain Route Efficiency & Lead-Time Analytics
-------------------------------------------------------------
1. Analyze supplier-to-warehouse fulfillment data for cycle-time patterns & transit delays.
2. Evaluate vendor lead-time variance and carrier performance.
3. Identify operational bottlenecks (route x carrier combinations) for process improvement.
"""
import json
import numpy as np
import pandas as pd

df = pd.read_csv("data/shipments.csv", parse_dates=["ship_date", "delivery_date"])
df["delay_days"] = df["actual_transit_days"] - df["planned_transit_days"]
df["route"] = df["supplier"] + " -> " + df["warehouse"]

# ---------- 1. Cycle-time patterns & transit delays across routes ----------
route_stats = (df.groupby("route")
                 .agg(shipments=("shipment_id", "count"),
                      avg_planned_days=("planned_transit_days", "mean"),
                      avg_actual_days=("actual_transit_days", "mean"),
                      avg_delay_days=("delay_days", "mean"),
                      otif_rate=("otif", "mean"))
                 .round(2)
                 .sort_values("avg_delay_days", ascending=False))
route_stats.to_csv("data/route_cycle_time_stats.csv")

# ---------- 2. Vendor (supplier) lead-time variance ----------
supplier_variance = (df.groupby("supplier")
                       .agg(shipments=("shipment_id", "count"),
                            mean_transit_days=("actual_transit_days", "mean"),
                            std_transit_days=("actual_transit_days", "std"),
                            otif_rate=("otif", "mean"))
                       .round(2))
supplier_variance["cv_pct"] = (100 * supplier_variance["std_transit_days"]
                                / supplier_variance["mean_transit_days"]).round(1)
supplier_variance = supplier_variance.sort_values("cv_pct", ascending=False)
supplier_variance.to_csv("data/supplier_lead_time_variance.csv")

# ---------- 3. Carrier performance & OTIF ----------
carrier_perf = (df.groupby("carrier")
                  .agg(shipments=("shipment_id", "count"),
                       on_time_rate=("on_time", "mean"),
                       in_full_rate=("in_full", "mean"),
                       otif_rate=("otif", "mean"),
                       avg_delay_days=("delay_days", "mean"),
                       avg_cost_usd=("cost_usd", "mean"))
                  .round(3)
                  .sort_values("otif_rate", ascending=False))
carrier_perf.to_csv("data/carrier_performance.csv")

# ---------- 4. Operational bottleneck detection ----------
# Flag route x carrier combos with below-median OTIF AND above-median delay
combo = (df.groupby(["route", "carrier"])
           .agg(shipments=("shipment_id", "count"),
                otif_rate=("otif", "mean"),
                avg_delay_days=("delay_days", "mean"))
           .reset_index())
combo = combo[combo["shipments"] >= 5]  # ignore statistically thin combos
otif_median = combo["otif_rate"].median()
delay_median = combo["avg_delay_days"].median()
bottlenecks = combo[(combo["otif_rate"] < otif_median) & (combo["avg_delay_days"] > delay_median)]
bottlenecks = bottlenecks.sort_values(["avg_delay_days"], ascending=False).round(2)
bottlenecks.to_csv("data/operational_bottlenecks.csv", index=False)

summary = {
    "total_shipments": int(len(df)),
    "overall_otif_rate_pct": round(100 * df["otif"].mean(), 1),
    "overall_avg_delay_days": round(df["delay_days"].mean(), 2),
    "best_carrier_by_otif": carrier_perf.index[0],
    "worst_carrier_by_otif": carrier_perf.index[-1],
    "highest_variance_supplier": supplier_variance.index[0],
    "highest_variance_supplier_cv_pct": float(supplier_variance.iloc[0]["cv_pct"]),
    "bottleneck_route_carrier_combos_flagged": int(len(bottlenecks)),
    "bottleneck_share_of_shipments_pct": round(
        100 * bottlenecks["shipments"].sum() / combo["shipments"].sum(), 1),
}
with open("data/summary_metrics.json", "w") as f:
    json.dump(summary, f, indent=2)

print(json.dumps(summary, indent=2))
print("\nCarrier performance:\n", carrier_perf.to_string())
print("\nTop 5 bottleneck route x carrier combos:\n", bottlenecks.head(5).to_string(index=False))
