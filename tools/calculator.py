def calculate_growth_rate(old_value: float, new_value: float) -> float:
    """
    % growth from old to new.
    Example: 100 → 120 = 20% growth
    """
    if old_value == 0:
        return 0.0
    return round(((new_value - old_value) / abs(old_value)) * 100, 2)


def calculate_cagr(start_value: float, end_value: float, years: int) -> float:
    """
    Compound Annual Growth Rate.
    """
    if start_value <= 0 or years == 0:
        return 0.0
    return round(((end_value / start_value) ** (1 / years) - 1) * 100, 2)


def calculate_margin(revenue: float, profit: float) -> float:
    """
    Profit margin %.
    """
    if revenue == 0:
        return 0.0
    return round((profit / revenue) * 100, 2)


def calculate_pe_ratio(price: float, eps: float) -> float:
    """
    Price to Earnings ratio.
    """
    if eps == 0:
        return 0.0
    return round(price / eps, 2)


def summarize_metrics(stock_info: dict) -> dict:
    """
    Takes raw stock_info dict and returns clean calculated metrics.
    """
    print("\n🧮 Calculating financial metrics...")

    metrics = {}

    # Profit margin %
    if stock_info.get("profit_margin") not in ["N/A", None]:
        metrics["profit_margin_pct"] = round(
            float(stock_info["profit_margin"]) * 100, 2
        )

    # ROE %
    if stock_info.get("roe") not in ["N/A", None]:
        metrics["roe_pct"] = round(float(stock_info["roe"]) * 100, 2)

    # Dividend yield %
    if stock_info.get("dividend_yield") not in ["N/A", None]:
        metrics["dividend_yield_pct"] = round(
            float(stock_info["dividend_yield"]), 2
        )

    # PE Ratio
    if stock_info.get("pe_ratio") not in ["N/A", None]:
        metrics["pe_ratio"] = round(float(stock_info["pe_ratio"]), 2)

    # Market cap in Crores (Indian format)
    if stock_info.get("market_cap") not in ["N/A", None]:
        metrics["market_cap_crores"] = round(
            float(stock_info["market_cap"]) / 1e7, 2
        )

    # Revenue in Crores
    if stock_info.get("revenue") not in ["N/A", None]:
        metrics["revenue_crores"] = round(
            float(stock_info["revenue"]) / 1e7, 2
        )

    print("  ✅ Metrics calculated")
    return metrics


def format_metrics(metrics: dict) -> str:
    """
    Formats metrics into clean readable string.
    """
    formatted = "\n📊 Calculated Financial Metrics:\n"
    formatted += "=" * 40 + "\n"
    for key, value in metrics.items():
        label = key.replace("_", " ").title()
        formatted += f"  {label}: {value}\n"
    return formatted