-- SQLite. Python loads the validated CSV into rental_monthly first.
-- A calendar-date JOIN avoids treating the 12th preceding row as last year.
DROP VIEW IF EXISTS monthly_yoy;
CREATE VIEW monthly_yoy AS
SELECT c.*, p.median_rent AS prior_year_median,
       p.lodged_bonds AS prior_year_bonds,
       ROUND(100.0 * (c.median_rent - p.median_rent)
             / NULLIF(p.median_rent, 0), 2) AS rent_yoy_pct,
       ROUND(100.0 * (c.lodged_bonds - p.lodged_bonds)
             / NULLIF(p.lodged_bonds, 0), 2) AS bonds_yoy_pct
FROM rental_monthly c
LEFT JOIN rental_monthly p
  ON c.location_id = p.location_id
 AND p.month = date(c.month, '-1 year');

DROP VIEW IF EXISTS annual_activity;
CREATE VIEW annual_activity AS
SELECT location_id, location, substr(month, 1, 4) AS year,
       COUNT(*) AS months_present,
       COUNT(lodged_bonds) AS months_with_bond_counts,
       SUM(lodged_bonds) AS reported_bonds_in_available_months,
       CASE WHEN COUNT(*) = 12 AND COUNT(lodged_bonds) = 12
            THEN SUM(lodged_bonds) END AS full_year_lodged_bonds
FROM rental_monthly
GROUP BY location_id, location, substr(month, 1, 4);

DROP VIEW IF EXISTS latest_snapshot;
CREATE VIEW latest_snapshot AS
SELECT * FROM monthly_yoy
WHERE month = (SELECT MAX(month) FROM rental_monthly);

DROP VIEW IF EXISTS latest_growth_ranking;
CREATE VIEW latest_growth_ranking AS
WITH eligible AS (
    -- Analyst-chosen threshold, not a statistical significance test.
    SELECT * FROM latest_snapshot
    WHERE lodged_bonds >= 30 AND prior_year_bonds >= 30
      AND rent_yoy_pct IS NOT NULL
)
SELECT DENSE_RANK() OVER (ORDER BY rent_yoy_pct DESC) AS growth_rank,
       location, month, median_rent, prior_year_median, rent_yoy_pct,
       lodged_bonds, prior_year_bonds
FROM eligible;
