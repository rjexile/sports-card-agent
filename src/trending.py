"""
Trending players module.
Identifies NBA players with breakout performances whose card values
are likely to be rising or about to rise. Uses player stats to find
performers who are exceeding expectations.
"""

from dataclasses import dataclass, field
from .player_stats import PlayerStatsClient, PlayerInfo, SeasonStats


@dataclass
class TrendingPlayer:
    player: PlayerInfo
    stats: SeasonStats
    trend_score: float  # 0-100, higher = more breakout
    reasons: list[str] = field(default_factory=list)
    card_tip: str = ""

    def format(self) -> str:
        lines = [
            f"  {self.player.full_name} ({self.player.team}) — Score: {self.trend_score:.0f}/100",
            f"    {self.stats.pts:.1f} PPG | {self.stats.reb:.1f} RPG | {self.stats.ast:.1f} APG | {self.stats.games_played} GP",
        ]
        for r in self.reasons:
            lines.append(f"    + {r}")
        if self.card_tip:
            lines.append(f"    Card tip: {self.card_tip}")
        return "\n".join(lines)


# Players to monitor for breakout potential (curated watchlist)
# These are young or ascending players whose cards see price movement
WATCHLIST = [
    "Victor Wembanyama",
    "Chet Holmgren",
    "Anthony Edwards",
    "Luka Doncic",
    "Jayson Tatum",
    "Tyrese Haliburton",
    "Paolo Banchero",
    "Jalen Brunson",
    "Shai Gilgeous-Alexander",
    "Tyrese Maxey",
    "Scottie Barnes",
    "Evan Mobley",
    "LaMelo Ball",
    "Ja Morant",
    "Zion Williamson",
    "Jaime Jaquez Jr",
    "Brandon Miller",
    "Amen Thompson",
    "Dereck Lively II",
    "Cason Wallace",
]


async def get_trending_players(
    stats_client: PlayerStatsClient,
    limit: int = 10,
) -> list[TrendingPlayer]:
    """
    Scan the watchlist for players with breakout stats.
    Returns players ranked by trend score.
    """
    trending = []

    for name in WATCHLIST:
        report = await stats_client.get_player_report(name)
        if not report or not report.current_stats:
            continue

        score, reasons, tip = _score_breakout(report.player, report.current_stats)

        if score > 20:  # Only include players with meaningful trend
            trending.append(
                TrendingPlayer(
                    player=report.player,
                    stats=report.current_stats,
                    trend_score=score,
                    reasons=reasons,
                    card_tip=tip,
                )
            )

    # Sort by trend score descending
    trending.sort(key=lambda x: x.trend_score, reverse=True)
    return trending[:limit]


def _score_breakout(
    player: PlayerInfo, stats: SeasonStats
) -> tuple[float, list[str], str]:
    """Score a player's breakout potential (0-100)."""
    score = 0.0
    reasons = []
    tips = []

    # --- Scoring thresholds ---
    if stats.pts >= 28:
        score += 30
        reasons.append(f"Elite scoring: {stats.pts:.1f} PPG")
        tips.append("Premium on all rookie and numbered cards")
    elif stats.pts >= 22:
        score += 20
        reasons.append(f"Strong scoring: {stats.pts:.1f} PPG")
    elif stats.pts >= 16:
        score += 10
        reasons.append(f"Solid scoring: {stats.pts:.1f} PPG")

    # All-around game
    if stats.reb >= 8 and stats.ast >= 5:
        score += 15
        reasons.append("Versatile stat line — collectors love this")
        tips.append("Look for cards highlighting versatility")
    elif stats.reb >= 10:
        score += 10
        reasons.append(f"Dominant rebounder: {stats.reb:.1f} RPG")
    elif stats.ast >= 8:
        score += 10
        reasons.append(f"Elite playmaker: {stats.ast:.1f} APG")

    # Efficiency
    if stats.fg_pct >= 0.55:
        score += 10
        reasons.append(f"Outstanding efficiency: {stats.fg_pct:.1%} FG")
    elif stats.fg_pct >= 0.48:
        score += 5

    # Shot blocking / defensive impact
    if stats.blk >= 2.0:
        score += 10
        reasons.append(f"Elite rim protector: {stats.blk:.1f} BPG")
    if stats.stl >= 1.5:
        score += 5
        reasons.append(f"Ball hawk: {stats.stl:.1f} SPG")

    # Three-point shooting
    if stats.fg3_pct >= 0.38 and stats.pts >= 15:
        score += 10
        reasons.append(f"Dangerous shooter: {stats.fg3_pct:.1%} from 3")
        tips.append("Shooting parallels and inserts in high demand")

    # Games played (health is a factor)
    if stats.games_played >= 60:
        score += 10
        reasons.append("Durable — played 60+ games")
    elif stats.games_played < 25:
        score -= 10
        reasons.append(f"Injury risk — only {stats.games_played} games")
        tips.append("Buy-low opportunity if player returns healthy")

    # Combine the best tip
    card_tip = tips[0] if tips else "Monitor for price movement as stats accumulate"

    return min(100, score), reasons, card_tip


def format_trending_report(trending: list[TrendingPlayer]) -> str:
    """Format the trending players into a readable report."""
    if not trending:
        return "No trending players found. Try again later or expand the watchlist."

    lines = [
        "=== Trending NBA Players — Card Market Watch ===",
        f"Found {len(trending)} players with breakout potential:\n",
    ]

    for i, tp in enumerate(trending, 1):
        lines.append(f"{i}. {tp.format()}")
        lines.append("")

    lines.append("--- How to Use This ---")
    lines.append("  * High-scoring players (70+): Cards likely already rising. Buy now or monitor.")
    lines.append("  * Mid-range (40-70): Emerging — good buy-low window.")
    lines.append("  * Lower (20-40): On the radar — watch for a catalyst game.")

    return "\n".join(lines)
