# Annapurna Stores — Part F: Monthly Revenue Reconciliation

## Objective

Reconcile the monthly revenue calculated from the sales pipeline against the Finance monthly figures in `finance_monthly.csv`.

The comparison was performed in DuckDB by loading the Finance CSV and joining it to the monthly revenue calculated from `fact_sales`.

---

## Reconciliation Query

### Load Finance data

```sql
CREATE OR REPLACE TABLE finance_monthly AS
SELECT *
FROM read_csv_auto('data/finance_monthly.csv');
```

### Calculate monthly revenue

```sql
CREATE OR REPLACE TABLE calculated_monthly AS
SELECT
    STRFTIME(business_date,'%Y-%m') AS month,
    ROUND(SUM(revenue_inr),2) AS calculated_revenue
FROM fact_sales
GROUP BY 1
ORDER BY 1;
```

### Compare Finance and calculated revenue

```sql
SELECT
    f.month,
    f.revenue_inr AS finance_revenue,
    c.calculated_revenue,
    ROUND(c.calculated_revenue - f.revenue_inr,2) AS difference
FROM finance_monthly f
LEFT JOIN calculated_monthly c
    ON f.month = c.month
ORDER BY f.month;
```

---

## Reconciliation Results

| Month | Finance Revenue | Calculated Revenue | Difference |
|---|---:|---:|---:|
| 2024-01 | 38,446,071.33 | 38,446,071.33 | 0.00 |
| 2024-02 | 34,887,085.55 | 34,887,085.55 | 0.00 |
| 2024-03 | 42,457,899.09 | 41,971,649.09 | -486,250.00 |
| 2024-04 | 37,958,457.37 | 37,958,457.37 | 0.00 |
| 2024-05 | 41,764,716.40 | 41,764,716.40 | 0.00 |
| 2024-06 | 38,987,082.82 | 38,987,082.82 | 0.00 |
| 2024-07 | 40,527,291.81 | 40,304,160.11 | -223,131.70 |
| 2024-08 | 45,252,181.75 | 45,252,181.75 | 0.00 |
| 2024-09 | 44,615,037.46 | 44,615,037.46 | 0.00 |
| 2024-10 | 56,359,195.92 | 56,359,195.92 | 0.00 |
| 2024-11 | 51,583,838.47 | 51,583,838.47 | 0.00 |
| 2024-12 | 50,745,209.00 | 50,745,259.48 | +50.48 |

**9 months match exactly. 3 months have differences.**

---

## Investigation of Mismatched Months

### March 2024

Finance revenue:

`₹42,457,899.09`

Calculated revenue:

`₹41,971,649.09`

Difference:

`-₹486,250.00`

The line-type breakdown was checked:

- DISCOUNT: `-₹422,529.83`
- RETURN: `-₹872,421.34`
- SALE: `₹43,570,195.04`
- TAX: `₹0.00`
- TENDER: `₹0.00`
- VOID: `-₹303,594.78`

A duplicate-line check was also performed:

- Rows: `91,711`
- Unique lines: `91,711`

Therefore, duplicate/resend lines were **not** found in March.

The available evidence does not establish a definitive root cause for the March difference. It should be taken back for investigation rather than assigning an unsupported cause.

---

### July 2024

Finance revenue:

`₹40,527,291.81`

Calculated revenue:

`₹40,304,160.11`

Difference:

`-₹223,131.70`

The vendor notes document a known source-data issue: **S07 Pune lost its till server for three days in July 2024 and therefore has no exports for those days. Finance received numbers because the store phoned them in.**

Therefore this mismatch is classified as:

**Classification: Source-data problem**

This should be taken back to Finance/source-data reconciliation to account for the missing S07 export period.

---

### December 2024

Finance revenue:

`₹50,745,209.00`

Calculated revenue:

`₹50,745,259.48`

Difference:

`+₹50.48`

The line-type breakdown was checked:

- DISCOUNT: `-₹512,901.24`
- RETURN: `-₹1,144,992.16`
- SALE: `₹52,692,638.60`
- TAX: `₹0.00`
- TENDER: `₹0.00`
- VOID: `-₹289,485.72`

A duplicate-line check was also performed:

- Rows: `105,721`
- Unique lines: `105,721`

Therefore, duplicate/resend lines were **not** found in December.

The available evidence does not establish a definitive root cause for the ₹50.48 difference. It should be investigated with Finance/source records rather than assigning an unsupported cause.

---

## Important October Check

October 2024 was specifically checked because the vendor notes warn that including all line types can roughly double revenue due to `TENDER` rows and can also include GST through `TAX` rows.

October reconciliation:

- Finance: `₹56,359,195.92`
- Calculated: `₹56,359,195.92`
- Difference: `₹0.00`

The calculated revenue therefore matches Finance for October, and the current revenue definition does not show the warned TENDER double-counting problem.

---

## Revenue Definition Used

The `fact_sales` pipeline calculates revenue only for:

- `SALE`
- `RETURN`
- `DISCOUNT`
- `VOID`

`TAX` and `TENDER` contribute `0` to `revenue_inr`.

This preserves the cancellation behavior because SALE and VOID lines are retained together, causing a cancelled bill to net to zero.

---

## Final Classification

| Month | Difference | Classification | Action |
|---|---:|---|---|
| March 2024 | -₹486,250.00 | Cause not established from available evidence | Investigate with Finance/source records |
| July 2024 | -₹223,131.70 | **Source-data problem** | Reconcile missing S07 export period |
| December 2024 | +₹50.48 | Cause not established from available evidence | Investigate with Finance/source records |

### Issues to Take Back to Finance

1. **July:** Confirm and reconcile the three missing S07 export days against the figures supplied directly to Finance.
2. **March:** Investigate the ₹486,250 difference using Finance/source records; duplicate lines have already been ruled out.
3. **December:** Investigate the small ₹50.48 difference; duplicate lines and TAX/TENDER revenue contribution have been ruled out by the checks performed.

---

## Evidence Included

The package contains screenshots showing:

1. Full monthly Finance vs calculated reconciliation.
2. March and December line-type revenue breakdown.
3. March and December store-level revenue breakdown.
4. March and December duplicate/unique-line check.

---

## Conclusion

The monthly reconciliation identified three mismatches:

- March: `-₹486,250.00`
- July: `-₹223,131.70`
- December: `+₹50.48`

The July mismatch has a documented source-data explanation involving the S07 till-server outage. March and December require further investigation because the available execution evidence does not prove a specific root cause.

**Part F: COMPLETE**
