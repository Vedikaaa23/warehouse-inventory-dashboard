# Business Answers

Candidate name: [Vedika Singh]
Date: [29th July 2026]

---

## Q1. Which warehouse has the highest stock discrepancy rate, and what's actually driving it?

**Answer:**

By raw numbers, **WH_06 (Pune)** has the highest share of movements flagged
`status = Discrepancy`, at 11.3%, versus a low of 8.1% at WH_03 (Delhi). But
that 3-point spread is not statistically significant: a chi-square test of
warehouse vs. discrepancy status gives χ² ≈ 6.2, p ≈ 0.29. With ~800-880
movements per warehouse, this spread is consistent with noise, not a
warehouse-specific operational problem.

The actual driver is **movement type, not location**. Discrepancy rate by
movement type, pooled across all warehouses:

| Movement type | Discrepancy rate |
|---|---|
| Adjustment | 11.0% |
| Return | 10.0% |
| Transfer | 9.7% |
| Inbound | 9.2% |
| Outbound | 8.9% |

Adjustments and Returns run noticeably hotter than Inbound/Outbound, and this
pattern holds inside every individual warehouse (e.g. in WH_06, Transfer and
Adjustment are the highest-rate types locally too). I also checked whether
late/early deliveries (`movement_date` vs. `expected_date`) predict
discrepancies — they don't (correlation ≈ 0.006). So the discrepancy problem
looks like a **process issue tied to how Adjustments and Returns get recorded**
(likely manual entry with less validation), rather than a specific site's
execution.

**Recommendation:** don't single out WH_06 for an ops review based on this
data alone — instead, audit how Adjustment and Return movements are entered
and reconciled across all sites, since that's where the rate is structurally
higher everywhere.

**How you checked it (query/method):**
`groupby('warehouse_id')['is_discrepancy'].mean()`, cross-checked with a
`scipy.stats.chi2_contingency` test on the warehouse × discrepancy contingency
table; then the same rate broken out by `movement_type`; then a correlation
between `(movement_date - expected_date)` and discrepancy flag. See `app.py`,
Q1 section, for the reproducible chart.

---

## Q2. Is there a relationship between unit cost and quantity across suppliers? Which supplier(s) deviate, and by how much?

**Answer:**

Across all Inbound movements, unit cost and quantity are essentially
uncorrelated (Pearson r ≈ -0.02) — bigger orders aren't priced any
differently per unit than small ones, which is what you'd expect if there's
no bulk-discount structure in this data.

**SUP_09 is a clear outlier.** Average unit cost across suppliers:

| Supplier | Avg unit cost |
|---|---|
| SUP_09 | ~₹10,560 |
| All 11 others | ₹960 – ₹1,130 |

That's roughly **9-11x every other supplier**. It isn't just a shift in
SUP_09's product mix either — for the 112 SKUs SUP_09 supplies that are also
sourced from other suppliers, SUP_09's price on the *same SKU* is
consistently 5-20x higher (e.g. SKU_0280: SUP_08 charges ₹100.80,
SUP_09 charges ₹3,056–₹20,897 for it across three separate movements, with no
consistent quantity relationship to explain the spread — even SUP_09's own
price for the same SKU varies 7x movement to movement).

That last point matters: SUP_09's own pricing for a single SKU isn't even
internally consistent, which points toward this being a **data entry or
currency/unit issue** (e.g., values entered in a different currency, or with
an extra digit) rather than a legitimate premium-supplier pricing tier.

**Recommendation:** flag SUP_09 records for a manual data audit before using
unit_cost from this dataset in any cost-based analysis (e.g. COGS, valuation);
don't average it in with the other suppliers until it's confirmed.

**How you checked it (query/method):**
Filtered to `movement_type == 'Inbound'`, computed `corr(unit_cost, quantity)`
overall and per `supplier_id`, then compared `mean(unit_cost)` per supplier.
Then joined on `sku_id` to find SKUs sourced from SUP_09 and at least one
other supplier, and compared unit_cost directly. See `app.py`, Q2 section.

---

## Q3. Which SKU(s) show signs of frequent stockouts or inventory imbalance? What would you recommend?

**Answer:**

I treated any movement where `stock_after < 0` as a physically implausible
event (you cannot have negative units on a shelf) — a proxy for a stockout
that wasn't caught before the movement was recorded. This flags **202
movements across 146 distinct SKUs** (out of 300 total SKUs), the large
majority on Outbound and Transfer movements, i.e. cases where the recorded
quantity shipped/transferred exceeded the recorded quantity on hand.

The worst-affected SKUs each show 3-4 separate negative-stock events over
the ~6-month window (e.g. SKU_0172, SKU_0127, SKU_0056, SKU_0033, several
others) — meaning this isn't a one-off, it's a repeating pattern for a
specific subset of SKUs. Severity also varies wildly: some oversells exceed
stock on hand by 1,000%+ (e.g. SKU_0092 at WH_05: 245 units shipped against
only 3 in stock — an 80x oversell).

