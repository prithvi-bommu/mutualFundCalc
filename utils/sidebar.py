# --- Custom Allocation: Show Remaining Amount in Brackets When < 100% ---
import streamlit as st

from utils.currencyFromatter import format_inr


def sidebar_inputs(DEFAULT_INVESTMENT, DEFAULT_YEARS, DEFAULT_ALLOC, DEFAULT_CAGR, categories):
    st.sidebar.header("Input Parameters")

    investment = st.sidebar.number_input(
        "Total Investment (₹)", min_value=0, max_value=1_000_000_000,
        value=DEFAULT_INVESTMENT, step=5000
    )
    years = st.sidebar.number_input(
        "Investment Horizon (Years)", min_value=1, max_value=30,
        value=DEFAULT_YEARS, step=1
    )
    risk_profile = st.sidebar.selectbox(
        "Risk Appetite", options=list(DEFAULT_ALLOC.keys()), index=1
    )

    use_custom_alloc = st.sidebar.checkbox("Custom Allocation (%)", value=False)
    custom_alloc = None
    if use_custom_alloc:
        st.sidebar.markdown("#### Enter allocation percentages below")
        if 'text_allocations' not in st.session_state:
            st.session_state['text_allocations'] = [DEFAULT_ALLOC[risk_profile][cat] * 100 for cat in categories]

        # Text input for each category (number_input)
        alloc_inputs = []
        cols = st.sidebar.columns(len(categories))
        for idx, cat in enumerate(categories):
            alloc = cols[idx].number_input(f"{cat} %", min_value=0.0, max_value=100.0,
                                           value=st.session_state['text_allocations'][idx], step=1.0,
                                           key=f"input_{cat}")
            alloc_inputs.append(alloc)

        total_pct = sum(alloc_inputs)
        st.session_state['text_allocations'] = alloc_inputs
        btn_disabled = total_pct > 100 or total_pct == 0
        remaining_pct = 100 - total_pct
        remaining_amount = investment * remaining_pct / 100

        if total_pct > 100:
            st.sidebar.error(f"⚠️ Allocation exceeds 100% (Currently {total_pct:.1f}%). Please reduce.")
        elif total_pct < 100:
            st.sidebar.info(f"ℹ️ Remaining: {remaining_pct:.1f}% ({format_inr(remaining_amount)})")
        else:
            st.sidebar.success("✅ Total allocation: 100%")
        submit = st.sidebar.button("Submit Custom Allocation", disabled=btn_disabled)
        if submit and total_pct <= 100 and total_pct > 0:
            custom_alloc = {cat: alloc_inputs[i] / 100 for i, cat in enumerate(categories)}
            st.session_state['submitted_custom_alloc'] = custom_alloc
        elif 'submitted_custom_alloc' in st.session_state and total_pct <= 100 and total_pct > 0:
            # Use the last submitted allocation if form not submitted this run
            custom_alloc = st.session_state['submitted_custom_alloc']

    # CAGR Inputs
    st.sidebar.header("CAGR Assumptions (%)")
    cagr_dict = {}
    for cat in categories:
        st.sidebar.markdown(f"**{cat}**")
        cagr_dict[cat] = {
            'Best': st.sidebar.number_input(f"{cat} Best", 0.0, 100.0, float(DEFAULT_CAGR[cat]['Best']), step=0.1,
                                            key=f"{cat}_Best"),
            'Medium': st.sidebar.number_input(f"{cat} Medium", 0.0, 100.0, float(DEFAULT_CAGR[cat]['Medium']), step=0.1,
                                              key=f"{cat}_Medium"),
            'Worst': st.sidebar.number_input(f"{cat} Worst", 0.0, 100.0, float(DEFAULT_CAGR[cat]['Worst']), step=0.1,
                                             key=f"{cat}_Worst"),
        }

    # Portfolio JSON
    st.sidebar.header("Current Portfolio (Optional)")
    portfolio_json = st.sidebar.text_area("Current Portfolio JSON (e.g. {\"Large-Cap\":2000000,...})", value="")
    current_portfolio = None
    if portfolio_json:
        try:
            current_portfolio = eval(portfolio_json)
            if not isinstance(current_portfolio, dict):
                raise ValueError
        except:
            st.sidebar.error("Invalid JSON. Use a format like: {'Large-Cap':2000000,'Mid-Cap':500000}")

    allocation = custom_alloc if use_custom_alloc and custom_alloc is not None else {
        cat: DEFAULT_ALLOC[risk_profile][cat] for cat in categories}
    return investment, years, risk_profile, allocation, cagr_dict, current_portfolio
