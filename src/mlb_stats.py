"""
MLB player stats client using the Ball Don't Lie MLB API.
Same API key as NBA/NFL — covers batting and pitching stats.
"""

import httpx
from dataclasses import dataclass


BASE_URL = "https://api.balldontlie.io/mlb/v1"


@dataclass
class MLBPlayerInfo:
    id: int
    first_name: str
    last_name: str
    position: str
    team: str

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def is_pitcher(self) -> bool:
        return self.position in ("P", "SP", "RP", "CL")


@dataclass
class MLBSeasonStats:
    season: int
    games_played: int
    # Batting
    batting_avg: float = 0
    home_runs: int = 0
    rbis: int = 0
    hits: int = 0
    runs: int = 0
    stolen_bases: int = 0
    obp: float = 0
    slg: float = 0
    ops: float = 0
    strikeouts_batting: int = 0
    walks: int = 0
    # Pitching
    era: float = 0
    wins: int = 0
    losses: int = 0
    saves: int = 0
    innings_pitched: float = 0
    strikeouts_pitching: int = 0
    walks_pitching: int = 0
    whip: float = 0
    is_pitcher: bool = False

    def summary(self) -> str:
        lines = [f"  {self.season} Season ({self.games_played} GP):"]

        if self.is_pitcher:
            lines.append(
                f"    Pitching: {self.wins}W-{self.losses}L | {self.era:.2f} ERA | "
                f"{self.strikeouts_pitching} K | {self.innings_pitched:.1f} IP"
            )
            lines.append(
                f"    WHIP: {self.whip:.3f} | BB: {self.walks_pitching} | SV: {self.saves}"
            )
        else:
            lines.append(
                f"    Batting: .{int(self.batting_avg * 1000):03d} AVG | {self.home_runs} HR | "
                f"{self.rbis} RBI | {self.runs} R"
            )
            lines.append(
                f"    OBP: .{int(self.obp * 1000):03d} | SLG: .{int(self.slg * 1000):03d} | "
                f"OPS: .{int(self.ops * 1000):03d}"
            )
            lines.append(
                f"    Hits: {self.hits} | SB: {self.stolen_bases} | BB: {self.walks} | K: {self.strikeouts_batting}"
            )

        return "\n".join(lines)


@dataclass
class MLBPlayerReport:
    player: MLBPlayerInfo
    current_stats: MLBSeasonStats | None = None
    card_insight: str = ""

    def summary(self) -> str:
        lines = [
            f"=== {self.player.full_name} (MLB) ===",
            f"Position: {self.player.position} | Team: {self.player.team}",
        ]
        if self.current_stats:
            lines.append(f"\nCurrent Season Stats:")
            lines.append(self.current_stats.summary())
        if self.card_insight:
            lines.append(f"\nCard Market Insight:")
            lines.append(f"  {self.card_insight}")
        return "\n".join(lines)


class MLBStatsClient:
    """Client for Ball Don't Lie MLB stats API."""

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

    async def search_player(self, name: str) -> list[MLBPlayerInfo]:
        """Search for MLB players by name."""
        if not self.is_configured:
            return _mock_mlb_search(name)

        resp = await self._http.get("/players", params={"search": name})
        resp.raise_for_status()
        data = resp.json()

        players = []
        for p in data.get("data", []):
            team = p.get("team", {})
            players.append(
                MLBPlayerInfo(
                    id=p["id"],
                    first_name=p.get("first_name", ""),
                    last_name=p.get("last_name", ""),
                    position=p.get("position", "N/A"),
                    team=team.get("full_name", "Unknown"),
                )
            )
        return players

    async def get_season_stats(
        self, player_id: int, season: int = 2025, is_pitcher: bool = False
    ) -> MLBSeasonStats | None:
        """Get a player's season stats."""
        if not self.is_configured:
            return _mock_mlb_stats(season, is_pitcher)

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
        return MLBSeasonStats(
            season=season,
            games_played=s.get("games_played", s.get("games", 0)),
            batting_avg=s.get("batting_average", s.get("avg", 0)),
            home_runs=s.get("home_runs", s.get("hr", 0)),
            rbis=s.get("rbis", s.get("rbi", 0)),
            hits=s.get("hits", 0),
            runs=s.get("runs", 0),
            stolen_bases=s.get("stolen_bases", s.get("sb", 0)),
            obp=s.get("on_base_percentage", s.get("obp", 0)),
            slg=s.get("slugging_percentage", s.get("slg", 0)),
            ops=s.get("ops", 0),
            strikeouts_batting=s.get("strikeouts", 0) if not is_pitcher else 0,
            walks=s.get("walks", s.get("bb", 0)),
            era=s.get("era", 0),
            wins=s.get("wins", 0),
            losses=s.get("losses", 0),
            saves=s.get("saves", 0),
            innings_pitched=s.get("innings_pitched", s.get("ip", 0)),
            strikeouts_pitching=s.get("strikeouts", 0) if is_pitcher else 0,
            walks_pitching=s.get("walks", 0) if is_pitcher else 0,
            whip=s.get("whip", 0),
            is_pitcher=is_pitcher,
        )

    async def get_player_report(self, name: str) -> MLBPlayerReport | None:
        """Search for a player and get their current stats."""
        players = await self.search_player(name)
        if not players:
            return None

        player = players[0]
        season_stats = await self.get_season_stats(
            player.id, is_pitcher=player.is_pitcher
        )
        insight = _generate_mlb_card_insight(player, season_stats)

        return MLBPlayerReport(
            player=player,
            current_stats=season_stats,
            card_insight=insight,
        )

    async def close(self):
        await self._http.aclose()


