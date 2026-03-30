def classify_risk_tier(
    volatility: float,
    max_drawdown: float,
    beta: float,
) -> str:
    score = 0

    if volatility < 0.10:
        score += 1
    elif volatility < 0.20:
        score += 2
    elif volatility < 0.35:
        score += 3
    else:
        score += 4

    mdd = abs(max_drawdown)
    if mdd < 0.10:
        score += 1
    elif mdd < 0.20:
        score += 2
    elif mdd < 0.40:
        score += 3
    else:
        score += 4

    if beta < 0.5:
        score += 1
    elif beta < 1.0:
        score += 2
    elif beta < 1.5:
        score += 3
    else:
        score += 4

    avg = score / 3
    if avg <= 1.5:
        return "Conservative"
    elif avg <= 2.5:
        return "Moderate"
    elif avg <= 3.5:
        return "Aggressive"
    else:
        return "Speculative"


def generate_risk_summary(metrics: dict) -> str:
    ticker = metrics.get("ticker", "This asset")
    tier = metrics.get("risk_tier", "Unknown")
    vol = metrics.get("annualized_volatility", 0)
    mdd = metrics.get("max_drawdown", 0)
    sharpe = metrics.get("sharpe_ratio")
    beta_val = metrics.get("beta", 1.0)

    vol_pct = f"{vol * 100:.1f}%"
    mdd_pct = f"{abs(mdd) * 100:.1f}%"
    sharpe_str = f"{sharpe:.2f}" if sharpe is not None else "N/A"

    summary = (
        f"{ticker} is classified as a {tier} asset with annualized volatility of {vol_pct} "
        f"and a maximum historical drawdown of {mdd_pct}. "
    )

    if tier == "Conservative":
        summary += "It exhibits low price fluctuations, making it suitable for risk-averse investors. "
    elif tier == "Moderate":
        summary += "It offers a balance between growth potential and risk, suitable for medium-horizon investors. "
    elif tier == "Aggressive":
        summary += "It carries significant price risk and is best suited for investors with a high risk tolerance. "
    else:
        summary += "It exhibits extreme price swings and speculative characteristics; only suitable for sophisticated investors. "

    summary += (
        f"With a beta of {beta_val:.2f} relative to the benchmark, it "
        + ("moves less than the market" if beta_val < 1 else "amplifies market movements")
        + f". The Sharpe ratio of {sharpe_str} reflects its risk-adjusted return profile."
    )

    return summary
