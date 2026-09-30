"""Build a self-contained interactive HTML dashboard (Tableau-style views)."""
import json
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

carrier_perf = pd.read_csv("data/carrier_performance.csv")
supplier_var = pd.read_csv("data/supplier_lead_time_variance.csv")
route_stats = pd.read_csv("data/route_cycle_time_stats.csv")
with open("data/summary_metrics.json") as f:
    summary = json.load(f)

fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        "Carrier OTIF Rate & Avg. Cost",
        "Supplier Lead-Time Variability (CV %)",
        "Top 10 Routes by Avg. Delay (days)",
        "On-Time vs. In-Full Rate by Carrier",
    ),
    specs=[[{"type": "bar"}, {"type": "bar"}],
           [{"type": "bar"}, {"type": "scatter"}]],
    vertical_spacing=0.15, horizontal_spacing=0.10,
)

fig.add_trace(go.Bar(x=carrier_perf["carrier"], y=carrier_perf["otif_rate"] * 100,
                      name="OTIF %", marker_color="#2f6db5"), row=1, col=1)

top_var = supplier_var.sort_values("cv_pct", ascending=False).head(8)
fig.add_trace(go.Bar(x=top_var["supplier"], y=top_var["cv_pct"], name="CV %",
                      marker_color="#c96a6a", showlegend=False), row=1, col=2)

top_delay = route_stats.sort_values("avg_delay_days", ascending=False).head(10)
fig.add_trace(go.Bar(x=top_delay["route"], y=top_delay["avg_delay_days"], name="Avg delay (days)",
                      marker_color="#e0a336", showlegend=False), row=2, col=1)

fig.add_trace(go.Scatter(x=carrier_perf["on_time_rate"] * 100, y=carrier_perf["in_full_rate"] * 100,
                          mode="markers+text", text=carrier_perf["carrier"], textposition="top center",
                          marker=dict(size=16, color="#4caf7d"), showlegend=False), row=2, col=2)

fig.update_layout(
    title=dict(text="Retail Supply Chain Route Efficiency & Lead-Time Analytics", x=0.5, font=dict(size=20)),
    height=860, width=1180, template="plotly_white", margin=dict(t=90),
)
fig.update_xaxes(tickangle=-35, row=2, col=1)
fig.update_yaxes(title_text="OTIF %", row=1, col=1)
fig.update_yaxes(title_text="CV %", row=1, col=2)
fig.update_yaxes(title_text="Avg delay (days)", row=2, col=1)
fig.update_xaxes(title_text="On-time rate %", row=2, col=2)
fig.update_yaxes(title_text="In-full rate %", row=2, col=2)

kpi_html = f"""
<div style="display:flex;gap:24px;justify-content:center;font-family:Arial;margin:18px 0 6px;flex-wrap:wrap;">
  <div style="background:#eef4fb;border-radius:10px;padding:14px 22px;text-align:center;">
    <div style="font-size:26px;font-weight:700;color:#2f6db5;">{summary['overall_otif_rate_pct']}%</div>
    <div style="font-size:12px;color:#555;">Overall OTIF rate</div>
  </div>
  <div style="background:#f5f0fb;border-radius:10px;padding:14px 22px;text-align:center;">
    <div style="font-size:26px;font-weight:700;color:#7a52a3;">{summary['bottleneck_route_carrier_combos_flagged']}</div>
    <div style="font-size:12px;color:#555;">Bottleneck route x carrier combos</div>
  </div>
  <div style="background:#fbeeee;border-radius:10px;padding:14px 22px;text-align:center;">
    <div style="font-size:26px;font-weight:700;color:#c96a6a;">{summary['bottleneck_share_of_shipments_pct']}%</div>
    <div style="font-size:12px;color:#555;">Shipments via flagged bottlenecks</div>
  </div>
  <div style="background:#eef8f0;border-radius:10px;padding:14px 22px;text-align:center;">
    <div style="font-size:26px;font-weight:700;color:#4caf7d;">{summary['best_carrier_by_otif']}</div>
    <div style="font-size:12px;color:#555;">Top-performing carrier</div>
  </div>
</div>
"""

fig_html = fig.to_html(include_plotlyjs="cdn", full_html=False)
html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Retail Supply Chain Route Efficiency & Lead-Time Analytics</title></head>
<body style="margin:0;background:#fafafa;">
{kpi_html}
{fig_html}
</body></html>"""

with open("dashboard/dashboard.html", "w") as f:
    f.write(html)
print("Dashboard written to dashboard/dashboard.html")
