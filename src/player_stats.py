"""
Player stats client using the Ball Don't Lie API.
Free tier: 5 requests/minute, no API key required for basic endpoints.
Covers NBA with player search and season averages.
"""

import httpx
from dataclasses import dataclass, field


BASE_URL = "https://api.balldontlie.io/v1"


@dataclass
class PlayerInfo:
    id: int
    first_name: str
    last_name: str
    position: str
    team: str
    conference: str

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


@dataclass
class SeasonStats:
    season: int
    games_played: int
    pts: float
    reb: float
    ast: float
    stl: float
    blk: float
    fg_pct: float
    fg3_pct: float
    ft_pct: float
    turnover: float
    min: str

    def summary(self) -> str:
        return (
            f"  {self.season}-{self.season + 1} Season ({self.games_played} GP):\n"
            f"    PPG: {self.pts:.1f} | RPG: {self.reb:.1f} | APG: {self.ast:.1f}\n"
            f"    STL: {self.stl:.1f} | BLK: {self.blk:.1f} | TO: {self.turnover:.1f}\n"
            f"    FG%: {self.fg_pct:.1%} | 3P%: {self.fg3_pct:.1%} | FT%: {self.ft_pct:.1%}\n"
            f"    MPG: {self.min}"
        )


@dataclass
class PlayerReport:
    player: PlayerInfo
    current_stats: SeasonStats | None = None
    card_insight: str = ""

    def summary(self) -> str:
        lines = [
            f"=== {self.player.full_name} ===",
            f"Position: {self.player.position} | Team: {self.player.team} | Conference: {self.player.conference}",
        ]
        if self.current_stats:
            lines.append(f"\nCurrent Season Stats:")
            lines.append(self.current_stats.summary())
        if self.card_insight:
            lines.append(f"\nCard Market Insight:")
            lines.append(f"  {self.card_insight}")
        return "\n".join(lines)


class PlayerStatsClient:
    """Client for Ball Don't Lie NBA stats API."""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        headers = {}
        if api_key:
            headers["Authorization"] = api_key
        self._http = httpx.AsyncClient(
            base_url=BASE_URL, timeout=15, headers=headers
        )

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    async def search_player(self, name: str) -> list[PlayerInfo]:
        """Search for NBA players by name."""
        resp = await self._http.get("/players", params={"search": name})
        resp.raise_for_status()
        data = resp.json()

        players = []
        for p in data.get("data", []):
            team = p.get("team", {})
            players.append(
                PlayerInfo(
                    id=p["id"],
                    first_name=p.get("first_name", ""),
                    last_name=p.get("last_name", ""),
                    position=p.get("position", "N/A"),
                    team=team.get("full_name", "Unknown"),
                    conference=team.get("conference", ""),
                )
            )
        return players

    async def get_season_averages(
        self, player_id: int, season: int = 2025
    ) -> SeasonStats | None:
        """Get a player's season averages."""
        resp = await self._http.get(
            "/season_averages",
            params={"season": season, "player_ids[]": player_id},
        )
        resp.raise_for_status()
        data = resp.json()

        rows = data.get("data", [])
        if not rows:
            return None

        s = rows[0]
        return SeasonStats(
            season=season,
            games_played=s.get("games_played", 0),
            pts=s.get("pts", 0),
            reb=s.get("reb", 0),
            ast=s.get("ast", 0),
            stl=s.get("stl", 0),
            blk=s.get("blk", 0),
            fg_pct=s.get("fg_pct", 0),
            fg3_pct=s.get("fg3_pct", 0),
            ft_pct=s.get("ft_pct", 0),
            turnover=s.get("turnover", 0),
            min=s.get("min", "0"),
        )

    async def get_player_report(self, name: str) -> PlayerReport | None:
        """Search for a player and get their current stats."""
        if not self.is_configured:
            return _mock_player_report(name)

        players = await self.search_player(name)
        if not players:
            return None

        player = players[0]
        season_stats = await self.get_season_averages(player.id)

        # Generate card market insight based on performance
        insight = _generate_card_insight(player, season_stats)

        return PlayerReport(
            player=player,
            current_stats=season_stats,
            card_insight=insight,
        )

    async def close(self):
        await self._http.aclose()


