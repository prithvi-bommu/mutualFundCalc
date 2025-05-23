import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go


from calculators.futureValue import calculate_future_value
from calculators.portfolioProjection import calc_portfolio_projection
from utils.sidebar import sidebar_inputs
from utils.currencyFromatter import format_inr

# ----- DEFAULTS -----
DEFAULT_INVESTMENT = 0
DEFAULT_YEARS = 5
DEFAULT_RISK = 'Medium'
categories = ['Large-Cap', 'Mid-Cap', 'Small-Cap', 'Hybrid']
DEFAULT_CAGR = {
    'Large-Cap': {'Best': 25, 'Medium': 23.79, 'Worst': 10},
    'Mid-Cap': {'Best': 35, 'Medium': 33, 'Worst': 15},
    'Small-Cap': {'Best': 50, 'Medium': 35, 'Worst': 20},
    'Hybrid': {'Best': 15, 'Medium': 12, 'Worst': 8},
}
DEFAULT_ALLOC = {
    'Low':    {'Large-Cap': 0.6, 'Mid-Cap': 0.2, 'Small-Cap': 0.0, 'Hybrid': 0.2},
    'Medium': {'Large-Cap': 0.4, 'Mid-Cap': 0.3, 'Small-Cap': 0.2, 'Hybrid': 0.1},
    'High':   {'Large-Cap': 0.2, 'Mid-Cap': 0.4, 'Small-Cap': 0.35, 'Hybrid': 0.05},
}
RECOMMENDED_FUNDS = {
    'Large-Cap': ['Nippon India Large Cap', 'ICICI Pru Bluechip'],
    'Mid-Cap': ['Motilal Oswal Midcap', 'Quant Mid Cap'],
    'Small-Cap': ['Quant Small Cap', 'Nippon India Small Cap'],
    'Hybrid': ['HDFC Balanced Advantage'],
}
LTCG_EXEMPTION = 125000
LTCG_RATE = 0.125
DRIFT_THRESHOLD = 5.0  # percent

# ----- UTILITY FUNCTIONS -----

def calculate_tax(total_gain, years, exemption=LTCG_EXEMPTION, rate=LTCG_RATE):
    total_exemption = exemption * years
    taxable_gain = max(total_gain - total_exemption, 0)
    return taxable_gain, taxable_gain * rate

def allocation_breakdown(investment, allocation):
    return {cat: investment * pct for cat, pct in allocation.items()}

def build_summary_table(results):
    table = {}
    for sc, cats in results.items():
        table[sc] = {**cats, 'Total Corpus': sum(cats.values())}
    return pd.DataFrame(table).T

def get_portfolio_drift(current, target):
    drift = {}
    for cat in target:
        curr = current.get(cat, 0)
        tgt = target[cat]
        drift[cat] = 100 * (curr - tgt)  # % over or under target
    return drift

def build_rebalance_table(current, target):
    drift = get_portfolio_drift(current, target)
    rebalance = []
    for cat, d in drift.items():
        action = ''
        if abs(d) >= DRIFT_THRESHOLD:
            action = 'Increase' if d < 0 else 'Reduce'
        rebalance.append({
            'Category': cat,
            'Target %': f"{target[cat]*100:.1f}%",
            'Current %': f"{current.get(cat,0)*100:.1f}%",
            'Drift': f"{d:+.1f}%",
            'Action': action if action else '—',
        })
    return pd.DataFrame(rebalance)

# ----- STREAMLIT UI -----
st.set_page_config(page_title="Mutual Fund Allocation & Projection", layout="wide")
st.title("Mutual Fund Allocation & Projection Web App")

# --- SIDEBAR: USER INPUT ---
investment, years, risk_profile, allocation, cagr_dict, current_portfolio = sidebar_inputs(
    DEFAULT_INVESTMENT, DEFAULT_YEARS, DEFAULT_ALLOC, DEFAULT_CAGR, categories
)

# --- Suggested Allocation Table with % in Header, No Row Index ---
breakdown = allocation_breakdown(investment, allocation)
header_map = {
    cat: f"{cat} (₹) ({allocation[cat]*100:.1f}%)" for cat in breakdown
}
alloc_df = pd.DataFrame([breakdown])
for col in alloc_df.columns:
    alloc_df[col] = alloc_df[col].apply(format_inr)
