import yfinance as yf


def get_stock_info(ticker: str) -> dict:
    print(f"\n📊 Fetching stock info: {ticker}")
    stock = yf.Ticker(ticker)
    info = stock.info

    # Get revenue with currency detection
    revenue_raw = info.get("totalRevenue", "N/A")
    currency = info.get("currency", "INR")

    if revenue_raw != "N/A" and revenue_raw is not None:
        if currency == "USD":
            revenue_inr_crores = round(float(revenue_raw) * 83 / 1e7, 2)
        else:
            revenue_inr_crores = round(float(revenue_raw) / 1e7, 2)
        # Sanity check — if revenue looks too low for a major company, mark as unreliable
        if isinstance(revenue_inr_crores, float) and revenue_inr_crores < 10000:
            revenue_inr_crores = f"{revenue_inr_crores} (⚠️ verify — yfinance may have incomplete data)"
    else:
        revenue_inr_crores = "N/A"

    result = {
        "name": info.get("longName", "N/A"),
        "sector": info.get("sector", "N/A"),
        "industry": info.get("industry", "N/A"),
        "market_cap": info.get("marketCap", "N/A"),
        "current_price": info.get("currentPrice", "N/A"),
        "52_week_high": info.get("fiftyTwoWeekHigh", "N/A"),
        "52_week_low": info.get("fiftyTwoWeekLow", "N/A"),
        "pe_ratio": info.get("trailingPE", "N/A"),
        "eps": info.get("trailingEps", "N/A"),
        "dividend_yield": info.get("dividendYield", "N/A"),
        "revenue_crores": revenue_inr_crores,
        "profit_margin": info.get("profitMargins", "N/A"),
        "debt_to_equity": info.get("debtToEquity", "N/A"),
        "roe": info.get("returnOnEquity", "N/A"),
    }

    print(f"  ✅ Got data for {result['name']}")
    return result


def get_financials(ticker: str) -> dict:
    print(f"\n📈 Fetching financials: {ticker}")
    stock = yf.Ticker(ticker)

    result = {
        "income_statement": stock.financials.to_dict() if not stock.financials.empty else {},
        "balance_sheet": stock.balance_sheet.to_dict() if not stock.balance_sheet.empty else {},
        "cash_flow": stock.cashflow.to_dict() if not stock.cashflow.empty else {},
    }

    print(f"  ✅ Financials fetched")
    return result


def get_historical_prices(ticker: str, period: str = "1y") -> list[dict]:
    print(f"\n📉 Fetching price history: {ticker} ({period})")
    stock = yf.Ticker(ticker)
    hist = stock.history(period=period)

    prices = []
    for date, row in hist.iterrows():
        prices.append({
            "date": str(date.date()),
            "close": round(row["Close"], 2),
            "volume": int(row["Volume"])
        })

    print(f"  ✅ Got {len(prices)} data points")
    return prices


def format_stock_info(info: dict) -> str:
    """
    Formats stock info into clean readable string for LLM.
    All monetary values in ₹ Crores.
    """
    formatted = f"\n{'='*40}\n"
    formatted += f"📊 {info['name']}\n"
    formatted += f"{'='*40}\n"

    for key, value in info.items():
        if key == "name":
            continue

        label = key.replace("_", " ").title()

        if key == "revenue_crores":
            formatted += f"  Revenue: ₹{value} Crores\n"

        elif key == "market_cap" and value not in ["N/A", None]:
            try:
                crore_value = round(float(value) / 1e7, 2)
                formatted += f"  Market Cap: ₹{crore_value:,.2f} Crores\n"
            except:
                formatted += f"  Market Cap: {value}\n"

        elif key in ["profit_margin", "roe"] and value not in ["N/A", None]:
            try:
                pct = round(float(value) * 100, 2)
                formatted += f"  {label}: {pct}%\n"
            except:
                formatted += f"  {label}: {value}\n"

        else:
            formatted += f"  {label}: {value}\n"

    return formatted