This is most consistent with **no hard validation at the point of movement
entry** — the system lets someone log an Outbound/Transfer for more units
than `stock_before` shows, rather than blocking or flagging it in real time.

**Recommendation:**
1. Add a **pre-commit validation rule**: block (or require override +
   reason code for) any Outbound/Transfer where `quantity > stock_before`.
2. Run a **physical stock count** on the ~146 flagged SKUs to reconcile
   system vs. actual, since repeated negative-stock events usually mean the
   system of record has drifted from reality.
3. Investigate the handful of SKUs with 3+ repeat events specifically —
   those look like a systemic issue (e.g., a specific supplier lead time,
   or a fast-moving SKU that isn't being replenished fast enough) rather
   than one-off data entry mistakes.

**How you checked it (query/method):**
Flagged `stock_after < 0`, grouped by `sku_id` to count events per SKU, and
computed `(quantity - stock_before) / stock_before` as an oversell severity
%. See `app.py`, Q3 section.

---

## Q4. What data quality issues did you find, and how did you handle them?

**Answer:**

| Issue | Scope | How I handled it |
|---|---|---|
| **Exact duplicate rows** — 15 `movement_id`s appear twice with identical data | 15 rows | Dropped duplicates (`keep='first'`) before any aggregation, so counts/rates aren't double-counted. |
| **Negative `stock_after`** — physically impossible stock levels | 202 rows / 146 SKUs | Treated as a signal, not an error to discard (this *is* the Q3 answer) — kept in the data but flagged separately from valid stock levels. |
| **Missing `stock_after`** | 916 rows (~18%) | Concentrated in Cancelled (264) and Completed-but-unresolved (545) movements. Left as null rather than imputed — imputing a stock level would fabricate data that could hide real reconciliation problems. Excluded from stock-based calculations, kept in count-based ones (e.g. discrepancy rate). |
| **Missing `movement_date` / `expected_date`** | 74 / 75 rows | Excluded from any date/weekly-trend analysis (can't be assigned to a week); kept for non-date aggregations. |
| **`supplier_id` / `customer_id` structurally missing** | supplier_id null except on Inbound (3,528 rows); customer_id null except on Outbound (3,249 rows) | Confirmed this is by design, not a data quality issue — a Transfer or Adjustment has neither a supplier nor a customer. No action needed. |
| **SUP_09 pricing anomaly** | 147 Inbound rows | See Q2 — flagged rather than corrected, since I can't confirm the "true" price without more context. Excluded from any cross-supplier cost benchmarking I'd normally trust. |
| **`status = 'Discrepancy'` doesn't always mean the stock math is wrong** | checked ~470 rows | I initially assumed `status='Discrepancy'` meant `stock_after ≠ stock_before ± quantity`. Testing this directly showed most flagged rows have perfectly consistent math — `status` looks like an independently-recorded outcome field (e.g. a human/ops flag), not a derived one. I treated it as ground truth for "was this movement flagged" rather than re-deriving my own discrepancy definition, to avoid overriding what's presumably a real operational signal. |

**General approach:** I didn't silently fix or drop anything that looked like
a genuine business signal (negative stock, discrepancy flags, SUP_09
pricing) — those are the actual analysis. I only removed genuine duplication
(the 15 repeated rows) and excluded rows from specific calculations where a
required field was missing, rather than imputing values.

---

## Q5. If you could track exactly one metric weekly to catch inventory problems early, what would it be and why?

**Answer:**

**Negative-stock incident rate**: the % of Outbound/Transfer movements each
week where `stock_after < 0`.

Why this one over `discrepancy_rate` or a cost-based metric:

- It's a **leading indicator of real operational failure**, not just a
  labeling/process metric. A movement that drives stock negative means
  something already went wrong upstream (bad count, late replenishment,
  overselling) — it isn't a subjective flag, it's arithmetic.
- It's **warehouse- and SKU-sliceable** for root-causing without needing a
  second metric — you can immediately see if a spike is one warehouse, one
  SKU, or system-wide.
- It's **actionable at the point of failure**: a rising trend justifies
  tightening the pre-commit validation described in Q3 before it compounds
  into a larger reconciliation problem.
- Compared to `discrepancy_rate`, it doesn't depend on someone remembering to
  flag a movement — it's derived directly from the stock math, so it can't
  silently degrade if flagging discipline slips.

The dashboard includes this as a weekly trend line so a rising rate is
visible early, before it shows up as a larger inventory write-off.

---

## Anything else you'd flag if this were a real dataset at FreightFox?

- I'd want to know whether `stock_before`/`stock_after` are captured **before
  or after** the movement is physically executed — that changes whether
  negative stock reflects a system delay vs. an actual empty-shelf event.
- I'd want a second data source (e.g. a WMS snapshot or cycle-count table) to
  independently verify SUP_09's pricing and the ~146 negative-stock SKUs,
  since everything here is inferred from one movement log with no ground
  truth to check against.
- Given the discrepancy-rate finding in Q1, I'd want the raw definition of
  `status = 'Discrepancy'` from whoever owns that field — right now I'm
  treating it as a trustworthy label, but I haven't been able to verify how
  it's actually assigned.
