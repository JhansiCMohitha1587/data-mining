# Annapurna Stores – Part C: Dashboard Tables

## Objective

Create dashboard-ready tables that allow revenue to be sliced quickly by store,
product category, day of week and month, without repeating descriptive store
information on every sales line.

## Fact table

A `fact_sales` table was created with **1,120,924 rows**.

The fact table contains the sales-line grain and measures, including:

- `store_id`
- `business_date`
- `bill_no`
- `line_no`
- `product_sk`
- `category_id`
- `product_code`
- `qty`
- `unit_price`
- `line_type`
- `revenue_inr`

Store and category descriptions remain in PostgreSQL master/dimension tables
instead of being repeated on every fact row.

## Revenue definition

Revenue is calculated only for the revenue-affecting line types:

- `SALE`
- `RETURN`
- `DISCOUNT`
- `VOID`

`TAX` and `TENDER` are excluded from revenue.

The calculation used is:

`qty * unit_price`

for the revenue-affecting line types.

## Product history handling

The product join uses:

`product_code + business_date`

against the product validity period (`valid_from` / `valid_to`) and returns
the corresponding `product_sk`.

This avoids incorrectly joining a retired product code to a later product after
the code was reissued.

## Dashboard query

Revenue can be grouped by:

- Store
- Product category
- Day of week
- Month

The query used was:

```sql
SELECT
    st.store_name,
    pc.category_name,
    DAYNAME(f.business_date) AS day_of_week,
    STRFTIME(f.business_date, '%Y-%m') AS month,
    ROUND(SUM(f.revenue_inr), 2) AS revenue_inr
FROM fact_sales f
JOIN pg.public.stores st
    ON f.store_id = st.store_id
JOIN pg.public.product_categories pc
    ON f.category_id = pc.category_id
GROUP BY 1,2,3,4
ORDER BY 4,1,2
LIMIT 30;
```

The query successfully returned revenue grouped by store, category, day of
week and month.

## Evidence

### Fact table row count

![Fact table row count](screenshots/C_fact_rows.png)

### Dashboard aggregation

![Dashboard aggregation](screenshots/C_dashboard_query.png)

## Conclusion

Part C is complete. The dashboard model separates sales-line facts from
descriptive master data and supports slicing revenue by store, category,
day of week and month.
