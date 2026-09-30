-- Retail Supply Chain Route Efficiency & Lead-Time Analytics
-- Run against data/shipments.csv loaded into a `shipments` table (see src/load_to_sqlite.py)

-- 1. Cycle-time & delay pattern per route (supplier -> warehouse)
SELECT
    supplier || ' -> ' || warehouse AS route,
    COUNT(*) AS shipments,
    ROUND(AVG(planned_transit_days), 2) AS avg_planned_days,
    ROUND(AVG(actual_transit_days), 2) AS avg_actual_days,
    ROUND(AVG(actual_transit_days - planned_transit_days), 2) AS avg_delay_days,
    ROUND(100.0 * AVG(otif), 1) AS otif_rate_pct
FROM shipments
GROUP BY route
HAVING shipments >= 5
ORDER BY avg_delay_days DESC;

-- 2. Vendor (supplier) lead-time variance -- coefficient of variation
SELECT
    supplier,
    COUNT(*) AS shipments,
    ROUND(AVG(actual_transit_days), 2) AS mean_transit_days,
    ROUND(
        SQRT(AVG(actual_transit_days * actual_transit_days) - AVG(actual_transit_days) * AVG(actual_transit_days)), 2
    ) AS stddev_transit_days,
    ROUND(
        100.0 * SQRT(AVG(actual_transit_days * actual_transit_days) - AVG(actual_transit_days) * AVG(actual_transit_days))
        / AVG(actual_transit_days), 1
    ) AS cv_pct
FROM shipments
GROUP BY supplier
ORDER BY cv_pct DESC;

-- 3. Carrier performance & OTIF comparison
SELECT
    carrier,
    COUNT(*) AS shipments,
    ROUND(100.0 * AVG(on_time), 1) AS on_time_rate_pct,
    ROUND(100.0 * AVG(in_full), 1) AS in_full_rate_pct,
    ROUND(100.0 * AVG(otif), 1) AS otif_rate_pct,
    ROUND(AVG(cost_usd), 2) AS avg_cost_usd
FROM shipments
GROUP BY carrier
ORDER BY otif_rate_pct DESC;

-- 4. Operational bottlenecks: route x carrier combos with below-average OTIF
-- and above-average delay (candidates for carrier reassignment / process review)
WITH combo AS (
    SELECT
        supplier || ' -> ' || warehouse AS route,
        carrier,
        COUNT(*) AS shipments,
        AVG(otif) AS otif_rate,
        AVG(actual_transit_days - planned_transit_days) AS avg_delay_days
    FROM shipments
    GROUP BY route, carrier
    HAVING shipments >= 5
),
medians AS (
    SELECT AVG(otif_rate) AS median_otif, AVG(avg_delay_days) AS median_delay FROM combo
)
SELECT c.route, c.carrier, c.shipments,
       ROUND(c.otif_rate, 2) AS otif_rate,
       ROUND(c.avg_delay_days, 2) AS avg_delay_days
FROM combo c, medians m
WHERE c.otif_rate < m.median_otif AND c.avg_delay_days > m.median_delay
ORDER BY c.avg_delay_days DESC;

-- 5. Monthly OTIF trend (for tracking process-improvement impact over time)
SELECT
    strftime('%Y-%m', ship_date) AS ship_month,
    COUNT(*) AS shipments,
    ROUND(100.0 * AVG(otif), 1) AS otif_rate_pct
FROM shipments
GROUP BY ship_month
ORDER BY ship_month;
