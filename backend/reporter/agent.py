"""
Report Writer Agent - generates portfolio analysis narratives.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from agents import function_tool, RunContextWrapper
from agents.extensions.models.litellm_model import LitellmModel

from guardrails import sanitize_user_input

logger = logging.getLogger()


@dataclass
class ReporterContext:
    """Context for the Reporter agent"""

    job_id: str
    portfolio_data: Dict[str, Any]
    user_data: Dict[str, Any]
    db: Optional[Any] = None  


def calculate_asset_allocation(portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute asset allocation as fractions of the TOTAL portfolio (including cash).
    Uses the same methodology as the Retirement agent so both outputs are consistent.
    Returns dollar values alongside fractions.
    """
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
        return {
            "fractions": {"equity": 0, "fixed_income": 0, "commodities": 0, "real_estate": 0, "cash": 0},
            "dollars": {"equity": 0, "fixed_income": 0, "commodities": 0, "real_estate": 0, "cash": 0},
            "total_value": 0,
        }

    return {
        "fractions": {
            "equity": total_equity / total_value,
            "fixed_income": total_bonds / total_value,
            "commodities": total_commodities / total_value,
            "real_estate": total_real_estate / total_value,
            "cash": total_cash / total_value,
        },
        "dollars": {
            "equity": total_equity,
            "fixed_income": total_bonds,
            "commodities": total_commodities,
            "real_estate": total_real_estate,
            "cash": total_cash,
        },
        "total_value": total_value,
    }


