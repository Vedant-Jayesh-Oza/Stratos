"""
Retirement Specialist Agent - provides retirement planning analysis and projections.
"""

import os
import json
import logging
import random
from typing import Dict, Any
from datetime import datetime

from agents.extensions.models.litellm_model import LitellmModel

logger = logging.getLogger()



def calculate_portfolio_value(portfolio_data: Dict[str, Any]) -> float:
    """Calculate current portfolio value."""
    total_value = 0.0

    for account in portfolio_data.get("accounts", []):
        cash = float(account.get("cash_balance", 0))
        total_value += cash

        for position in account.get("positions", []):
            quantity = float(position.get("quantity", 0))
            instrument = position.get("instrument", {})
            price = float(instrument.get("current_price", 100))
            total_value += quantity * price

    return total_value


def calculate_asset_allocation(portfolio_data: Dict[str, Any]) -> Dict[str, float]:
    """Calculate asset allocation percentages."""
    total_equity = 0.0
    total_bonds = 0.0
    total_real_estate = 0.0
    total_commodities = 0.0
    total_cash = 0.0
    total_value = 0.0

    for account in portfolio_data.get("accounts", []):
        cash = float(account.get("cash_balance", 0))
        total_cash += cash
        total_value += cash

        for position in account.get("positions", []):
            quantity = float(position.get("quantity", 0))
            instrument = position.get("instrument", {})
            price = float(instrument.get("current_price", 100))
            value = quantity * price
            total_value += value

            asset_allocation = instrument.get("allocation_asset_class", {})
            if asset_allocation:
                total_equity += value * asset_allocation.get("equity", 0) / 100
                total_bonds += value * asset_allocation.get("fixed_income", 0) / 100
                total_real_estate += value * asset_allocation.get("real_estate", 0) / 100
                total_commodities += value * asset_allocation.get("commodities", 0) / 100

    if total_value == 0:
        return {"equity": 0, "bonds": 0, "real_estate": 0, "commodities": 0, "cash": 0}

    return {
        "equity": total_equity / total_value,
        "bonds": total_bonds / total_value,
        "real_estate": total_real_estate / total_value,
        "commodities": total_commodities / total_value,
        "cash": total_cash / total_value,
    }


EQUITY_RETURN_MEAN = 0.07
EQUITY_RETURN_STD = 0.18
BOND_RETURN_MEAN = 0.04
BOND_RETURN_STD = 0.05
REAL_ESTATE_RETURN_MEAN = 0.06
REAL_ESTATE_RETURN_STD = 0.12
ANNUAL_CONTRIBUTION = 10000
INFLATION_RATE = 1.03
RETIREMENT_DURATION = 30


def _portfolio_return(asset_allocation: Dict[str, float]) -> float:
    """Single year stochastic portfolio return based on allocation."""
    return (
        asset_allocation["equity"] * random.gauss(EQUITY_RETURN_MEAN, EQUITY_RETURN_STD)
        + asset_allocation["bonds"] * random.gauss(BOND_RETURN_MEAN, BOND_RETURN_STD)
        + asset_allocation["real_estate"] * random.gauss(REAL_ESTATE_RETURN_MEAN, REAL_ESTATE_RETURN_STD)
        + asset_allocation.get("commodities", 0) * random.gauss(0.04, 0.15)
        + asset_allocation["cash"] * 0.02
    )


