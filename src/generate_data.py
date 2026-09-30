"""Generate synthetic supplier-to-warehouse shipment data across multiple routes/carriers."""
import numpy as np
import pandas as pd

np.random.seed(11)

warehouses = ["North DC", "South DC", "East DC", "West DC"]
suppliers = [f"Supplier-{i:02d}" for i in range(1, 13)]
carriers = ["Carrier A", "Carrier B", "Carrier C", "Carrier D"]

# Each supplier has a home region -> biases which warehouse & base transit time
supplier_profile = {}
for i, s in enumerate(suppliers):
    supplier_profile[s] = {
        "base_transit_days": np.random.uniform(2, 9),
        "variability": np.random.uniform(0.5, 2.5),
        "region": warehouses[i % 4],
    }

carrier_profile = {
    "Carrier A": {"speed_factor": 0.92, "otif_rate": 0.94, "cost_per_shipment": 480, "reliability": 0.6},
    "Carrier B": {"speed_factor": 1.00, "otif_rate": 0.89, "cost_per_shipment": 410, "reliability": 1.0},
    "Carrier C": {"speed_factor": 1.15, "otif_rate": 0.80, "cost_per_shipment": 350, "reliability": 1.8},
    "Carrier D": {"speed_factor": 1.05, "otif_rate": 0.86, "cost_per_shipment": 390, "reliability": 1.3},
}

n_shipments = 6000
dates = pd.date_range("2024-01-01", "2025-12-31", freq="D")

rows = []
for i in range(n_shipments):
    supplier = np.random.choice(suppliers)
    prof = supplier_profile[supplier]
    warehouse = prof["region"] if np.random.rand() < 0.75 else np.random.choice(warehouses)
    carrier = np.random.choice(carriers, p=[0.30, 0.30, 0.22, 0.18])
    cprof = carrier_profile[carrier]

    planned_transit = prof["base_transit_days"] * cprof["speed_factor"]
    combined_variability = prof["variability"] * cprof["reliability"]
    actual_transit = max(0.5, np.random.normal(planned_transit, combined_variability))
    ship_date = np.random.choice(dates)
    delivery_date = pd.Timestamp(ship_date) + pd.Timedelta(days=actual_transit)

    # On-time is driven by whether the (noisy) actual transit blew past the planned window
    on_time = actual_transit <= planned_transit * 1.10
    # In-full fill rate is a carrier-specific probability (pick/pack/inventory accuracy)
    in_full = np.random.rand() < cprof["otif_rate"]
    otif = on_time and in_full

    rows.append({
        "shipment_id": f"SHP-{100000+i}",
        "supplier": supplier,
        "warehouse": warehouse,
        "carrier": carrier,
        "ship_date": pd.Timestamp(ship_date).date(),
        "planned_transit_days": round(planned_transit, 1),
        "actual_transit_days": round(actual_transit, 1),
        "delivery_date": delivery_date.date(),
        "on_time": bool(on_time),
        "in_full": bool(in_full),
        "otif": bool(otif),
        "cost_usd": round(cprof["cost_per_shipment"] * np.random.uniform(0.9, 1.1), 2),
    })

df = pd.DataFrame(rows)
df.to_csv("data/shipments.csv", index=False)
print(df.shape)
print(df.groupby("carrier")[["on_time", "in_full", "otif"]].mean().round(3))
