# Warehouse Inventory Analytics — Take-Home Assignment

## Context

You've been given a warehouse movement-level dataset (`inventory_movements.csv`,
~5,000 rows) covering inbound, outbound, transfer, return, and adjustment
movements across 6 warehouses. Ops wants to understand where inventory
accuracy is breaking down and what's driving cost anomalies.

## Task

1. Explore `inventory_movements.csv` and answer the 5 business questions
   below in `BUSINESS_ANSWERS.md`. Back up every answer with a
   query/calculation — don't eyeball it.
2. Build a simple dashboard (any stack — Streamlit, a notebook, a small
   React/Next app, Retool, whatever you're fastest in) showing the key
   metrics behind your answers.
3. Deploy it somewhere reachable by a URL (Vercel, Streamlit Cloud, Render,
   Replit — your choice).

## You may use any AI tool

Use whatever you're fastest and most comfortable with, including (not
limited to):

- Streamlit
- Vercel
- ChatGPT
- Claude
- Emergent
- Base44
- Bolt.new
- Lovable
- Softgen
- Glide
- Rocket.new
- Bubble

We expect you to use AI tools — that's how the job works too. What we're
evaluating is your judgment in using them, not whether you typed every line
yourself.

## Business Questions

1. Which warehouse has the highest stock discrepancy rate, and what's
   actually driving it?
2. Is there a relationship between unit cost and quantity across suppliers?
   Which supplier(s), if any, deviate from that pattern — and by how much?
3. Which SKU(s) show signs of frequent stockouts or inventory imbalance
   (e.g. negative or implausible stock levels)? What would you recommend
   doing about it?
4. Before trusting any of the above — what data quality issues did you find
   in this dataset, and how did you handle them?
5. If you could track exactly one metric weekly to catch inventory problems
   early, what would it be and why?

## Deliverables

Submit all of the following:

1. **Public GitHub repo** with your code — mandatory, regardless of which
   tool/platform you build with. If your platform doesn't natively export
   clean source (e.g. no-code builders), export/download the project and
   push it to GitHub anyway.
2. **Live URL** to your deployed dashboard
3. **README.md** in your repo — your setup steps and a short note on your
   approach
4. **BUSINESS_ANSWERS.md** — written answers to all 5 questions. Charts alone
   are not an answer; explain your reasoning and any caveats.
5. **A 5-minute screen recording** (Loom or similar) walking through your
   dashboard and your answers. We want to hear you reason out loud, not just
   see the finished tool.

## One more thing

We may follow up with a short live conversation about your submission —
come ready to explain and defend any specific choice you made, and to make a
small change to your own analysis live if asked. This isn't a gotcha; it's how
we make sure the thinking is yours.

Good luck — we're looking for how you think, not how polished the dashboard is.