def _generate_mlb_card_insight(player: MLBPlayerInfo, stats: MLBSeasonStats | None) -> str:
    """Generate card market insight based on MLB performance."""
    if not stats:
        return "No current season data available."

    insights = []

    if stats.is_pitcher:
        if stats.era <= 2.50 and stats.innings_pitched >= 100:
            insights.append(f"Ace-level ERA ({stats.era:.2f}) — premium on rookie and auto cards.")
        elif stats.era <= 3.50:
            insights.append(f"Strong ERA ({stats.era:.2f}) — solid card demand.")
        elif stats.era > 5.00 and stats.innings_pitched >= 50:
            insights.append(f"Struggling ({stats.era:.2f} ERA) — card values likely declining.")

        if stats.strikeouts_pitching >= 200:
            insights.append(f"Strikeout artist ({stats.strikeouts_pitching} K) — collectors love K kings.")
        if stats.saves >= 30:
            insights.append(f"Elite closer ({stats.saves} SV) — niche but loyal collector base.")
        if stats.wins >= 15:
            insights.append(f"Big winner ({stats.wins}W) — strong traditional appeal.")
    else:
        if stats.home_runs >= 40:
            insights.append(f"Power elite ({stats.home_runs} HR) — major card demand driver.")
        elif stats.home_runs >= 25:
            insights.append(f"Strong power ({stats.home_runs} HR) — solid collector interest.")

        if stats.batting_avg >= 0.300:
            insights.append(f"Elite hitter (.{int(stats.batting_avg * 1000):03d}) — high card premium.")
        elif stats.batting_avg < 0.220 and stats.games_played > 60:
            insights.append(f"Struggling at the plate (.{int(stats.batting_avg * 1000):03d}) — card values may be soft.")

        if stats.stolen_bases >= 30:
            insights.append(f"Speed threat ({stats.stolen_bases} SB) — dynamic players command premiums.")

        if stats.ops >= 0.900:
            insights.append(f"Elite OPS (.{int(stats.ops * 1000):03d}) — premier hitter, premium cards.")

        if stats.home_runs >= 30 and stats.stolen_bases >= 20:
            insights.append("30/20 club — rare combo drives massive collector demand.")

    if stats.games_played < 30:
        insights.append(f"Only {stats.games_played} games — possible injury. Buy-low opportunity if healthy.")

    if not insights:
        insights.append("Average production — card values likely stable.")

    if not player.team or player.team == "Unknown":
        insights.append("[MOCK DATA — configure BALLDONTLIE_API_KEY for live stats]")

    return " ".join(insights)


def _mock_mlb_search(name: str) -> list[MLBPlayerInfo]:
    """Mock MLB player search."""
    import hashlib
    import random

    seed = int(hashlib.md5(name.lower().encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)

    known = {
        "ohtani": ("Shohei", "Ohtani", "DH", "Los Angeles Dodgers"),
        "judge": ("Aaron", "Judge", "OF", "New York Yankees"),
        "acuna": ("Ronald", "Acuna Jr", "OF", "Atlanta Braves"),
        "soto": ("Juan", "Soto", "OF", "New York Mets"),
        "tatis": ("Fernando", "Tatis Jr", "SS", "San Diego Padres"),
        "trout": ("Mike", "Trout", "OF", "Los Angeles Angels"),
        "betts": ("Mookie", "Betts", "OF", "Los Angeles Dodgers"),
        "cole": ("Gerrit", "Cole", "SP", "New York Yankees"),
        "devers": ("Rafael", "Devers", "3B", "Boston Red Sox"),
        "rodriguez": ("Julio", "Rodriguez", "OF", "Seattle Mariners"),
        "skenes": ("Paul", "Skenes", "SP", "Pittsburgh Pirates"),
    }

    name_lower = name.lower()
    for key, (first, last, pos, team) in known.items():
        if key in name_lower or name_lower in key:
            return [MLBPlayerInfo(id=seed % 10000, first_name=first, last_name=last, position=pos, team=team)]

    first = name.split()[0].title() if " " in name else name.title()
    last = name.split()[-1].title() if " " in name else "Player"
    pos = rng.choice(["OF", "SS", "3B", "1B", "2B", "C", "SP", "RP"])
    return [MLBPlayerInfo(id=seed % 10000, first_name=first, last_name=last, position=pos, team="Unknown")]


def _mock_mlb_stats(season: int, is_pitcher: bool) -> MLBSeasonStats:
    """Mock MLB season stats."""
    import random

    rng = random.Random(season + (1 if is_pitcher else 0))

    if is_pitcher:
        return MLBSeasonStats(
            season=season,
            games_played=rng.randint(20, 34),
            era=round(rng.uniform(2.0, 5.5), 2),
            wins=rng.randint(5, 20),
            losses=rng.randint(3, 14),
            saves=rng.randint(0, 40),
            innings_pitched=round(rng.uniform(80, 220), 1),
            strikeouts_pitching=rng.randint(80, 300),
            walks_pitching=rng.randint(20, 80),
            whip=round(rng.uniform(0.85, 1.50), 3),
            is_pitcher=True,
        )
    else:
        avg = round(rng.uniform(.220, .340), 3)
        obp = round(avg + rng.uniform(.040, .100), 3)
        slg = round(rng.uniform(.350, .650), 3)
        return MLBSeasonStats(
            season=season,
            games_played=rng.randint(80, 162),
            batting_avg=avg,
            home_runs=rng.randint(5, 50),
            rbis=rng.randint(30, 130),
            hits=rng.randint(80, 200),
            runs=rng.randint(40, 120),
            stolen_bases=rng.randint(0, 50),
            obp=obp,
            slg=slg,
            ops=round(obp + slg, 3),
            strikeouts_batting=rng.randint(60, 200),
            walks=rng.randint(20, 100),
            is_pitcher=False,
        )