def _generate_card_insight(player: PlayerInfo, stats: SeasonStats | None) -> str:
    """Generate a card market insight based on player performance."""
    if not stats:
        return "No current season data available. Check if player is active."

    insights = []

    # Scoring breakout
    if stats.pts >= 25:
        insights.append(
            f"Elite scorer ({stats.pts:.1f} PPG) — rookie and key cards "
            f"likely command premium prices."
        )
    elif stats.pts >= 18:
        insights.append(
            f"Strong scoring ({stats.pts:.1f} PPG) — solid demand for cards."
        )
    elif stats.pts < 10 and stats.games_played > 20:
        insights.append(
            f"Below-average scoring ({stats.pts:.1f} PPG) — card values "
            f"may be declining unless player is young with upside."
        )

    # All-around game
    if stats.ast >= 7 and stats.reb >= 7:
        insights.append("Triple-double threat — these players' cards trend higher.")
    elif stats.ast >= 7:
        insights.append("Elite playmaker — look for assists leader parallels.")
    elif stats.reb >= 10:
        insights.append("Dominant rebounder — niche collector appeal.")

    # Efficiency
    if stats.fg_pct >= 0.50 and stats.games_played > 20:
        insights.append(f"High efficiency ({stats.fg_pct:.1%} FG) — a good sign for sustained value.")

    # Games played (injury concern)
    if stats.games_played < 15 and stats.pts > 0:
        insights.append(
            f"Only {stats.games_played} games played — possible injury concern. "
            f"Cards may be discounted; could be a buy-low opportunity if healthy."
        )

    if not insights:
        insights.append("Average performance — card values likely stable.")

    return " ".join(insights)


def _mock_player_report(name: str) -> PlayerReport | None:
    """Return mock data when Ball Don't Lie API isn't configured."""
    import hashlib

    seed = int(hashlib.md5(name.lower().encode()).hexdigest()[:8], 16)
    import random
    rng = random.Random(seed)

    # Common NBA players for realistic mock data
    mock_players = {
        "lebron": ("LeBron", "James", "SF", "Los Angeles Lakers", "Western"),
        "wembanyama": ("Victor", "Wembanyama", "C", "San Antonio Spurs", "Western"),
        "luka": ("Luka", "Doncic", "PG", "Los Angeles Lakers", "Western"),
        "giannis": ("Giannis", "Antetokounmpo", "PF", "Milwaukee Bucks", "Eastern"),
        "curry": ("Stephen", "Curry", "PG", "Golden State Warriors", "Western"),
        "jokic": ("Nikola", "Jokic", "C", "Denver Nuggets", "Western"),
        "tatum": ("Jayson", "Tatum", "SF", "Boston Celtics", "Eastern"),
    }

    # Try to match a known player
    name_lower = name.lower()
    matched = None
    for key, val in mock_players.items():
        if key in name_lower or name_lower in key:
            matched = val
            break

    if matched:
        first, last, pos, team, conf = matched
    else:
        first = name.split()[0].title() if " " in name else name.title()
        last = name.split()[-1].title() if " " in name else "Player"
        pos = rng.choice(["PG", "SG", "SF", "PF", "C"])
        team = "Unknown Team"
        conf = rng.choice(["Eastern", "Western"])

    player = PlayerInfo(
        id=seed % 10000,
        first_name=first,
        last_name=last,
        position=pos,
        team=team,
        conference=conf,
    )

    mock_stats = SeasonStats(
        season=2025,
        games_played=rng.randint(30, 70),
        pts=round(rng.uniform(8, 32), 1),
        reb=round(rng.uniform(2, 12), 1),
        ast=round(rng.uniform(1, 10), 1),
        stl=round(rng.uniform(0.3, 2.0), 1),
        blk=round(rng.uniform(0.1, 2.5), 1),
        fg_pct=round(rng.uniform(0.38, 0.58), 3),
        fg3_pct=round(rng.uniform(0.28, 0.42), 3),
        ft_pct=round(rng.uniform(0.65, 0.92), 3),
        turnover=round(rng.uniform(1.0, 4.0), 1),
        min=str(rng.randint(20, 38)),
    )

    insight = _generate_card_insight(player, mock_stats)
    insight += " [MOCK DATA — configure BALLDONTLIE_API_KEY in .env for live stats]"

    return PlayerReport(
        player=player,
        current_stats=mock_stats,
        card_insight=insight,
    )
