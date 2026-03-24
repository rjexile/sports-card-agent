"""
Grading ROI calculator for sports cards.
Estimates whether it's profitable to send a raw card for professional grading
by comparing raw vs graded price differences against grading costs.
"""

from dataclasses import dataclass
from .ebay_client import EbayClient, PriceResult


# Average grading costs per company (as of 2025-2026)
GRADING_COSTS = {
    "PSA": {
        "economy": {"cost": 25, "turnaround": "120+ days"},
        "regular": {"cost": 50, "turnaround": "65 business days"},
        "express": {"cost": 100, "turnaround": "20 business days"},
        "super_express": {"cost": 200, "turnaround": "10 business days"},
        "walk_through": {"cost": 600, "turnaround": "5 business days"},
    },
    "BGS": {
        "economy": {"cost": 25, "turnaround": "120+ days"},
        "standard": {"cost": 50, "turnaround": "45 business days"},
        "express": {"cost": 150, "turnaround": "10 business days"},
        "premium": {"cost": 300, "turnaround": "5 business days"},
    },
    "SGC": {
        "economy": {"cost": 20, "turnaround": "90+ days"},
        "regular": {"cost": 30, "turnaround": "30 business days"},
        "express": {"cost": 100, "turnaround": "10 business days"},
    },
}


@dataclass
class GradingROI:
    card_query: str
    raw_avg_price: float
    graded_avg_price: float
    grading_company: str
    grading_tier: str
    grading_cost: float
    turnaround: str
    price_uplift: float  # graded - raw
    net_profit: float  # uplift - grading cost
    roi_pct: float  # net_profit / (raw + grading_cost) * 100
    recommendation: str
    reasoning: list[str]

    def summary(self) -> str:
        lines = [
            f"=== Grading ROI Analysis: '{self.card_query}' ===",
            f"",
            f"Raw Card Value:       ${self.raw_avg_price:.2f}",
            f"Graded Card Value:    ${self.graded_avg_price:.2f}",
            f"Price Uplift:         ${self.price_uplift:.2f}",
            f"",
            f"Grading Company:      {self.grading_company}",
            f"Service Tier:         {self.grading_tier}",
            f"Grading Cost:         ${self.grading_cost:.2f}",
            f"Turnaround:           {self.turnaround}",
            f"",
            f"Net Profit:           ${self.net_profit:.2f}",
            f"ROI:                  {self.roi_pct:.1f}%",
            f"",
            f"Recommendation:       {self.recommendation}",
        ]

        if self.reasoning:
            lines.append(f"\n--- Details ---")
            for r in self.reasoning:
                lines.append(f"  * {r}")

        return "\n".join(lines)


async def calculate_grading_roi(
    client: EbayClient,
    card_query: str,
    grading_company: str = "PSA",
    expected_grade: str = "10",
) -> GradingROI:
    """
    Calculate whether grading a card is worth the investment.
    Compares raw card prices vs graded (at the expected grade) prices.
    """
    # Search for raw version
    raw_result = await client.search_sold(f"{card_query} raw", limit=15)

    # Search for graded version
    graded_query = f"{card_query} {grading_company} {expected_grade}"
    graded_result = await client.search_sold(graded_query, limit=15)

    raw_avg = raw_result.avg_price
    graded_avg = graded_result.avg_price

    # Pick the best grading tier
    company_key = grading_company.upper()
    if company_key not in GRADING_COSTS:
        company_key = "PSA"

    tiers = GRADING_COSTS[company_key]
    best_tier, best_roi_data = _find_best_tier(raw_avg, graded_avg, tiers)
    tier_info = tiers[best_tier]

    price_uplift = graded_avg - raw_avg
    grading_cost = tier_info["cost"]
    net_profit = price_uplift - grading_cost
    total_investment = raw_avg + grading_cost
    roi_pct = (net_profit / total_investment * 100) if total_investment > 0 else 0

    # Generate recommendation
    recommendation, reasoning = _generate_recommendation(
        raw_avg, graded_avg, grading_cost, net_profit, roi_pct,
        expected_grade, grading_company, raw_result, graded_result,
    )

    return GradingROI(
        card_query=card_query,
        raw_avg_price=raw_avg,
        graded_avg_price=graded_avg,
        grading_company=company_key,
        grading_tier=best_tier,
        grading_cost=grading_cost,
        turnaround=tier_info["turnaround"],
        price_uplift=price_uplift,
        net_profit=net_profit,
        roi_pct=roi_pct,
        recommendation=recommendation,
        reasoning=reasoning,
    )


