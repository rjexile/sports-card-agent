"""
NFL player stats client using the Ball Don't Lie NFL API.
Same API key as NBA — covers passing, rushing, receiving, and defensive stats.
"""

import httpx
from dataclasses import dataclass, field


BASE_URL = "https://api.balldontlie.io/nfl/v1"


@dataclass
class NFLPlayerInfo:
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
class NFLSeasonStats:
    season: int
    games_played: int
    # Passing
    pass_completions: int = 0
    pass_attempts: int = 0
    pass_yards: int = 0
    pass_touchdowns: int = 0
    interceptions: int = 0
    # Rushing
    rush_attempts: int = 0
    rush_yards: int = 0
    rush_touchdowns: int = 0
    # Receiving
    receptions: int = 0
    receiving_yards: int = 0
    receiving_touchdowns: int = 0
    targets: int = 0
    # Defense
    sacks: float = 0
    tackles: int = 0
    def_interceptions: int = 0

    def summary(self, position: str) -> str:
        lines = [f"  {self.season} Season ({self.games_played} GP):"]

        if position in ("QB",) or self.pass_attempts > 50:
            comp_pct = (self.pass_completions / self.pass_attempts * 100) if self.pass_attempts > 0 else 0
            lines.append(
                f"    Passing: {self.pass_completions}/{self.pass_attempts} ({comp_pct:.1f}%) | "
                f"{self.pass_yards} YDS | {self.pass_touchdowns} TD | {self.interceptions} INT"
            )

        if position in ("RB", "QB") or self.rush_attempts > 20:
            ypc = self.rush_yards / self.rush_attempts if self.rush_attempts > 0 else 0
            lines.append(
                f"    Rushing: {self.rush_attempts} ATT | {self.rush_yards} YDS | "
                f"{ypc:.1f} YPC | {self.rush_touchdowns} TD"
            )

        if position in ("WR", "TE", "RB") or self.receptions > 10:
            ypr = self.receiving_yards / self.receptions if self.receptions > 0 else 0
            lines.append(
                f"    Receiving: {self.receptions} REC | {self.receiving_yards} YDS | "
                f"{ypr:.1f} YPR | {self.receiving_touchdowns} TD"
            )

        if position in ("DE", "DT", "LB", "CB", "S", "DB") or self.sacks > 2 or self.tackles > 20:
            lines.append(
                f"    Defense: {self.tackles} TKL | {self.sacks:.1f} SACK | "
                f"{self.def_interceptions} INT"
            )

        return "\n".join(lines)


@dataclass
class NFLPlayerReport:
    player: NFLPlayerInfo
    current_stats: NFLSeasonStats | None = None
    card_insight: str = ""

    def summary(self) -> str:
        lines = [
            f"=== {self.player.full_name} (NFL) ===",
            f"Position: {self.player.position} | Team: {self.player.team}",
        ]
        if self.current_stats:
            lines.append(f"\nCurrent Season Stats:")
            lines.append(self.current_stats.summary(self.player.position))
        if self.card_insight:
            lines.append(f"\nCard Market Insight:")
            lines.append(f"  {self.card_insight}")
        return "\n".join(lines)


class NFLStatsClient:
    """Client for Ball Don't Lie NFL stats API."""

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

    async def search_player(self, name: str) -> list[NFLPlayerInfo]:
        """Search for NFL players by name."""
        if not self.is_configured:
            return _mock_nfl_search(name)

        resp = await self._http.get("/players", params={"search": name})
        resp.raise_for_status()
        data = resp.json()

        players = []
        for p in data.get("data", []):
            team = p.get("team", {})
            players.append(
                NFLPlayerInfo(
                    id=p["id"],
                    first_name=p.get("first_name", ""),
                    last_name=p.get("last_name", ""),
                    position=p.get("position", "N/A"),
                    team=team.get("full_name", "Unknown"),
                    conference=team.get("conference", ""),
                )
            )
        return players

    async def get_season_stats(
        self, player_id: int, season: int = 2025
    ) -> NFLSeasonStats | None:
        """Get a player's season stats."""
        if not self.is_configured:
            return _mock_nfl_stats(season)

        resp = await self._http.get(
            "/season_stats",
            params={"season": season, "player_ids[]": player_id},
        )
        resp.raise_for_status()
        data = resp.json()

        rows = data.get("data", [])
        if not rows:
            return None

        s = rows[0]
        return NFLSeasonStats(
            season=season,
            games_played=s.get("games_played", 0),
            pass_completions=s.get("completions", 0),
            pass_attempts=s.get("attempts", 0),
            pass_yards=s.get("passing_yards", s.get("yards", 0)),
            pass_touchdowns=s.get("passing_touchdowns", s.get("touchdowns", 0)),
            interceptions=s.get("interceptions", 0),
            rush_attempts=s.get("rushing_attempts", 0),
            rush_yards=s.get("rushing_yards", 0),
            rush_touchdowns=s.get("rushing_touchdowns", 0),
            receptions=s.get("receptions", 0),
            receiving_yards=s.get("receiving_yards", 0),
            receiving_touchdowns=s.get("receiving_touchdowns", 0),
            targets=s.get("targets", 0),
            sacks=s.get("sacks", 0),
            tackles=s.get("tackles", 0),
            def_interceptions=s.get("defensive_interceptions", 0),
        )

    async def get_player_report(self, name: str) -> NFLPlayerReport | None:
        """Search for a player and get their current stats."""
        players = await self.search_player(name)
        if not players:
            return None

        player = players[0]
        season_stats = await self.get_season_stats(player.id)
        insight = _generate_nfl_card_insight(player, season_stats)

        return NFLPlayerReport(
            player=player,
            current_stats=season_stats,
            card_insight=insight,
        )

    async def close(self):
        await self._http.aclose()


