"""
Sports Card Price Agent - MCP Server

A comprehensive MCP server for sports trading card data across all major
sports. Provides pricing, market analysis, arbitrage detection, grading ROI,
investment advice, player stats (NBA/NFL/MLB), vintage card analysis,
and trending player insights.

Tools (9 total):
  - card_price_lookup: Real-time market prices
  - card_market_analysis: Trend analysis + arbitrage detection
  - player_stats_lookup: Multi-sport player stats (NBA/NFL/MLB) with card insights
  - grading_roi_calculator: Should you grade this card?
  - card_investment_advisor: Buy/sell/hold recommendations
  - trending_players: Breakout performers whose cards are rising
  - nfl_stats_lookup: NFL player stats with card market insights
  - mlb_stats_lookup: MLB player stats with card market insights
  - vintage_card_analysis: Era-specific analysis for pre-2000 cards
"""

import os
import json
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from .ebay_client import EbayClient
from .analysis import analyze_market
from .player_stats import PlayerStatsClient
from .nfl_stats import NFLStatsClient
from .mlb_stats import MLBStatsClient
from .grading import calculate_grading_roi
from .advisor import get_investment_advice
from .trending import get_trending_players, format_trending_report
from .vintage import analyze_vintage_card

# Load environment
load_dotenv()

# Initialize MCP server
mcp = FastMCP(
    "Sports Card Price Agent",
    instructions=(
        "Comprehensive sports trading card agent with 9 tools. "
        "Real-time pricing, market analysis, arbitrage detection, grading ROI, "
        "investment advice, player stats (NBA/NFL/MLB), vintage card analysis, "
        "and trending player alerts. Covers baseball, basketball, football, "
        "hockey, and soccer cards from all major manufacturers (Topps, Panini, "
        "Upper Deck, Bowman, Fleer, etc.)."
    ),
)

# Initialize clients
ebay = EbayClient(
    app_id=os.getenv("EBAY_APP_ID", ""),
    cert_id=os.getenv("EBAY_CERT_ID", ""),
)
api_key = os.getenv("BALLDONTLIE_API_KEY", "")
nba_stats = PlayerStatsClient(api_key=api_key)
nfl_stats = NFLStatsClient(api_key=api_key)
mlb_stats = MLBStatsClient(api_key=api_key)


# ── Pricing Tools ──────────────────────────────────────────────────────

@mcp.tool()
async def card_price_lookup(
    query: str,
    listing_type: str = "sold",
    limit: int = 15,
) -> str:
    """
    Look up current market prices for a sports trading card.

    Args:
        query: Card search query, e.g. "2023 Topps Chrome Victor Wembanyama rookie"
                or "Michael Jordan Fleer rookie PSA 9". Include as much detail as
                possible: year, brand/set, player name, card number, parallel,
                and grading info.
        listing_type: "sold" for recent sold prices (true market value) or
                      "active" for current asking prices. Default: "sold"
        limit: Number of results to return (1-50). Default: 15

    Returns:
        Price summary with average, median, low, high and individual listings.
    """
    limit = max(1, min(50, limit))

    if listing_type == "active":
        result = await ebay.search_active(query, limit=limit)
    else:
        result = await ebay.search_sold(query, limit=limit)

    output = [result.summary(), ""]

    if result.listings:
        output.append(f"--- Top {min(5, len(result.listings))} Listings ---")
        for listing in result.listings[:5]:
            status = "SOLD" if listing.sold else "ACTIVE"
            output.append(
                f"  [{status}] ${listing.price:.2f} - {listing.title}"
            )
            if listing.condition != "Unknown":
                output.append(f"           Condition: {listing.condition}")
            if listing.url:
                output.append(f"           {listing.url}")
            output.append("")

    if not ebay.is_configured:
        output.append(
            "\n[!] Using mock data. Configure EBAY_APP_ID and EBAY_CERT_ID "
            "in .env for live eBay pricing."
        )

    return "\n".join(output)