def _find_best_tier(
    raw_avg: float, graded_avg: float, tiers: dict
) -> tuple[str, dict]:
    """Find the grading tier with the best ROI."""
    best_tier = None
    best_roi = float("-inf")

    for tier_name, tier_info in tiers.items():
        cost = tier_info["cost"]
        net = graded_avg - raw_avg - cost
        investment = raw_avg + cost
        roi = (net / investment * 100) if investment > 0 else 0

        if roi > best_roi:
            best_roi = roi
            best_tier = tier_name

    return best_tier or list(tiers.keys())[0], {"roi": best_roi}


def _generate_recommendation(
    raw_avg, graded_avg, grading_cost, net_profit, roi_pct,
    expected_grade, company, raw_result, graded_result,
) -> tuple[str, list[str]]:
    """Generate a human-readable grading recommendation."""
    reasoning = []

    # ROI-based recommendation
    if roi_pct > 100:
        recommendation = "STRONG YES — Grade this card"
        reasoning.append(
            f"Excellent ROI of {roi_pct:.0f}%. The graded price premium "
            f"far exceeds grading costs."
        )
    elif roi_pct > 40:
        recommendation = "YES — Worth grading"
        reasoning.append(
            f"Good ROI of {roi_pct:.0f}%. Grading should be profitable."
        )
    elif roi_pct > 10:
        recommendation = "MAYBE — Marginal"
        reasoning.append(
            f"Marginal ROI of {roi_pct:.0f}%. Profit depends on actually "
            f"getting a {company} {expected_grade}."
        )
    elif roi_pct > 0:
        recommendation = "PROBABLY NOT — Thin margins"
        reasoning.append(
            f"Very thin ROI of {roi_pct:.0f}%. After eBay fees (~13%) and "
            f"shipping, you'd likely break even or lose money."
        )
    else:
        recommendation = "NO — Not worth grading"
        reasoning.append(
            f"Negative ROI of {roi_pct:.0f}%. Grading costs more than "
            f"the price uplift. Sell raw instead."
        )

    # Grade probability warning
    if expected_grade == "10":
        reasoning.append(
            "Note: Only ~2-5% of modern cards grade PSA 10. "
            "A PSA 9 typically sells for 30-60% less than a 10."
        )

    # Raw card value threshold
    if raw_avg < 5:
        reasoning.append(
            f"Raw card is only ${raw_avg:.2f} — generally not worth grading "
            f"cards under $20 raw unless they have significant sentimental value."
        )
    elif raw_avg < 20:
        reasoning.append(
            f"Raw card at ${raw_avg:.2f} is on the low side for grading. "
            f"Consider batch submissions for cost efficiency."
        )

    # Volume check
    if raw_result.num_results < 5:
        reasoning.append(
            "Low sales volume for raw cards — pricing may be unreliable."
        )
    if graded_result.num_results < 5:
        reasoning.append(
            "Low sales volume for graded cards — pricing may be unreliable."
        )

    # Fee reminder
    if net_profit > 0:
        after_fees = net_profit * 0.87  # ~13% eBay + PayPal fees
        reasoning.append(
            f"After marketplace fees (~13%): estimated net profit ~${after_fees:.2f}"
        )

    return recommendation, reasoning
