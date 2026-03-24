# Sports Card Agent

## What This Is
An MCP server that provides sports trading card data to other AI agents. 9 tools covering pricing, market analysis, grading ROI, investment advice, player stats (NBA/NFL/MLB), vintage card analysis, and trending players.

## Architecture
- Python 3.12 MCP server using FastMCP
- Runs over stdio protocol
- eBay Browse API for pricing data (mock fallback when no key)
- Ball Don't Lie API for player stats across NBA/NFL/MLB (mock fallback)
- All tools return plain text summaries

## Project Structure
- `src/server.py` — Main MCP server with all 9 tool definitions
- `src/ebay_client.py` — eBay API client with OAuth2 + mock data
- `src/analysis.py` — Price trend analysis and arbitrage detection
- `src/player_stats.py` — NBA stats (Ball Don't Lie API)
- `src/nfl_stats.py` — NFL stats (Ball Don't Lie API)
- `src/mlb_stats.py` — MLB stats (Ball Don't Lie API)
- `src/grading.py` — Grading ROI calculator (PSA/BGS/SGC)
- `src/advisor.py` — Investment advisor (buy/sell/hold)
- `src/trending.py` — Trending NBA players watchlist
- `src/vintage.py` — Vintage card analysis (40+ iconic sets)
- `run_server.py` — Launcher script
- `test_all.py` — Full test suite (29 tests)

## Key Accounts & Config
- **GitHub:** rjexile/sports-card-agent
- **PyPI:** sports-card-agent v1.0.0
- **eBay Developer:** Registered, waiting for approval (keys go in .env)
- **Ball Don't Lie:** Needs free signup at app.balldontlie.io (key goes in .env)

## Running
```bash
# From venv
python run_server.py

# After pip install
sports-card-agent
```

## Testing
```bash
python test_all.py  # 29/29 tests should pass
```

## Revenue Strategy
- Listed on MCP registries for other agents to discover
- Phase 1: Free usage to build adoption
- Phase 2: Monetize via MCPize or similar (85% revenue share)
- Phase 2: Deploy to VPS for 24/7 availability
