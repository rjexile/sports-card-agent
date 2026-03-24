"""
Sports card investment advisor.
Combines player performance data with market pricing to generate
buy/sell/hold recommendations.
"""

from dataclasses import dataclass, field
from .ebay_client import EbayClient
from .analysis import analyze_market, TrendAnalysis


@dataclass
class InvestmentAdvice:
    card_query: str
    player_name: str
    action: str  # "BUY", "SELL", "HOLD", "AVOID"
    confidence: str  # "high", "medium", "low"
    summary: str
    price_data: TrendAnalysis | None = None
    player_data: object = None  # PlayerReport from any sport
    factors: list[str] = field(default_factory=list)

    def format(self) -> str:
        emoji = {"BUY": "BUY", "SELL": "SELL", "HOLD": "HOLD", "AVOID": "AVOID"}
        lines = [
            f"=== Investment Advice: '{self.card_query}' ===",
            f"",
            f"Action:      {emoji.get(self.action, self.action)} ({self.confidence} confidence)",
            f"Summary:     {self.summary}",
        ]

        if self.price_data:
            lines.append(f"")
            lines.append(f"--- Market Data ---")
            lines.append(f"  Sold Avg:    ${self.price_data.sold_avg:.2f}")
            lines.append(f"  Active Avg:  ${self.price_data.active_avg:.2f}")
            lines.append(f"  Trend:       {self.price_data.price_direction.upper()}")
            lines.append(f"  Spread:      {self.price_data.spread_pct:+.1f}%")

        if self.player_data and hasattr(self.player_data, 'current_stats') and self.player_data.current_stats:
            s = self.player_data.current_stats
            p = self.player_data.player
            lines.append(f"")
            lines.append(f"--- Player Performance ---")
            lines.append(f"  {p.full_name} ({p.team})")

            # NBA
            if hasattr(s, 'pts'):
                lines.append(f"  {s.pts:.1f} PPG | {s.reb:.1f} RPG | {s.ast:.1f} APG")
            # NFL
            elif hasattr(s, 'pass_touchdowns'):
                if hasattr(s, 'summary'):
                    lines.append(s.summary(getattr(p, 'position', '')))
                else:
                    lines.append(f"  {s.pass_yards} PASS YDS | {s.pass_touchdowns} TD")
            # MLB
            elif hasattr(s, 'home_runs'):
                if getattr(s, 'is_pitcher', False):
                    lines.append(f"  {s.era:.2f} ERA | {s.strikeouts_pitching} K | {s.wins}W-{s.losses}L")
                else:
                    lines.append(f"  .{int(s.batting_avg * 1000):03d} AVG | {s.home_runs} HR | {s.rbis} RBI")

            lines.append(f"  Games Played: {s.games_played}")

        if self.factors:
            lines.append(f"")
            lines.append(f"--- Key Factors ---")
            for f in self.factors:
                lines.append(f"  * {f}")

        return "\n".join(lines)


async def get_investment_advice(
    ebay: EbayClient,
    stats_client,
    card_query: str,
    player_name: str = "",
) -> InvestmentAdvice:
    """
    Generate buy/sell/hold advice by combining market data with player stats.
    """
    # Get market data
    market = await analyze_market(ebay, card_query)

    # Try to get player stats if a player name is available
    player_report = None
    if player_name:
        player_report = await stats_client.get_player_report(player_name)

    # Score the investment
    score, factors = _score_investment(market, player_report)

    # Determine action and confidence
    action, confidence, summary = _determine_action(score, factors, market, player_report)

    return InvestmentAdvice(
        card_query=card_query,
        player_name=player_name,
        action=action,
        confidence=confidence,
        summary=summary,
        price_data=market,
        player_data=player_report,
        factors=factors,
    )


