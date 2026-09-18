# Annapurna Stores – Part D: Historical Prices

## Objective

Return the price that was applicable during a historical reporting period,
rather than using the current product price.

## Method

Historical prices are obtained from the PostgreSQL `price_revisions` table.

The join uses:

- `product_sk` to identify the exact product version
- `effective_from`
- `effective_to`

The reporting date is checked using:

```sql
reporting_date BETWEEN effective_from AND effective_to
```

The same query structure is used for different reporting periods; only the
reporting date changes.

## March 2024 result

The query was executed for:

```text
DATE '2024-03-15'
```

Examples from the result:

| Product code | Product | March selling price |
|---|---|---:|
| P100005 | Thums Up Mango Juice 250g | ₹103.45 |
| P100007 | Vim Dishwash Bar 1kg | ₹129.42 |
| P100019 | Sunfeast Cookies 150g | ₹62.95 |
| P100033 | Gold Winner Mustard Oil 1L | ₹763.12 |
| P100035 | Huggies Diapers Small | ₹1,456.57 |

## October 2024 result

The same query was executed for:

```text
DATE '2024-10-15'
```

Examples from the result:

| Product code | Product | October selling price |
|---|---|---:|
| P100005 | Thums Up Mango Juice 250g | ₹114.37 |
| P100007 | Vim Dishwash Bar 1kg | ₹155.06 |
| P100019 | Sunfeast Cookies 150g | ₹74.65 |
| P100033 | Gold Winner Mustard Oil 1L | ₹828.62 |
| P100035 | Huggies Diapers Small | ₹1,810.38 |

These results demonstrate that historical prices can differ between reporting
periods because the applicable price revision changes over time.

## SQL used

```sql
SELECT
    p.product_code,
    p.product_name,
    pr.selling_price,
    pr.effective_from,
    pr.effective_to
FROM pg.public.products p
JOIN pg.public.price_revisions pr
    ON p.product_sk = pr.product_sk
WHERE DATE '2024-03-15'
      BETWEEN pr.effective_from AND pr.effective_to
ORDER BY p.product_code
LIMIT 20;
```

For the second demonstration, only the reporting date was changed to:

```sql
DATE '2024-10-15'
```

## Evidence

The two terminal outputs showing the March and October historical prices
were captured during the practical.

## Conclusion

Part D is complete. The solution retrieves the historical price applicable to
the requested reporting date from `price_revisions`, using `product_sk` and
the effective date range rather than relying on a current price.
