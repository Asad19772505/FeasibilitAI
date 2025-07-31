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
loan_pct = st.sidebar.slider("Loan Percentage (%)", 50, 90, 70, step=5) / 100
wacc = st.sidebar.slider("WACC (%)", 8, 15, 11, step=1) / 100
project_years = st.sidebar.slider("Project Duration (Years)", 1, 20, 5)

# --- FIXED PARAMETERS ---
area = 1000  # sqm
sellable_pct = 0.6
dev_cost_per_sqm = 500  # Infrastructure + Dev Fee
total_sellable_area = area * sellable_pct

# --- CALCULATIONS ---
def simulate_financials(selling_price, land_price, loan_pct, wacc, project_years):
    revenue = selling_price * total_sellable_area
    land_cost = land_price * area
    development_cost = dev_cost_per_sqm * area
    total_cost = land_cost + development_cost

    equity = total_cost * (1 - loan_pct)
    annual_cash_inflow = revenue / project_years
    annual_cash_outflow = total_cost / project_years
    net_cash_flows = [-equity] + [annual_cash_inflow - annual_cash_outflow] * project_years

    irr = npf.irr(net_cash_flows)
    discounted_cf = [cf / (1 + wacc) ** i for i, cf in enumerate(net_cash_flows)]
    npv = sum(discounted_cf)
    roic = revenue / total_cost if total_cost else 0
    return irr, npv, roic, net_cash_flows

irr, npv, roic, net_cash_flows = simulate_financials(selling_price, land_price, loan_pct, wacc, project_years)

# --- OUTPUTS ---
st.subheader("📈 Results")
st.metric("IRR", f"{irr*100:.2f}%" if irr else "N/A")
st.metric("NPV", f"SAR {npv:,.0f}")
st.metric("ROIC", f"{roic:.2f}x")

# --- Arabic Summary ---
st.subheader("ملخص باللغة العربية")
arabic_summary = (
    f"استنادًا إلى هذه الفرضيات، يحقق المشروع معدل عائد داخلي (IRR) قدره {irr*100:.2f}٪، وصافي القيمة الحالية (NPV) بمقدار {npv:,.0f} ريال سعودي، "
    f"وعائد على رأس المال المستثمر (ROIC) بمقدار {roic:.2f} مرة."
)
st.write(arabic_summary)

# --- CHART ---
cf_df = pd.DataFrame({"Year": list(range(len(net_cash_flows))), "Net Cash Flow": net_cash_flows})
chart = alt.Chart(cf_df).mark_bar().encode(
    x="Year:O",
    y="Net Cash Flow:Q",
    tooltip=["Year", "Net Cash Flow"]
).properties(title="Projected Net Cash Flows")
st.altair_chart(chart, use_container_width=True)

# --- MULTI-SCENARIO COMPARISON ---
st.subheader("📊 Multi-Scenario Comparison")
comparison_prices = [1000, 2000, 3000, 4000, 5000]
comparison_results = []

for price in comparison_prices:
    comp_irr, comp_npv, comp_roic, _ = simulate_financials(price, land_price, loan_pct, wacc, project_years)
    comparison_results.append({
        "Selling Price": price,
        "IRR %": round(comp_irr*100, 2) if comp_irr else None,
        "NPV": round(comp_npv, 0) if comp_npv else None,
        "ROIC": round(comp_roic, 2) if comp_roic else None
    })

comparison_df = pd.DataFrame(comparison_results)
st.dataframe(comparison_df)

comparison_chart = alt.Chart(comparison_df).transform_fold(
    ["IRR %", "NPV", "ROIC"], as_=["Metric", "Value"]
).mark_line(point=True).encode(
    x="Selling Price:O",
    y="Value:Q",
    color="Metric:N",
    tooltip=["Selling Price", "Metric", "Value"]
).properties(title="Scenario Comparison by Selling Price")

st.altair_chart(comparison_chart, use_container_width=True)

# --- WACC SENSITIVITY ---
st.subheader("📈 IRR Sensitivity to WACC")
wacc_values = [0.08, 0.1, 0.12, 0.14, 0.15]
sensitivity_results = []

for wacc_val in wacc_values:
    irr_val, npv_val, roic_val, _ = simulate_financials(selling_price, land_price, loan_pct, wacc_val, project_years)
    sensitivity_results.append({
        "WACC %": round(wacc_val*100, 1),
        "IRR %": round(irr_val*100, 2) if irr_val else None,
        "NPV": round(npv_val, 0) if npv_val else None
    })

sensitivity_df = pd.DataFrame(sensitivity_results)
st.dataframe(sensitivity_df)

sensitivity_chart = alt.Chart(sensitivity_df).transform_fold(
    ["IRR %", "NPV"], as_=["Metric", "Value"]
).mark_line(point=True).encode(
    x="WACC %:O",
    y="Value:Q",
    color="Metric:N",
    tooltip=["WACC %", "Metric", "Value"]
).properties(title="IRR & NPV vs WACC")

st.altair_chart(sensitivity_chart, use_container_width=True)

# --- BREAKEVEN FINDER ---
st.subheader("🔍 Breakeven Selling Price Finder")
def find_breakeven_price(start=1000, end=5000, step=50):
    for price in range(start, end + 1, step):
        irr, npv, _, _ = simulate_financials(price, land_price, loan_pct, wacc, project_years)
        if npv >= 0:
            return price, irr, npv
    return None, None, None

breakeven_price, breakeven_irr, breakeven_npv = find_breakeven_price()

if breakeven_price:
    st.success(f"Breakeven Selling Price ≈ SAR {breakeven_price}/sqm with IRR {breakeven_irr*100:.2f}% and NPV SAR {breakeven_npv:,.0f}")
else:
    st.error("No breakeven price found in the range 1000–5000 SAR/sqm")

# --- EXPORT TO EXCEL ---
def to_excel():
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    # Write assumptions
    inputs_df = pd.DataFrame({
        "Parameter": ["Selling Price/sqm", "Land Price/sqm", "Loan %", "WACC %", "Project Duration (Years)", "Area (sqm)", "Sellable %"],
        "Value": [selling_price, land_price, loan_pct, wacc, project_years, area, sellable_pct]
    })
    inputs_df.to_excel(writer, sheet_name='Inputs', index=False)

    # Write outputs
    results_df = pd.DataFrame({
        "Metric": ["IRR", "NPV", "ROIC"],
        "Value": [irr, npv, roic]
    })
    results_df.to_excel(writer, sheet_name='Results', index=False)

    # Write breakeven
    breakeven_df = pd.DataFrame({
        "Metric": ["Breakeven Selling Price", "IRR at Breakeven", "NPV at Breakeven"],
        "Value": [breakeven_price, breakeven_irr, breakeven_npv]
    })
    breakeven_df.to_excel(writer, sheet_name='Breakeven', index=False)

    # Write cash flows
    cf_df.to_excel(writer, sheet_name='Cash Flows', index=False)

    # Write scenario comparison
    comparison_df.to_excel(writer, sheet_name='Scenarios', index=False)

    # Write WACC sensitivity
    sensitivity_df.to_excel(writer, sheet_name='WACC Sensitivity', index=False)

    writer.save()
    processed_data = output.getvalue()
    return processed_data

st.download_button(
    label="📥 Download Summary as Excel",
    data=to_excel(),
    file_name="Feasibility_Summary.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# --- FOOTER ---
st.caption("Built for feasibility study simulation by a Finance Professional.")