def _generate_nfl_card_insight(player: NFLPlayerInfo, stats: NFLSeasonStats | None) -> str:
    """Generate card market insight based on NFL player performance."""
    if not stats:
        return "No current season data available."

    insights = []
    pos = player.position

    if pos == "QB":
        if stats.pass_touchdowns >= 30:
            insights.append(f"Elite QB season ({stats.pass_touchdowns} TD) — rookie and auto cards in high demand.")
        elif stats.pass_touchdowns >= 20:
            insights.append(f"Strong QB season ({stats.pass_touchdowns} TD) — solid card demand.")
        if stats.pass_yards >= 4000:
            insights.append(f"4,000+ yard passer — blue chip card candidate.")
        if stats.interceptions > stats.pass_touchdowns:
            insights.append("More INTs than TDs — card values may be declining.")

    elif pos in ("WR", "TE"):
        total_yards = stats.receiving_yards
        total_tds = stats.receiving_touchdowns
        if total_yards >= 1200:
            insights.append(f"Elite receiver ({total_yards} YDS) — premium on rookie cards.")
        elif total_yards >= 800:
            insights.append(f"Productive receiver ({total_yards} YDS) — steady demand.")
        if total_tds >= 10:
            insights.append(f"Double-digit TDs ({total_tds}) — big card market appeal.")

    elif pos == "RB":
        total_yards = stats.rush_yards + stats.receiving_yards
        total_tds = stats.rush_touchdowns + stats.receiving_touchdowns
        if total_yards >= 1500:
            insights.append(f"Workhorse back ({total_yards} total YDS) — strong card demand.")
        if total_tds >= 12:
            insights.append(f"TD machine ({total_tds} total) — highly collectible.")
        if stats.rush_yards < 500 and stats.games_played > 10:
            insights.append("Below-average rushing production — card values may be soft.")

    elif pos in ("DE", "DT", "LB", "CB", "S", "DB"):
        if stats.sacks >= 10:
            insights.append(f"Double-digit sacks ({stats.sacks:.1f}) — defensive stars have growing card appeal.")
        if stats.def_interceptions >= 5:
            insights.append(f"Ballhawk ({stats.def_interceptions} INT) — niche but valuable collector base.")

    if stats.games_played < 8:
        insights.append(f"Only {stats.games_played} games — injury concern may create a buy-low window.")

    if not insights:
        insights.append("Average production — card values likely stable.")

    if not player.team or player.team == "Unknown":
        insights.append("[MOCK DATA — configure BALLDONTLIE_API_KEY for live stats]")

    return " ".join(insights)


def _mock_nfl_search(name: str) -> list[NFLPlayerInfo]:
    """Mock NFL player search."""
    import hashlib
    import random

    seed = int(hashlib.md5(name.lower().encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)

    known = {
        "mahomes": ("Patrick", "Mahomes", "QB", "Kansas City Chiefs"),
        "allen": ("Josh", "Allen", "QB", "Buffalo Bills"),
        "henry": ("Derrick", "Henry", "RB", "Baltimore Ravens"),
        "hill": ("Tyreek", "Hill", "WR", "Miami Dolphins"),
        "kelce": ("Travis", "Kelce", "TE", "Kansas City Chiefs"),
        "jefferson": ("Justin", "Jefferson", "WR", "Minnesota Vikings"),
        "parsons": ("Micah", "Parsons", "LB", "Dallas Cowboys"),
        "burrow": ("Joe", "Burrow", "QB", "Cincinnati Bengals"),
        "stroud": ("C.J.", "Stroud", "QB", "Houston Texans"),
        "mccaffrey": ("Christian", "McCaffrey", "RB", "San Francisco 49ers"),
    }

    name_lower = name.lower()
    for key, (first, last, pos, team) in known.items():
        if key in name_lower or name_lower in key:
            return [NFLPlayerInfo(id=seed % 10000, first_name=first, last_name=last, position=pos, team=team, conference="")]

    first = name.split()[0].title() if " " in name else name.title()
    last = name.split()[-1].title() if " " in name else "Player"
    pos = rng.choice(["QB", "RB", "WR", "TE", "LB", "DE"])
    return [NFLPlayerInfo(id=seed % 10000, first_name=first, last_name=last, position=pos, team="Unknown", conference="")]


def _mock_nfl_stats(season: int) -> NFLSeasonStats:
    """Mock NFL season stats."""
    import hashlib
    import random

    rng = random.Random(season)
    return NFLSeasonStats(
        season=season,
        games_played=rng.randint(10, 17),
        pass_completions=rng.randint(200, 400),
        pass_attempts=rng.randint(350, 600),
        pass_yards=rng.randint(2500, 5000),
        pass_touchdowns=rng.randint(15, 40),
        interceptions=rng.randint(3, 15),
        rush_attempts=rng.randint(20, 150),
        rush_yards=rng.randint(100, 800),
        rush_touchdowns=rng.randint(0, 8),
        receptions=rng.randint(0, 80),
        receiving_yards=rng.randint(0, 1000),
        receiving_touchdowns=rng.randint(0, 8),
        targets=rng.randint(0, 100),
        sacks=rng.uniform(0, 12),
        tackles=rng.randint(0, 100),
        def_interceptions=rng.randint(0, 6),
    )