def _score_investment(
    market: TrendAnalysis,
    player,
) -> tuple[float, list[str]]:
    """
    Score the investment on a -100 to +100 scale.
    Positive = buy signal, Negative = sell signal.
    """
    score = 0.0
    factors = []

    # --- Market factors ---

    # Price direction
    if market.price_direction == "rising":
        score += 20
        factors.append("Price trend is RISING — positive momentum")
    elif market.price_direction == "falling":
        score -= 25
        factors.append("Price trend is FALLING — declining demand")
    elif market.price_direction == "stable":
        score += 5
        factors.append("Prices are STABLE — predictable market")

    # Spread (asks vs sold)
    if market.spread_pct < -10:
        score += 25
        factors.append(
            f"Active listings are {abs(market.spread_pct):.0f}% BELOW sold prices — "
            f"buying opportunity"
        )
    elif market.spread_pct > 30:
        score -= 15
        factors.append(
            f"Sellers asking {market.spread_pct:.0f}% above sold prices — "
            f"market may be overpriced"
        )

    # Arbitrage opportunities
    if market.arbitrage_opportunities:
        best = market.arbitrage_opportunities[0]
        score += min(20, best.profit_margin / 5)
        factors.append(
            f"Found {len(market.arbitrage_opportunities)} arbitrage opportunities "
            f"(best: {best.profit_margin:.0f}% margin)"
        )

    # Volume
    if market.sold_data:
        if market.sold_data.num_results >= 15:
            score += 10
            factors.append("High sales volume — liquid market")
        elif market.sold_data.num_results < 5:
            score -= 10
            factors.append("Very low sales volume — illiquid, risky")

    # --- Player performance factors ---
    if player and player.current_stats:
        s = player.current_stats
        gp = getattr(s, 'games_played', 0)

        # NBA stats
        if hasattr(s, 'pts'):
            if s.pts >= 25:
                score += 20
                factors.append(f"Elite scorer ({s.pts:.1f} PPG) — high card demand")
            elif s.pts >= 18:
                score += 10
                factors.append(f"Strong scorer ({s.pts:.1f} PPG) — solid demand")
            elif s.pts < 10 and gp > 20:
                score -= 15
                factors.append(f"Low scoring ({s.pts:.1f} PPG) — declining interest")

            if hasattr(s, 'ast') and hasattr(s, 'reb'):
                if s.ast >= 7 and s.reb >= 7:
                    score += 15
                    factors.append("Triple-double threat — premium card appeal")

            if hasattr(s, 'fg_pct') and s.fg_pct >= 0.50:
                score += 5
                factors.append(f"High efficiency ({s.fg_pct:.1%} FG) — sustainable production")

            if s.pts >= 20 and gp >= 40:
                score += 10
                factors.append("Consistent high performer — strong long-term hold")

        # NFL stats
        if hasattr(s, 'pass_touchdowns'):
            if s.pass_touchdowns >= 30:
                score += 25
                factors.append(f"Elite QB ({s.pass_touchdowns} TD) — premium card demand")
            elif s.pass_touchdowns >= 20:
                score += 15
                factors.append(f"Strong QB ({s.pass_touchdowns} TD) — solid demand")
            if hasattr(s, 'rush_yards') and s.rush_yards >= 1000:
                score += 15
                factors.append(f"1,000+ rushing yards — strong RB card appeal")
            if hasattr(s, 'receiving_yards') and s.receiving_yards >= 1200:
                score += 15
                factors.append(f"Elite receiver ({s.receiving_yards} YDS) — premium cards")

        # MLB stats
        if hasattr(s, 'home_runs') and not hasattr(s, 'pts'):
            if s.home_runs >= 40:
                score += 25
                factors.append(f"Power elite ({s.home_runs} HR) — major card demand")
            elif s.home_runs >= 25:
                score += 15
                factors.append(f"Strong power ({s.home_runs} HR) — solid demand")
            if hasattr(s, 'batting_avg') and s.batting_avg >= 0.300:
                score += 15
                factors.append(f"Elite hitter (.{int(s.batting_avg * 1000):03d}) — high premium")
            if hasattr(s, 'era') and s.era > 0 and s.era <= 2.50:
                score += 20
                factors.append(f"Ace pitcher ({s.era:.2f} ERA) — premium card demand")

        # Injury concern (all sports)
        if gp < 20 and gp > 0:
            score -= 10
            factors.append(
                f"Only {gp} games played — injury risk may depress values"
            )

    return score, factors


def _determine_action(
    score: float,
    factors: list[str],
    market: TrendAnalysis,
    player,
) -> tuple[str, str, str]:
    """Convert score to action, confidence, and summary."""

    # Determine confidence based on data availability
    has_player = player is not None and player.current_stats is not None
    has_good_market = (
        market.sold_data is not None and market.sold_data.num_results >= 5
    )

    if has_player and has_good_market:
        confidence = "high"
    elif has_good_market:
        confidence = "medium"
    else:
        confidence = "low"

    # Determine action
    if score >= 30:
        action = "BUY"
        summary = (
            "Strong buy signal. Market conditions and player performance "
            "both favor this card appreciating in value."
        )
    elif score >= 10:
        action = "BUY"
        summary = (
            "Moderate buy signal. Positive indicators outweigh negatives, "
            "but consider timing your purchase for a dip."
        )
    elif score >= -10:
        action = "HOLD"
        summary = (
            "Mixed signals. If you own it, hold. If you don't, "
            "wait for a clearer trend before buying."
        )
    elif score >= -25:
        action = "SELL"
        summary = (
            "Sell signal. Declining indicators suggest this card may "
            "lose value. Consider selling before further drops."
        )
    else:
        action = "AVOID"
        summary = (
            "Strong avoid. Multiple negative signals. If you own this card, "
            "sell now. Do not buy at current prices."
        )

    return action, confidence, summary