def run_monte_carlo_simulation(
    current_value: float,
    years_until_retirement: int,
    target_annual_income: float,
    asset_allocation: Dict[str, float],
    current_age: int = 40,
    num_simulations: int = 500,
) -> Dict[str, Any]:
    """Run Monte Carlo simulation and derive consistent projections from it."""

    total_years = years_until_retirement + RETIREMENT_DURATION
    milestone_years = sorted(set(
        list(range(0, total_years + 1, 5)) + [years_until_retirement]
    ))

    all_paths = []
    successful_scenarios = 0
    final_values = []
    years_lasted = []

    for _ in range(num_simulations):
        path = {}
        portfolio_value = current_value

        for year in range(1, years_until_retirement + 1):
            portfolio_value = portfolio_value * (1 + _portfolio_return(asset_allocation))
            portfolio_value += ANNUAL_CONTRIBUTION
            if year in milestone_years:
                path[year] = portfolio_value

        value_at_retirement = portfolio_value
        annual_withdrawal = target_annual_income
        years_income_lasted = 0

        for year_offset in range(1, RETIREMENT_DURATION + 1):
            if portfolio_value <= 0:
                break
            annual_withdrawal *= INFLATION_RATE
            portfolio_value = portfolio_value * (1 + _portfolio_return(asset_allocation)) - annual_withdrawal
            if portfolio_value > 0:
                years_income_lasted += 1
            abs_year = years_until_retirement + year_offset
            if abs_year in milestone_years:
                path[abs_year] = max(0, portfolio_value)

        final_values.append(max(0, portfolio_value))
        years_lasted.append(years_income_lasted)
        all_paths.append(path)

        if years_income_lasted >= RETIREMENT_DURATION:
            successful_scenarios += 1

    final_values.sort()
    success_rate = (successful_scenarios / num_simulations) * 100

    projections = []
    for year in milestone_years:
        if year == 0:
            projections.append({
                "year": year, "age": current_age,
                "p10": round(current_value), "median": round(current_value), "p90": round(current_value),
                "phase": "accumulation", "annual_income": 0,
            })
            continue

        values_at_year = sorted(p.get(year, 0) for p in all_paths)
        p10 = values_at_year[max(0, num_simulations // 10)]
        median = values_at_year[num_simulations // 2]
        p90 = values_at_year[min(num_simulations - 1, 9 * num_simulations // 10)]
        phase = "accumulation" if year <= years_until_retirement else "retirement"
        annual_income = round(median * 0.04) if phase == "retirement" else 0

        projections.append({
            "year": year, "age": current_age + year,
            "p10": round(p10), "median": round(median), "p90": round(p90),
            "phase": phase, "annual_income": annual_income,
        })

    return {
        "success_rate": round(success_rate, 1),
        "median_final_value": round(final_values[num_simulations // 2], 2),
        "percentile_10": round(final_values[num_simulations // 10], 2),
        "percentile_90": round(final_values[9 * num_simulations // 10], 2),
        "average_years_lasted": round(sum(years_lasted) / len(years_lasted), 1),
        "median_value_at_retirement": round(
            sorted(p.get(years_until_retirement, 0) for p in all_paths)[num_simulations // 2]
        ),
        "projections": projections,
    }



def create_agent(
    job_id: str, portfolio_data: Dict[str, Any], user_preferences: Dict[str, Any], db=None
):
    """Create the retirement agent with tools and context."""

    model_id = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
    bedrock_region = os.getenv("BEDROCK_REGION", "us-east-1")
    os.environ["AWS_REGION_NAME"] = bedrock_region

    model = LitellmModel(model=f"bedrock/{model_id}")

    years_until_retirement = user_preferences.get("years_until_retirement", 30)
    target_income = user_preferences.get("target_retirement_income", 80000)
    current_age = user_preferences.get("current_age", 40)

    portfolio_value = calculate_portfolio_value(portfolio_data)
    allocation = calculate_asset_allocation(portfolio_data)

    monte_carlo = run_monte_carlo_simulation(
        portfolio_value, years_until_retirement, target_income, allocation,
        current_age=current_age, num_simulations=500,
    )

    projections = monte_carlo["projections"]

    tools = []

    task = f"""
# Portfolio Analysis Context

## Current Situation
- Portfolio Value: ${portfolio_value:,.0f}
- Asset Allocation: {", ".join([f"{k.title()}: {v:.0%}" for k, v in allocation.items() if v > 0])}
- Years to Retirement: {years_until_retirement}
- Target Annual Income: ${target_income:,.0f}
- Current Age: {current_age}

## Monte Carlo Simulation Results (500 scenarios)
- Success Rate: {monte_carlo["success_rate"]}% (probability of sustaining ${target_income:,.0f}/yr income for 30 years)
- Median Portfolio Value at Retirement: ${monte_carlo["median_value_at_retirement"]:,.0f}
- 10th Percentile Final Value (bad luck): ${monte_carlo["percentile_10"]:,.0f}
- Median Final Value (after 30yr retirement): ${monte_carlo["median_final_value"]:,.0f}
- 90th Percentile Final Value (good luck): ${monte_carlo["percentile_90"]:,.0f}
- Average Years Portfolio Lasts: {monte_carlo["average_years_lasted"]} years

## Projected Milestones (derived from the Monte Carlo paths above)
| Age | 10th %ile | Median | 90th %ile | Phase |
|-----|-----------|--------|-----------|-------|
"""

    for proj in projections:
        if proj["phase"] == "accumulation":
            task += f"| {proj['age']} | ${proj['p10']:,.0f} | ${proj['median']:,.0f} | ${proj['p90']:,.0f} | Accumulation |\n"
        else:
            task += f"| {proj['age']} | ${proj['p10']:,.0f} | ${proj['median']:,.0f} | ${proj['p90']:,.0f} | Retirement (est. income ${proj['annual_income']:,.0f}/yr) |\n"

    task += f"""
NOTE: The projections above come directly from the same 500 Monte Carlo simulations.
A success rate of {monte_carlo["success_rate"]}% means only {monte_carlo["success_rate"]}% of the 500 paths sustained the target income for 30 years.
The median path shows the 50th percentile outcome — not a guaranteed result.

## Risk Factors to Consider
- Sequence of returns risk (poor returns early in retirement)
- Inflation impact (3% assumed)
- Healthcare costs in retirement
- Longevity risk (living beyond 30 years)
- Market volatility (equity standard deviation: 18%)

## Safe Withdrawal Rate Analysis
- 4% Rule: ${portfolio_value * 0.04:,.0f} initial annual income
- Target Income: ${target_income:,.0f}
- Gap: ${target_income - (portfolio_value * 0.04):,.0f}

Your task: Analyze this retirement readiness data and provide a comprehensive retirement analysis including:
1. Clear assessment of retirement readiness based on the {monte_carlo["success_rate"]}% success rate
2. Specific recommendations to improve success rate
3. Risk mitigation strategies
4. Action items with timeline

IMPORTANT: The projections and the success rate come from the same simulation.
If the success rate is low, acknowledge that most paths fail — do NOT present the median path as guaranteed.

Provide your analysis in clear markdown format with specific numbers and actionable recommendations.
"""

    return model, tools, task