def calculate_portfolio_metrics(portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate basic portfolio metrics."""
    metrics = {
        "total_value": 0,
        "cash_balance": 0,
        "num_accounts": len(portfolio_data.get("accounts", [])),
        "num_positions": 0,
        "unique_symbols": set(),
    }

    for account in portfolio_data.get("accounts", []):
        metrics["cash_balance"] += float(account.get("cash_balance", 0))
        positions = account.get("positions", [])
        metrics["num_positions"] += len(positions)

        for position in positions:
            symbol = position.get("symbol")
            if symbol:
                metrics["unique_symbols"].add(symbol)

            instrument = position.get("instrument", {})
            if instrument.get("current_price"):
                value = float(position.get("quantity", 0)) * float(instrument["current_price"])
                metrics["total_value"] += value

    metrics["total_value"] += metrics["cash_balance"]
    metrics["unique_symbols"] = len(metrics["unique_symbols"])

    return metrics


def format_portfolio_for_analysis(portfolio_data: Dict[str, Any], user_data: Dict[str, Any]) -> str:
    """Format portfolio data for agent analysis."""
    metrics = calculate_portfolio_metrics(portfolio_data)

    lines = [
        f"Portfolio Overview:",
        f"- {metrics['num_accounts']} accounts",
        f"- {metrics['num_positions']} total positions",
        f"- {metrics['unique_symbols']} unique holdings",
        f"- ${metrics['cash_balance']:,.2f} in cash",
        f"- ${metrics['total_value']:,.2f} total value" if metrics["total_value"] > 0 else "",
        "",
        "Account Details:",
    ]

    for account in portfolio_data.get("accounts", []):
        name = sanitize_user_input(account.get("name") or "Unknown")
        cash = float(account.get("cash_balance", 0))
        lines.append(f"\n{name} (${cash:,.2f} cash):")

        for position in account.get("positions", []):
            symbol = position.get("symbol")
            quantity = float(position.get("quantity", 0))
            instrument = position.get("instrument", {})
            inst_name = sanitize_user_input(instrument.get("name") or "")
            inst_type = instrument.get("instrument_type", "")
            price = instrument.get("current_price", 0)

            details = []
            if inst_name:
                details.append(inst_name)
            if inst_type:
                details.append(f"type={inst_type}")
            if price:
                details.append(f"price=${float(price):,.2f}")

            asset_class = instrument.get("allocation_asset_class", {})
            if asset_class and isinstance(asset_class, dict):
                primary = max(asset_class, key=asset_class.get)
                details.append(f"asset_class={primary}({asset_class[primary]:.0f}%)")

            regions = instrument.get("allocation_regions", {})
            if regions and isinstance(regions, dict):
                top_regions = sorted(regions.items(), key=lambda x: x[1], reverse=True)[:2]
                region_str = ", ".join(f"{r}({p:.0f}%)" for r, p in top_regions)
                details.append(f"regions={region_str}")

            sectors = instrument.get("allocation_sectors", {})
            if sectors and isinstance(sectors, dict):
                top_sectors = sorted(sectors.items(), key=lambda x: x[1], reverse=True)[:2]
                sector_str = ", ".join(f"{s}({p:.0f}%)" for s, p in top_sectors)
                details.append(f"sectors={sector_str}")

            detail_str = f" [{'; '.join(details)}]" if details else ""
            lines.append(f"  - {symbol}: {quantity:,.2f} shares{detail_str}")

    lines.extend(
        [
            "",
            "User Profile:",
            f"- Years to retirement: {user_data.get('years_until_retirement', 'Not specified')}",
            f"- Target retirement income: ${user_data.get('target_retirement_income', 0):,.0f}/year",
        ]
    )

    alloc = calculate_asset_allocation(portfolio_data)
    fractions = alloc["fractions"]
    dollars = alloc["dollars"]
    total = alloc["total_value"]

    lines.append("")
    lines.append("PRE-COMPUTED PORTFOLIO ALLOCATION (verified Python calculation — use these exact figures, do not recalculate):")
    lines.append(f"Total portfolio value (including cash): ${total:,.2f}")
    for label, key in [("Cash", "cash"), ("Equity", "equity"), ("Fixed Income", "fixed_income"), ("Commodities", "commodities"), ("Real Estate", "real_estate")]:
        frac = fractions.get(key, 0)
        dol = dollars.get(key, 0)
        if frac > 0:
            lines.append(f"  {label}: {frac:.1%} (${dol:,.2f}) — of total portfolio including cash")

    return "\n".join(lines)


@function_tool
async def get_market_insights(
    wrapper: RunContextWrapper[ReporterContext], symbols: List[str]
) -> str:
    """
    Retrieve market insights from S3 Vectors knowledge base.

    Args:
        wrapper: Context wrapper with job_id and database
        symbols: List of symbols to get insights for

    Returns:
        Relevant market context and insights
    """
    try:
        import boto3

        sts = boto3.client("sts")
        account_id = sts.get_caller_identity()["Account"]
        bucket = f"stratos-vectors-{account_id}"

        sagemaker_region = os.getenv("DEFAULT_AWS_REGION", "us-east-1")
        sagemaker = boto3.client("sagemaker-runtime", region_name=sagemaker_region)
        endpoint_name = os.getenv("SAGEMAKER_ENDPOINT", "stratos-embedding-endpoint")
        query = f"market analysis {' '.join(symbols[:5])}" if symbols else "market outlook"

        response = sagemaker.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType="application/json",
            Body=json.dumps({"inputs": query}),
        )

        result = json.loads(response["Body"].read().decode())
        if isinstance(result, list) and result:
            embedding = result[0][0] if isinstance(result[0], list) else result[0]
        else:
            embedding = result

        s3v = boto3.client("s3vectors", region_name=sagemaker_region)
        response = s3v.query_vectors(
            vectorBucketName=bucket,
            indexName="financial-research",
            queryVector={"float32": embedding},
            topK=3,
            returnMetadata=True,
        )

        insights = []
        for vector in response.get("vectors", []):
            metadata = vector.get("metadata", {})
            text = metadata.get("text", "")[:200]
            if text:
                company = metadata.get("company_name", "")
                prefix = f"{company}: " if company else "- "
                insights.append(f"{prefix}{text}...")

        if insights:
            return "Market Insights:\n" + "\n".join(insights)
        else:
            return "Market insights unavailable - proceeding with standard analysis."

    except Exception as e:
        logger.warning(f"Reporter: Could not retrieve market insights: {e}")
        return "Market insights unavailable - proceeding with standard analysis."


def create_agent(job_id: str, portfolio_data: Dict[str, Any], user_data: Dict[str, Any], db=None):
    """Create the reporter agent with tools and context."""

    model_id = os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
    bedrock_region = os.getenv("BEDROCK_REGION", "us-east-1")
    logger.info(f"DEBUG: BEDROCK_REGION from env = {bedrock_region}")
    os.environ["AWS_REGION_NAME"] = bedrock_region
    logger.info(f"DEBUG: Set AWS_REGION_NAME to {bedrock_region}")

    model = LitellmModel(model=f"bedrock/{model_id}")

    context = ReporterContext(
        job_id=job_id, portfolio_data=portfolio_data, user_data=user_data, db=db
    )
    
    tools = [get_market_insights]

    portfolio_summary = format_portfolio_for_analysis(portfolio_data, user_data)

    task = f"""Analyze this investment portfolio and write a comprehensive report.

{portfolio_summary}

CRITICAL — ALLOCATION FIGURES: The portfolio summary above contains a section labeled
"PRE-COMPUTED PORTFOLIO ALLOCATION". These figures were calculated in Python and are
mathematically verified. You MUST use these exact percentages and dollar values when
reporting asset allocation in the report. Do NOT attempt to recalculate them from the
per-instrument data — doing so will produce incorrect results. All percentages are of
the TOTAL portfolio including cash.

Your task:
1. First, get market insights for the top holdings using get_market_insights()
2. Analyze the portfolio's current state, strengths, and weaknesses
3. Generate a detailed, professional analysis report in markdown format

The report should include:
- Executive Summary
- Portfolio Composition Analysis (use the PRE-COMPUTED ALLOCATION figures exactly)
- Risk Assessment
- Diversification Analysis
- Retirement Readiness (based on user goals)
- Recommendations
- Market Context (from insights)

Provide your complete analysis as the final output in clear markdown format.
Make the report informative yet accessible to a retail investor."""

    return model, tools, task, context
