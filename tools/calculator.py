def calculate_growth_rate(old_value: float, new_value: float) -> float:
    if old_value == 0:
        return 0.0
    return round(((new_value - old_value) / abs(old_value)) * 100, 2)


def calculate_cagr(start_value: float, end_value: float, years: int) -> float:
    if start_value <= 0 or years == 0:
        return 0.0
    return round(((end_value / start_value) ** (1 / years) - 1) * 100, 2)


def calculate_margin(revenue: float, profit: float) -> float:
    if revenue == 0:
        return 0.0
    return round((profit / revenue) * 100, 2)


def calculate_pe_ratio(price: float, eps: float) -> float:
    if eps == 0:
        return 0.0
    return round(price / eps, 2)


def summarize_metrics(stock_info: dict) -> dict:
    print("\n🧮 Calculating financial metrics...")
    metrics = {}

    if stock_info.get("profit_margin") not in ["N/A", None]:
        metrics["profit_margin_pct"] = round(float(stock_info["profit_margin"]) * 100, 2)

    if stock_info.get("roe") not in ["N/A", None]:
        metrics["roe_pct"] = round(float(stock_info["roe"]) * 100, 2)

    if stock_info.get("dividend_yield") not in ["N/A", None]:
        metrics["dividend_yield_pct"] = round(float(stock_info["dividend_yield"]), 2)

    if stock_info.get("pe_ratio") not in ["N/A", None]:
        metrics["pe_ratio"] = round(float(stock_info["pe_ratio"]), 2)

    if stock_info.get("market_cap") not in ["N/A", None]:
        metrics["market_cap_crores"] = round(float(stock_info["market_cap"]) / 1e7, 2)

    if stock_info.get("revenue") not in ["N/A", None]:
        metrics["revenue_crores"] = round(float(stock_info["revenue"]) / 1e7, 2)

    print("  ✅ Metrics calculated")
    return metrics


def format_metrics(metrics: dict) -> str:
    formatted = "\n📊 Calculated Financial Metrics:\n"
    formatted += "=" * 40 + "\n"
    for key, value in metrics.items():
        label = key.replace("_", " ").title()
        formatted += f"  {label}: {value}\n"
    return formatted


def extract_revenue_inr_from_text(text: str) -> dict:
    """
    Extracts ALL INR revenue values with years dynamically.
    Returns: {year: revenue}
    Strategy: find all large numbers (>50000) near a year on the same line.
    """
    import re

    revenue_data = {}

    # Split into lines — revenue tables are line-based
    lines = text.split("\n")

    for line in lines:
        # Find any year in the line
        years_in_line = re.findall(r"\b(20\d{2})\b", line)
        if not years_in_line:
            continue

        # Find all numbers in the line
        numbers_in_line = re.findall(r"(\d{1,3}(?:,\d{2,3})+)", line)

        large_numbers = []
        for num_str in numbers_in_line:
            try:
                num = float(num_str.replace(",", ""))
                if num >= 50000:
                    large_numbers.append(num)
            except:
                continue

        if not large_numbers:
            continue

        # Use the largest number on the line as revenue
        # (avoids picking employee count or market cap by mistake)
        best_value = max(large_numbers)

        for year in years_in_line:
            # Only update if not already found or new value is more reliable
            if year not in revenue_data:
                revenue_data[year] = best_value

    return revenue_data
# def calculate_growth_rate(old_value: float, new_value: float) -> float:
#     """
#     % growth from old to new.
#     Example: 100 → 120 = 20% growth
#     """
#     if old_value == 0:
#         return 0.0
#     return round(((new_value - old_value) / abs(old_value)) * 100, 2)


# def calculate_cagr(start_value: float, end_value: float, years: int) -> float:
#     """
#     Compound Annual Growth Rate.
#     """
#     if start_value <= 0 or years == 0:
#         return 0.0
#     return round(((end_value / start_value) ** (1 / years) - 1) * 100, 2)


# def calculate_margin(revenue: float, profit: float) -> float:
#     """
#     Profit margin %.
#     """
#     if revenue == 0:
#         return 0.0
#     return round((profit / revenue) * 100, 2)


# def calculate_pe_ratio(price: float, eps: float) -> float:
#     """
#     Price to Earnings ratio.
#     """
#     if eps == 0:
#         return 0.0
#     return round(price / eps, 2)


# def summarize_metrics(stock_info: dict) -> dict:
#     """
#     Takes raw stock_info dict and returns clean calculated metrics.
#     """
#     print("\n🧮 Calculating financial metrics...")

#     metrics = {}

#     # Profit margin %
#     if stock_info.get("profit_margin") not in ["N/A", None]:
#         metrics["profit_margin_pct"] = round(
#             float(stock_info["profit_margin"]) * 100, 2
#         )

#     # ROE %
#     if stock_info.get("roe") not in ["N/A", None]:
#         metrics["roe_pct"] = round(float(stock_info["roe"]) * 100, 2)

#     # Dividend yield %
#     if stock_info.get("dividend_yield") not in ["N/A", None]:
#         metrics["dividend_yield_pct"] = round(
#             float(stock_info["dividend_yield"]), 2
#         )

#     # PE Ratio
#     if stock_info.get("pe_ratio") not in ["N/A", None]:
#         metrics["pe_ratio"] = round(float(stock_info["pe_ratio"]), 2)

#     # Market cap in Crores (Indian format)
#     if stock_info.get("market_cap") not in ["N/A", None]:
#         metrics["market_cap_crores"] = round(
#             float(stock_info["market_cap"]) / 1e7, 2
#         )

#     # Revenue in Crores
#     if stock_info.get("revenue") not in ["N/A", None]:
#         metrics["revenue_crores"] = round(
#             float(stock_info["revenue"]) / 1e7, 2
#         )

#     print("  ✅ Metrics calculated")
#     return metrics


# def format_metrics(metrics: dict) -> str:
#     """
#     Formats metrics into clean readable string.
#     """
#     formatted = "\n📊 Calculated Financial Metrics:\n"
#     formatted += "=" * 40 + "\n"
#     for key, value in metrics.items():
#         label = key.replace("_", " ").title()
#         formatted += f"  {label}: {value}\n"
#     return formatted
# def extract_revenue_inr_from_text(text: str) -> dict:
#     """
#     Extracts ALL INR revenue values with years dynamically.
#     Returns: {year: revenue}
#     """
#     import re

#     # Pattern: year + number (handles tables like 2024 153,670)
#     matches = re.findall(r"(20\d{2}).{0,50}?(?:₹|INR)?.{0,10}?(\d{1,3}(?:,\d{3})+)", text)
#     revenue_data = {}

#     for year, value in matches:
#      try:
#         num = float(value.replace(",", ""))

#         # 🔥 CRITICAL FILTER
#         # Ignore small values (USD million etc.)
#         if num < 50000:
#             continue

#         revenue_data[year] = num
#      except:
#         continue

#     return revenue_data