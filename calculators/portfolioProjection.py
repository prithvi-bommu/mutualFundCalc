from calculators.futureValue import calculate_future_value


def calc_portfolio_projection(breakdown, cagr_dict, years):
    scenarios = ['Best', 'Medium', 'Worst']
    results = {sc: {} for sc in scenarios}
    for sc in scenarios:
        for cat, amt in breakdown.items():
            results[sc][cat] = calculate_future_value(amt, cagr_dict[cat][sc], years)
    return results