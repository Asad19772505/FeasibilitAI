import streamlit as st
import numpy as np
import pandas as pd
import numpy_financial as npf
import altair as alt
from io import BytesIO

st.set_page_config(page_title="Feasibility What-If Simulator", layout="centered")
st.title("📊 Feasibility What-If Simulator")
st.write("Adjust the assumptions below to simulate IRR, NPV, and ROIC for your project.")

# --- INPUTS ---
st.sidebar.header("Project Assumptions")
selling_price = st.sidebar.slider("Selling Price (SAR/sqm)", 1000, 5000, 3500, step=100)
land_price = st.sidebar.slider("Land Price (SAR/sqm)", 2000, 3500, 3000, step=100)
wacc = st.sidebar.slider("WACC (%)", 8, 15, 11, step=1) / 100
project_years = st.sidebar.slider("Project Duration (Years)", 1, 20, 5)

# --- FIXED PARAMETERS ---
area = 1000  # sqm
sellable_pct = 0.6
dev_cost_per_sqm = 500  # Infrastructure + Dev Fee
total_sellable_area = area * sellable_pct

# --- CALCULATIONS ---
def simulate_financials_monthly(selling_price, land_price, wacc, project_years):
    revenue = selling_price * total_sellable_area
    land_cost = land_price * area
    development_cost = dev_cost_per_sqm * area
    total_cost = land_cost + development_cost

    months = project_years * 12
    monthly_revenue = revenue / months
    monthly_cost = total_cost / months

    net_cash_flows = [-total_cost] + [monthly_revenue - monthly_cost] * months

    irr = npf.irr(net_cash_flows) * 12  # annualized
    discounted_cf = [cf / (1 + wacc/12) ** i for i, cf in enumerate(net_cash_flows)]
    npv = sum(discounted_cf)
    roic = revenue / total_cost if total_cost else 0

    return irr, npv, roic, net_cash_flows, monthly_revenue, monthly_cost

irr, npv, roic, net_cash_flows, monthly_revenue, monthly_cost = simulate_financials_monthly(selling_price, land_price, wacc, project_years)

# --- OUTPUTS ---
st.subheader("📈 Results (Monthly Model)")
st.metric("IRR (Annualized)", f"{irr*100:.2f}%" if irr else "N/A")
st.metric("NPV", f"SAR {npv:,.0f}")
st.metric("ROIC", f"{roic:.2f}x")

# --- Arabic Summary ---
st.subheader("ملخص باللغة العربية")
arabic_summary = (
    f"استنادًا إلى هذه الفرضيات، يحقق المشروع معدل عائد داخلي (IRR) سنوي قدره {irr*100:.2f}٪، وصافي القيمة الحالية (NPV) بمقدار {npv:,.0f} ريال سعودي، "
    f"وعائد على رأس المال المستثمر (ROIC) بمقدار {roic:.2f} مرة."
)
st.write(arabic_summary)

# --- CHART ---
cf_df = pd.DataFrame({
    "Month": list(range(len(net_cash_flows))),
    "Revenue": [0] + [monthly_revenue] * (project_years * 12),
    "Cost": [total_cost] + [monthly_cost] * (project_years * 12),
    "Net Cash Flow": net_cash_flows
})

chart = alt.Chart(cf_df).transform_fold(
    ["Revenue", "Cost", "Net Cash Flow"], as_=["Type", "Value"]
).mark_line(point=True).encode(
    x="Month:O",
    y="Value:Q",
    color="Type:N",
    tooltip=["Month", "Type", "Value"]
).properties(title="Monthly Revenue, Cost, and Net Cash Flow")

st.altair_chart(chart, use_container_width=True)

# --- FOOTER ---
st.caption("Built for feasibility study simulation by a Finance Professional (monthly cash flow model).")
