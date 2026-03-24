"""
Price trend analysis and arbitrage detection for sports cards.
Compares active vs sold prices, identifies undervalued listings,
and provides market trend insights.
"""

from dataclasses import dataclass, field
from .ebay_client import PriceResult, EbayClient


@dataclass
class ArbitrageOpportunity:
    card_title: str
    buy_price: float
    estimated_value: float
    profit_margin: float  # percentage
    url: str = ""
    reasoning: str = ""


@dataclass
class TrendAnalysis:
    query: str
    sold_avg: float
    active_avg: float
    price_direction: str  # "rising", "falling", "stable"
    spread_pct: float  # difference between active asks and sold prices
    arbitrage_opportunities: list[ArbitrageOpportunity] = field(default_factory=list)
    insights: list[str] = field(default_factory=list)
    sold_data: PriceResult | None = None
    active_data: PriceResult | None = None

    def summary(self) -> str:
        lines = [
            f"=== Market Analysis: '{self.query}' ===",
            f"",
            f"Sold Price Average:   ${self.sold_avg:.2f}",
            f"Active Ask Average:   ${self.active_avg:.2f}",
            f"Market Spread:        {self.spread_pct:+.1f}%",
            f"Price Direction:      {self.price_direction.upper()}",
        ]

        if self.insights:
            lines.append(f"\n--- Insights ---")
            for insight in self.insights:
                lines.append(f"  * {insight}")

        if self.arbitrage_opportunities:
            lines.append(f"\n--- Arbitrage Opportunities ({len(self.arbitrage_opportunities)} found) ---")
            for opp in self.arbitrage_opportunities[:5]:
                lines.append(
                    f"  > {opp.card_title}\n"
                    f"    Buy: ${opp.buy_price:.2f} | Est. Value: ${opp.estimated_value:.2f} | "
                    f"Margin: {opp.profit_margin:.1f}%\n"
                    f"    {opp.reasoning}"
                )
                if opp.url:
                    lines.append(f"    Link: {opp.url}")

        return "\n".join(lines)


async def analyze_market(client: EbayClient, query: str) -> TrendAnalysis:
    """
    Full market analysis: compares sold vs active prices,
    detects arbitrage, and generates insights.
    """
    # Fetch both sold and active data
    sold = await client.search_sold(query, limit=20)
    active = await client.search_active(query, limit=20)

    # Calculate spread (how much sellers are asking vs what buyers pay)
    if sold.avg_price > 0 and active.avg_price > 0:
        spread_pct = ((active.avg_price - sold.avg_price) / sold.avg_price) * 100
    else:
        spread_pct = 0.0

    # Determine price direction based on sold price distribution
    direction = _detect_direction(sold)

    # Find arbitrage: active listings priced below sold median
    opportunities = _find_arbitrage(active, sold)

    # Generate insights
    insights = _generate_insights(sold, active, spread_pct, direction, opportunities)

    return TrendAnalysis(
        query=query,
        sold_avg=sold.avg_price,
        active_avg=active.avg_price,
        price_direction=direction,
        spread_pct=spread_pct,
        arbitrage_opportunities=opportunities,
        insights=insights,
        sold_data=sold,
        active_data=active,
    )


def _detect_direction(sold: PriceResult) -> str:
    """
    Detect price direction from sold listings.
    Compares lower half vs upper half of recent sales.
    """
    if sold.num_results < 4:
        return "insufficient data"

    prices = sorted([l.price for l in sold.listings if l.price > 0])
    if len(prices) < 4:
        return "insufficient data"

    mid = len(prices) // 2
    lower_avg = sum(prices[:mid]) / mid
    upper_avg = sum(prices[mid:]) / (len(prices) - mid)

    # With sold data sorted by recency, this gives a rough trend
    ratio = upper_avg / lower_avg if lower_avg > 0 else 1
    if ratio > 1.15:
        return "rising"
    elif ratio < 0.85:
        return "falling"
    return "stable"


def _find_arbitrage(
    active: PriceResult, sold: PriceResult
) -> list[ArbitrageOpportunity]:
    """Find active listings priced significantly below sold median."""
    if sold.median_price <= 0 or not active.listings:
        return []

    opportunities = []
    threshold = sold.median_price * 0.75  # 25% below sold median

    for listing in active.listings:
        if 0 < listing.price < threshold:
            margin = ((sold.median_price - listing.price) / listing.price) * 100

            # Only flag if margin is meaningful (covers fees + shipping)
            if margin > 20:
                opportunities.append(
                    ArbitrageOpportunity(
                        card_title=listing.title,
                        buy_price=listing.price,
                        estimated_value=sold.median_price,
                        profit_margin=margin,
                        url=listing.url,
                        reasoning=(
                            f"Listed {margin:.0f}% below sold median. "
                            f"Sold median is ${sold.median_price:.2f}."
                        ),
                    )
                )

    # Sort by margin descending
    opportunities.sort(key=lambda x: x.profit_margin, reverse=True)
    return opportunities[:10]


def _generate_insights(
    sold: PriceResult,
    active: PriceResult,
    spread_pct: float,
    direction: str,
    opportunities: list[ArbitrageOpportunity],
) -> list[str]:
    """Generate human-readable market insights."""
    insights = []

    # Spread insight
    if spread_pct > 30:
        insights.append(
            f"Sellers are asking {spread_pct:.0f}% above recent sold prices -- "
            f"the market may be overpriced. Be patient for deals."
        )
    elif spread_pct < -10:
        insights.append(
            f"Active listings are {abs(spread_pct):.0f}% BELOW recent sold prices -- "
            f"this could be a buying opportunity."
        )
    elif sold.num_results > 0:
        insights.append(
            f"Market spread is {spread_pct:+.0f}% -- fairly priced relative to recent sales."
        )

    # Direction insight
    if direction == "rising":
        insights.append("Price trend is RISING based on recent sales distribution.")
    elif direction == "falling":
        insights.append("Price trend is FALLING --consider waiting before buying.")
    elif direction == "stable":
        insights.append("Prices are STABLE --consistent market for this card.")

    # Volume insight
    if sold.num_results >= 15:
        insights.append(
            f"High sales volume ({sold.num_results} recent sales) --"
            f"liquid market, easy to buy and sell."
        )
    elif sold.num_results < 5 and sold.num_results > 0:
        insights.append(
            f"Low sales volume ({sold.num_results} recent sales) --"
            f"illiquid market, prices may be unreliable."
        )

    # Price range insight
    if sold.high_price > 0 and sold.low_price > 0:
        range_ratio = sold.high_price / sold.low_price
        if range_ratio > 5:
            insights.append(
                f"Wide price range (${sold.low_price:.2f}-${sold.high_price:.2f}) --"
                f"condition and grading heavily affect value. Consider graded copies."
            )

    # Arbitrage insight
    if opportunities:
        best = opportunities[0]
        insights.append(
            f"Found {len(opportunities)} arbitrage opportunities. "
            f"Best: {best.profit_margin:.0f}% margin at ${best.buy_price:.2f}."
        )

    return insights