alloc_df = alloc_df.rename(columns=header_map)
alloc_df.index = [""]  # Removes the 0 row index
st.header("1. Suggested Allocation")
st.table(alloc_df)

st.subheader("Recommended Funds by Category")
for cat, funds in RECOMMENDED_FUNDS.items():
    st.markdown(f"**{cat}:** {', '.join(funds)}")

st.header("2. Corpus Projection (Best / Medium / Worst Case)")
results = calc_portfolio_projection(breakdown, cagr_dict, years)
proj_table = build_summary_table(results)
for sc in proj_table.index:
    total_corpus = proj_table.loc[sc, 'Total Corpus']
    percent_return = ((float(str(total_corpus).replace('₹','').replace(',','')) - investment) / investment) * 100
    percent_str = f"{percent_return:.1f}%"
    # Add to index name
    proj_table.rename(index={sc: f"{sc} ({percent_str})"}, inplace=True)
for col in proj_table.columns:
    proj_table[col] = proj_table[col].apply(format_inr)
st.dataframe(proj_table)

st.subheader("Growth Over Time (Scenario Comparison)")

# Build line chart for total corpus per scenario
years_list = np.arange(1, years+1)
chart_data = {'Year': years_list}
for sc in ['Best', 'Medium', 'Worst']:
    yearly = []
    for y in years_list:
        yearly.append(sum([calculate_future_value(breakdown[cat], cagr_dict[cat][sc], y) for cat in breakdown]))
    chart_data[sc] = yearly
chart_df = pd.DataFrame(chart_data)
fig = go.Figure()
for sc in ['Best', 'Medium', 'Worst']:
    fig.add_trace(go.Scatter(x=chart_df['Year'], y=chart_df[sc], mode='lines', name=sc))
fig.update_layout(title='Projected Total Corpus Over Time', xaxis_title='Year', yaxis_title='Corpus (₹)')
st.plotly_chart(fig, use_container_width=True)

# --- Tax Table Calculation: Loop Over Actual proj_table Index (supports labels like 'Best (xxx%)') ---
st.header("3. Tax Calculation (LTCG)")
tax_table = []
for sc in proj_table.index:
    # If formatted, strip '₹' and ',' before calculation
    corpus_val = proj_table.loc[sc, 'Total Corpus']
    if isinstance(corpus_val, str):
        corpus_val_num = float(corpus_val.replace('₹','').replace(',',''))
    else:
        corpus_val_num = corpus_val
    gain = corpus_val_num - investment
    taxable, tax = calculate_tax(gain, years)
    net = corpus_val_num - tax
    tax_table.append({
        'Scenario': sc,  # This may be 'Best (xxx%)' etc.
        'Total Gain': gain,
        'Taxable Gain': taxable,
        'Tax': tax,
        'Net Corpus': net
    })
tax_df = pd.DataFrame(tax_table).set_index('Scenario')
# Apply Indian formatting
for col in ['Total Gain', 'Taxable Gain', 'Tax', 'Net Corpus']:
    tax_df[col] = tax_df[col].apply(format_inr)

st.dataframe(tax_df)


st.header("4. Rebalancing Suggestions")
if current_portfolio:
    total_current = sum(current_portfolio.values())
    current_pct = {cat: current_portfolio.get(cat,0)/total_current for cat in allocation.keys()}
    rebalance_df = build_rebalance_table(current_pct, allocation)
    st.dataframe(rebalance_df)
else:
    st.info("Add current portfolio data in the sidebar to get rebalancing suggestions.")

# --- Export Section ---
st.header("5. Export Reports")
col1, col2 = st.columns(2)
with col1:
    csv = proj_table.to_csv().encode('utf-8')
    st.download_button("Download Projection (CSV)", csv, "projection.csv", "text/csv")
with col2:
    csv2 = tax_df.to_csv().encode('utf-8')
    st.download_button("Download Tax Calculation (CSV)", csv2, "tax_calculation.csv", "text/csv")

st.markdown("---")
st.caption("Mutual Fund Allocation & Projection App · Built with Python + Streamlit · © 2025")
