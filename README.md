# Sports Card Agent

An MCP server that gives AI agents expert-level sports trading card data. Covers pricing, market analysis, arbitrage detection, grading ROI, investment advice, player stats (NBA/NFL/MLB), vintage card analysis, and trending player alerts.

**9 tools. 3 sports. 40+ vintage sets. Zero manual research.**

## Tools

### Pricing & Market

| Tool | Description |
|------|-------------|
| `card_price_lookup` | Real-time sold and active prices from eBay. Supports any sport, brand, year, or grading. |
| `card_market_analysis` | Trend analysis comparing sold vs asking prices. Detects arbitrage opportunities where cards are listed below market value. |

### Player Stats

| Tool | Description |
|------|-------------|
| `player_stats_lookup` | Multi-sport player stats (NBA/NFL/MLB) with card market insights based on performance. |
| `nfl_stats_lookup` | NFL passing, rushing, receiving, and defensive stats with card market insights. |
| `mlb_stats_lookup` | MLB batting (AVG, HR, RBI, OPS) and pitching (ERA, K, WHIP) stats with card insights. |

### Analysis & Strategy

| Tool | Description |
|------|-------------|
| `grading_roi_calculator` | Calculates whether grading a card is profitable. Compares raw vs graded prices for PSA, BGS, and SGC with fee-adjusted ROI. |
| `card_investment_advisor` | Buy/sell/hold recommendations combining market trends with player performance data across all 3 sports. |
| `trending_players` | Identifies NBA players with breakout performances whose cards are likely rising in value. |
| `vintage_card_analysis` | Era-specific analysis for pre-2000 cards. Covers 40+ iconic sets from 1909 T206 to 2000 Playoff Contenders with grade-based pricing. |

## Quick Start

### Install from PyPI

```bash
pip install sports-card-agent
```

### Run the server

```bash
sports-card-agent
```

### Use with Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "sports-card-agent": {
      "command": "sports-card-agent"
    }
  }
}
```

### Use with Claude Code

Add to your `.mcp.json`:

```json
{
  "mcpServers": {
    "sports-card-agent": {
      "command": "sports-card-agent"
    }
  }
}
```

## Configuration

Create a `.env` file or set environment variables:

```bash
# eBay API (register free at developer.ebay.com)
EBAY_APP_ID=your_app_id
EBAY_CERT_ID=your_cert_id

# Ball Don't Lie API (register free at app.balldontlie.io)
BALLDONTLIE_API_KEY=your_api_key
```

The server works without API keys using mock data, so you can try it immediately.

## Example Queries

Once connected, any AI agent can ask:

- "What's a 2023 Topps Chrome Wembanyama rookie selling for?"
- "Should I buy or sell my Patrick Mahomes rookie card?"
- "Is it worth grading my 1986 Fleer Jordan?"
- "Who are the trending NBA players whose cards are rising?"
- "Analyze the market for Ken Griffey Jr 1989 Upper Deck rookie"
- "What's the investment outlook on vintage 1952 Topps Mickey Mantle?"
- "How is Shohei Ohtani performing this season and what does that mean for his cards?"

## Sports & Sets Covered

**Sports:** Baseball, Basketball, Football, Hockey, Soccer

**Player Stats:** NBA (all teams), NFL (all positions), MLB (batting + pitching)

**Vintage Sets Include:** 1909 T206, 1933 Goudey, 1951 Bowman, 1952 Topps, 1954-55 Topps, 1958 Topps Football, 1961 Fleer Basketball, 1965 Topps Football, 1966 Topps Hockey, 1969 Topps, 1979 O-Pee-Chee, 1981 Topps Football, 1984 Topps Football, 1986 Fleer Basketball, 1986 Donruss, 1989 Upper Deck, 1993 SP, 1996 Topps Chrome, 1997 Metal Universe, 2000 Playoff Contenders, and more.

**Grading Companies:** PSA, BGS, SGC (all service tiers with current pricing)

## Development

```bash
git clone https://github.com/rjexile/sports-card-agent.git
cd sports-card-agent
python -m venv venv
source venv/Scripts/activate  # Windows
pip install -e .
python test_all.py  # Run all 29 tests
```

## License

MIT
