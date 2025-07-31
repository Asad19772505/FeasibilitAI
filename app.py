import streamlit as st
import numpy as np
import pandas as pd

st.set_page_config(page_title="Feasibility What-If Simulator", layout="centered")
st.title("📊 Feasibility What-If Simulator")
st.write("Adjust the assumptions below to simulate IRR, NPV, and ROIC for your project.")

# --- INPUTS ---
st.sidebar.header("Project Assumptions")
selling_price = st.sidebar.slider("Selling Price (SAR/sqm)", 3000, 5000, 3500, step=100)
land_price = st.sidebar.slider("Land Price (SAR/sqm)", 2000, 3500, 3000, step=100)
loan_pct = st.sidebar.slider("Loan Percentage (%)", 50, 90, 70, step=5) / 100
wacc = st.sidebar.slider("WACC (%)", 8, 15, 11, step=1) / 100
project_years = st.sidebar.slider("Project Duration (Years)", 1, 20, 5)

# --- FIXED PARAMETERS ---
area = 1000  # sqm
sellable_pct = 0.6
dev_cost_per_sqm = 500  # Infrastructure + Dev Fee
total_sellable_area = area * sellable_pct

# --- CALCULATIONS ---
revenue = selling_price * total_sellable_area
land_cost = land_price * area
development_cost = dev_cost_per_sqm * area
total_cost = land_cost + development_cost

equity = total_cost * (1 - loan_pct)
loan_amount = total_cost * loan_pct

# Assume linear cash flow distribution over project years
annual_cash_inflow = revenue / project_years
annual_cash_outflow = total_cost / project_years
net_cash_flows = [-equity] + [annual_cash_inflow - annual_cash_outflow] * project_years

# IRR & NPV
irr = np.irr(net_cash_flows)
discounted_cf = [cf / (1 + wacc) ** i for i, cf in enumerate(net_cash_flows)]
npv = sum(discounted_cf)
roic = revenue / total_cost if total_cost else 0

# --- OUTPUTS ---
st.subheader("📈 Results")
st.metric("IRR", f"{irr*100:.2f}%" if irr else "N/A")
st.metric("NPV", f"SAR {npv:,.0f}")
st.metric("ROIC", f"{roic:.2f}x")

# --- CHART ---
cf_df = pd.DataFrame({"Year": list(range(len(net_cash_flows))), "Net Cash Flow": net_cash_flows})
st.bar_chart(cf_df.set_index("Year"))

# --- FOOTER ---
st.caption("Built for feasibility study simulation by a Finance Professional.")