@mcp.tool()
async def card_market_analysis(query: str) -> str:
    """
    Full market analysis for a sports card: price trends, buy/sell spread,
    and arbitrage opportunities where cards are listed below market value.

    Args:
        query: Card search query, e.g. "2024 Panini Prizm Caitlin Clark rookie"
                or "Ken Griffey Jr 1989 Upper Deck rookie". Include year, brand,
                player name, and any grading info for best results.

    Returns:
        Comprehensive market analysis including:
        - Average sold price vs average asking price
        - Price direction (rising/falling/stable)
        - Market spread percentage
        - Arbitrage opportunities (underpriced active listings)
        - Actionable buying/selling insights
    """
    analysis = await analyze_market(ebay, query)

    output = [analysis.summary()]

    if not ebay.is_configured:
        output.append(
            "\n[!] Using mock data. Configure EBAY_APP_ID and EBAY_CERT_ID "
            "in .env for live eBay pricing."
        )

    return "\n".join(output)


# ── Player Stats Tools ─────────────────────────────────────────────────

@mcp.tool()
async def player_stats_lookup(
    player_name: str,
    sport: str = "nba",
    season: int = 2025,
) -> str:
    """
    Look up player stats for NBA, NFL, or MLB and get card market insights
    based on their performance.

    Args:
        player_name: Player name, e.g. "LeBron James", "Patrick Mahomes",
                     "Shohei Ohtani". Partial names work.
        sport: "nba", "nfl", or "mlb". Default: "nba"
        season: Season year (e.g. 2025). Default: 2025

    Returns:
        Player bio, current season stats, and card market insight
        based on their performance level.
    """
    sport = sport.lower().strip()

    if sport == "nfl":
        report = await nfl_stats.get_player_report(player_name)
        if not report:
            return f"No NFL player found matching '{player_name}'."
        return report.summary()

    elif sport == "mlb":
        report = await mlb_stats.get_player_report(player_name)
        if not report:
            return f"No MLB player found matching '{player_name}'."
        return report.summary()

    else:  # nba (default)
        report = await nba_stats.get_player_report(player_name)
        if not report:
            return f"No NBA player found matching '{player_name}'."

        if season != 2025 and report.player:
            from .player_stats import _generate_card_insight
            season_data = await nba_stats.get_season_averages(report.player.id, season)
            if season_data:
                report.current_stats = season_data
                report.card_insight = _generate_card_insight(report.player, season_data)

        return report.summary()


@mcp.tool()
async def nfl_stats_lookup(
    player_name: str,
    season: int = 2025,
) -> str:
    """
    Look up NFL player stats and get card market insights. Covers passing,
    rushing, receiving, and defensive stats.

    Args:
        player_name: NFL player name, e.g. "Patrick Mahomes", "Josh Allen",
                     "Justin Jefferson", "Micah Parsons". Partial names work.
        season: NFL season year (e.g. 2025). Default: 2025

    Returns:
        Player bio, season stats (passing/rushing/receiving/defense),
        and card market insight based on performance.
    """
    report = await nfl_stats.get_player_report(player_name)
    if not report:
        return f"No NFL player found matching '{player_name}'."
    return report.summary()


@mcp.tool()
async def mlb_stats_lookup(
    player_name: str,
    season: int = 2025,
) -> str:
    """
    Look up MLB player stats and get card market insights. Covers batting
    stats (AVG, HR, RBI, OPS) and pitching stats (ERA, K, WHIP, W-L).

    Args:
        player_name: MLB player name, e.g. "Shohei Ohtani", "Aaron Judge",
                     "Gerrit Cole", "Paul Skenes". Partial names work.
        season: MLB season year (e.g. 2025). Default: 2025

    Returns:
        Player bio, season stats (batting or pitching),
        and card market insight based on performance.
    """
    report = await mlb_stats.get_player_report(player_name)
    if not report:
        return f"No MLB player found matching '{player_name}'."
    return report.summary()


# ── Analysis Tools ─────────────────────────────────────────────────────

