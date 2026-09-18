# Annapurna Stores — Part E: Query Across Two Systems

## Objective

Query sales data stored in the analytical/query-engine side together with store and product-category master data stored in PostgreSQL, without first copying either side into the other system.

## Systems Used

- **DuckDB** — analytical query engine
- **PostgreSQL** — relational master-data database
- **Sales data** — `fact_sales` in DuckDB
- **Store master** — `pg.public.stores` in PostgreSQL
- **Product categories** — `pg.public.product_categories` in PostgreSQL

The PostgreSQL database was attached to DuckDB using the PostgreSQL extension:

```sql
INSTALL postgres;
LOAD postgres;

ATTACH 'host=host.docker.internal port=5432 dbname=annapurna user=annapurna password=annapurna'
AS pg (TYPE postgres, READ_ONLY);
```

## Federated Query

The following single query joins the DuckDB `fact_sales` table with the PostgreSQL master tables:

```sql
EXPLAIN ANALYZE
SELECT
    f.store_id,
    st.store_name,
    pc.category_name,
    ROUND(SUM(f.revenue_inr),2) AS revenue_inr
FROM fact_sales f
JOIN pg.public.stores st
    ON f.store_id = st.store_id
JOIN pg.public.product_categories pc
    ON f.category_id = pc.category_id
WHERE f.business_date >= DATE '2024-10-01'
  AND f.business_date < DATE '2024-11-01'
GROUP BY 1,2,3
ORDER BY 1,3;
```

## Evidence From EXPLAIN ANALYZE

The captured DuckDB query profile shows:

- **Total query time:** `0.0263s`
- `fact_sales` is scanned with the October 2024 business-date filter.
- PostgreSQL `stores` is scanned with projections `store_id` and `store_name`.
- PostgreSQL `product_categories` is scanned with projections `category_id` and `category_name`.
- DuckDB performs hash joins between the sales data and PostgreSQL tables.
- The plan contains a `HASH_JOIN` on `store_id`.
- The plan contains a `HASH_JOIN` on `category_id`.
- The final aggregation uses `HASH_GROUP_BY` with `sum(#3)`.
- The profile shows `14 rows` for `product_categories` and `12 rows` for `stores`.
- The filtered sales side produced `81,453 rows` for the October query before the final grouping.

## What This Demonstrates

The query successfully performs a **federated join across two systems**:

1. Sales facts are read from DuckDB's `fact_sales`.
2. Store master data is read from PostgreSQL.
3. Product-category master data is read from PostgreSQL.
4. DuckDB joins the datasets and performs the aggregation.
5. No preliminary copy of the PostgreSQL tables into DuckDB was required.
6. The `EXPLAIN ANALYZE` output provides engine-level evidence of the scans, filters, joins, and aggregation.

## Conclusion

Part E is demonstrated using one SQL query across DuckDB and PostgreSQL. The execution profile confirms that DuckDB evaluated the query by scanning `fact_sales` and accessing the PostgreSQL `stores` and `product_categories` tables, followed by hash joins and aggregation.

**Part E: COMPLETE**