@mcp.tool()
async def grading_roi_calculator(
    card_query: str,
    grading_company: str = "PSA",
    expected_grade: str = "10",
) -> str:
    """
    Calculate whether it's worth paying to professionally grade a sports card.
    Compares raw card value vs graded card value, factoring in grading costs,
    turnaround time, and marketplace fees.

    Args:
        card_query: Card description, e.g. "2023 Topps Chrome Wembanyama rookie"
                    or "1986 Fleer Michael Jordan". Do NOT include grading info.
        grading_company: "PSA", "BGS", or "SGC". Default: "PSA"
        expected_grade: Expected grade if submitted, e.g. "10", "9", "8".
                       Default: "10"

    Returns:
        Detailed ROI analysis including raw vs graded prices, grading cost,
        net profit, ROI percentage, and a clear recommendation.
    """
    roi = await calculate_grading_roi(ebay, card_query, grading_company, expected_grade)

    output = [roi.summary()]

    if not ebay.is_configured:
        output.append(
            "\n[!] Using mock data. Configure EBAY_APP_ID and EBAY_CERT_ID "
            "in .env for live eBay pricing."
        )

    return "\n".join(output)


@mcp.tool()
async def card_investment_advisor(
    card_query: str,
    player_name: str = "",
    sport: str = "nba",
) -> str:
    """
    Get a buy/sell/hold recommendation for a sports card based on market
    trends and player performance data.

    Args:
        card_query: Card to evaluate, e.g. "2023 Topps Chrome Victor Wembanyama
                    rookie auto" or "Ken Griffey Jr 1989 Upper Deck rookie".
        player_name: Optional player name for stats cross-reference.
                     Improves accuracy. e.g. "Victor Wembanyama"
        sport: Sport for player stats lookup: "nba", "nfl", or "mlb".
               Default: "nba"

    Returns:
        BUY/SELL/HOLD/AVOID recommendation with confidence level,
        supporting market data, player stats, and key factors.
    """
    # Use the appropriate stats client based on sport
    sport = sport.lower().strip()
    if sport == "nfl":
        stats_client = nfl_stats
    elif sport == "mlb":
        stats_client = mlb_stats
    else:
        stats_client = nba_stats

    advice = await get_investment_advice(ebay, stats_client, card_query, player_name)
    return advice.format()


@mcp.tool()
async def trending_players(
    limit: int = 10,
) -> str:
    """
    Get a list of NBA players with breakout performances whose trading cards
    are likely rising in value. Scans a curated watchlist of young stars
    and ascending players.

    Args:
        limit: Number of trending players to return (1-20). Default: 10

    Returns:
        Ranked list of trending players with their stats, trend score,
        breakout reasons, and card buying tips.
    """
    limit = max(1, min(20, limit))
    trending = await get_trending_players(nba_stats, limit=limit)
    return format_trending_report(trending)


@mcp.tool()
async def vintage_card_analysis(card_query: str) -> str:
    """
    Specialized analysis for vintage and classic sports cards (pre-2000).
    Provides era-specific insights, condition sensitivity analysis,
    grade-based pricing, and investment outlook.

    Args:
        card_query: Vintage card description, e.g. "1952 Topps Mickey Mantle",
                    "1986 Fleer Michael Jordan rookie", "1979 O-Pee-Chee Wayne
                    Gretzky rookie", "1989 Upper Deck Ken Griffey Jr rookie".
                    Include year, brand, and player name.

    Returns:
        Era classification, set significance, condition impact analysis,
        estimated prices by grade, investment outlook, and collector tips.
    """
    analysis = await analyze_vintage_card(ebay, card_query)

    output = [analysis.summary()]

    if not ebay.is_configured:
        output.append(
            "\n[!] Using mock data. Configure EBAY_APP_ID and EBAY_CERT_ID "
            "in .env for live eBay pricing."
        )

    return "\n".join(output)


# ── Status Resource ────────────────────────────────────────────────────

@mcp.resource("config://status")
async def get_status() -> str:
    """Check if the agent is configured with live data sources."""
    status = {
        "ebay_configured": ebay.is_configured,
        "balldontlie_configured": nba_stats.is_configured,
        "data_mode": "live" if ebay.is_configured else "mock",
        "sports_covered": ["NBA", "NFL", "MLB", "Hockey", "Soccer"],
        "tools_available": [
            "card_price_lookup",
            "card_market_analysis",
            "player_stats_lookup",
            "nfl_stats_lookup",
            "mlb_stats_lookup",
            "grading_roi_calculator",
            "card_investment_advisor",
            "trending_players",
            "vintage_card_analysis",
        ],
    }
    return json.dumps(status, indent=2)


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
