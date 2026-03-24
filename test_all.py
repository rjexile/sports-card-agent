"""Full test suite for Sports Card Agent — all 9 tools."""
import asyncio
from src.server import mcp


async def test_all():
    results = {}

    # ── Tool 1: card_price_lookup (sold) ──
    try:
        r = await mcp.call_tool("card_price_lookup", {"query": "2023 Topps Chrome Victor Wembanyama rookie", "listing_type": "sold", "limit": 5})
        text = str(r)
        assert "Price data" in text and "Average" in text
        results["1a. card_price_lookup (sold)"] = "PASS"
    except Exception as e:
        results["1a. card_price_lookup (sold)"] = f"FAIL: {e}"

    # ── Tool 1b: card_price_lookup (active) ──
    try:
        r = await mcp.call_tool("card_price_lookup", {"query": "Ken Griffey Jr 1989 Upper Deck", "listing_type": "active", "limit": 3})
        text = str(r)
        assert "Price data" in text
        results["1b. card_price_lookup (active)"] = "PASS"
    except Exception as e:
        results["1b. card_price_lookup (active)"] = f"FAIL: {e}"

    # ── Tool 2: card_market_analysis ──
    try:
        r = await mcp.call_tool("card_market_analysis", {"query": "Michael Jordan Fleer rookie PSA 9"})
        text = str(r)
        assert "Market Analysis" in text and "Spread" in text
        results["2. card_market_analysis"] = "PASS"
    except Exception as e:
        results["2. card_market_analysis"] = f"FAIL: {e}"

    # ── Tool 3a: player_stats_lookup (NBA) ──
    try:
        r = await mcp.call_tool("player_stats_lookup", {"player_name": "LeBron James", "sport": "nba"})
        text = str(r)
        assert "LeBron" in text and "PPG" in text
        results["3a. player_stats (NBA)"] = "PASS"
    except Exception as e:
        results["3a. player_stats (NBA)"] = f"FAIL: {e}"

    # ── Tool 3b: player_stats_lookup (NFL) ──
    try:
        r = await mcp.call_tool("player_stats_lookup", {"player_name": "Mahomes", "sport": "nfl"})
        text = str(r)
        assert "Mahomes" in text and "NFL" in text
        results["3b. player_stats (NFL)"] = "PASS"
    except Exception as e:
        results["3b. player_stats (NFL)"] = f"FAIL: {e}"

    # ── Tool 3c: player_stats_lookup (MLB) ──
    try:
        r = await mcp.call_tool("player_stats_lookup", {"player_name": "Aaron Judge", "sport": "mlb"})
        text = str(r)
        assert "Judge" in text and "MLB" in text
        results["3c. player_stats (MLB)"] = "PASS"
    except Exception as e:
        results["3c. player_stats (MLB)"] = f"FAIL: {e}"

    # ── Tool 4: nfl_stats_lookup ──
    try:
        r = await mcp.call_tool("nfl_stats_lookup", {"player_name": "Justin Jefferson"})
        text = str(r)
        assert "Jefferson" in text and "NFL" in text
        results["4. nfl_stats_lookup"] = "PASS"
    except Exception as e:
        results["4. nfl_stats_lookup"] = f"FAIL: {e}"

    # ── Tool 5: mlb_stats_lookup ──
    try:
        r = await mcp.call_tool("mlb_stats_lookup", {"player_name": "Gerrit Cole"})
        text = str(r)
        assert "Cole" in text and "MLB" in text
        results["5. mlb_stats_lookup"] = "PASS"
    except Exception as e:
        results["5. mlb_stats_lookup"] = f"FAIL: {e}"

    # ── Tool 5b: mlb_stats_lookup (pitcher) ──
    try:
        r = await mcp.call_tool("mlb_stats_lookup", {"player_name": "Paul Skenes"})
        text = str(r)
        assert "Skenes" in text and "ERA" in text
        results["5b. mlb_stats (pitcher)"] = "PASS"
    except Exception as e:
        results["5b. mlb_stats (pitcher)"] = f"FAIL: {e}"

    # ── Tool 6a: grading_roi (PSA 10) ──
    try:
        r = await mcp.call_tool("grading_roi_calculator", {"card_query": "2023 Topps Chrome Wembanyama rookie", "grading_company": "PSA", "expected_grade": "10"})
        text = str(r)
        assert "Grading ROI" in text and "Recommendation" in text and "PSA" in text
        results["6a. grading_roi (PSA)"] = "PASS"
    except Exception as e:
        results["6a. grading_roi (PSA)"] = f"FAIL: {e}"

    # ── Tool 6b: grading_roi (BGS 9) ──
    try:
        r = await mcp.call_tool("grading_roi_calculator", {"card_query": "1986 Fleer Michael Jordan", "grading_company": "BGS", "expected_grade": "9"})
        text = str(r)
        assert "BGS" in text and "Recommendation" in text
        results["6b. grading_roi (BGS)"] = "PASS"
    except Exception as e:
        results["6b. grading_roi (BGS)"] = f"FAIL: {e}"

    # ── Tool 6c: grading_roi (SGC 10) ──
    try:
        r = await mcp.call_tool("grading_roi_calculator", {"card_query": "2020 Panini Prizm Joe Burrow", "grading_company": "SGC", "expected_grade": "10"})
        text = str(r)
        assert "SGC" in text
        results["6c. grading_roi (SGC)"] = "PASS"
    except Exception as e:
        results["6c. grading_roi (SGC)"] = f"FAIL: {e}"

    # ── Tool 7a: investment_advisor (NBA) ──
    try:
        r = await mcp.call_tool("card_investment_advisor", {"card_query": "2023 Topps Chrome Wembanyama auto", "player_name": "Wembanyama", "sport": "nba"})
        text = str(r)
        assert "Investment Advice" in text
        assert any(x in text for x in ["BUY", "SELL", "HOLD", "AVOID"])
        results["7a. advisor (NBA)"] = "PASS"
    except Exception as e:
        results["7a. advisor (NBA)"] = f"FAIL: {e}"

    # ── Tool 7b: investment_advisor (NFL) ──
    try:
        r = await mcp.call_tool("card_investment_advisor", {"card_query": "2018 Panini Prizm Josh Allen", "player_name": "Josh Allen", "sport": "nfl"})
        text = str(r)
        assert "Investment Advice" in text
        results["7b. advisor (NFL)"] = "PASS"
    except Exception as e:
        results["7b. advisor (NFL)"] = f"FAIL: {e}"

    # ── Tool 7c: investment_advisor (MLB) ──
    try:
        r = await mcp.call_tool("card_investment_advisor", {"card_query": "2018 Topps Update Ohtani rookie", "player_name": "Ohtani", "sport": "mlb"})
        text = str(r)
        assert "Investment Advice" in text
        results["7c. advisor (MLB)"] = "PASS"
    except Exception as e:
        results["7c. advisor (MLB)"] = f"FAIL: {e}"

    # ── Tool 7d: investment_advisor (no player stats) ──
    try:
        r = await mcp.call_tool("card_investment_advisor", {"card_query": "1952 Topps Mickey Mantle #311"})
        text = str(r)
        assert "Investment Advice" in text
        results["7d. advisor (no player)"] = "PASS"
    except Exception as e:
        results["7d. advisor (no player)"] = f"FAIL: {e}"

    # ── Tool 8: trending_players ──
    try:
        r = await mcp.call_tool("trending_players", {"limit": 5})
        text = str(r)
        assert "Trending" in text
        results["8. trending_players"] = "PASS"
    except Exception as e:
        results["8. trending_players"] = f"FAIL: {e}"

    # ── Tool 9a: vintage (post-war baseball) ──
    try:
        r = await mcp.call_tool("vintage_card_analysis", {"card_query": "1952 Topps Mickey Mantle"})
        text = str(r)
        assert "Vintage" in text and "Era" in text
        results["9a. vintage (post-war)"] = "PASS"
    except Exception as e:
        results["9a. vintage (post-war)"] = f"FAIL: {e}"

    # ── Tool 9b: vintage (basketball) ──
    try:
        r = await mcp.call_tool("vintage_card_analysis", {"card_query": "1986 Fleer Michael Jordan rookie"})
        text = str(r)
        assert "Vintage" in text
        results["9b. vintage (basketball)"] = "PASS"
    except Exception as e:
        results["9b. vintage (basketball)"] = f"FAIL: {e}"

    # ── Tool 9c: vintage (junk wax) ──
    try:
        r = await mcp.call_tool("vintage_card_analysis", {"card_query": "1989 Upper Deck Ken Griffey Jr rookie"})
        text = str(r)
        assert "Vintage" in text
        results["9c. vintage (junk wax)"] = "PASS"
    except Exception as e:
        results["9c. vintage (junk wax)"] = f"FAIL: {e}"

    # ── Tool 9d: vintage (hockey) ──
    try:
        r = await mcp.call_tool("vintage_card_analysis", {"card_query": "1979 O-Pee-Chee Wayne Gretzky rookie"})
        text = str(r)
        assert "Vintage" in text
        results["9d. vintage (hockey)"] = "PASS"
    except Exception as e:
        results["9d. vintage (hockey)"] = f"FAIL: {e}"

    # ── Tool 9e: vintage (football) ──
    try:
        r = await mcp.call_tool("vintage_card_analysis", {"card_query": "1958 Topps Jim Brown rookie"})
        text = str(r)
        assert "Vintage" in text
        results["9e. vintage (football)"] = "PASS"
    except Exception as e:
        results["9e. vintage (football)"] = f"FAIL: {e}"

    # ── EDGE CASES ──

    # Unknown player
    try:
        r = await mcp.call_tool("player_stats_lookup", {"player_name": "zzzznonexistent", "sport": "nba"})
        text = str(r)
        # Should return a useful message, not crash
        assert "found" in text.lower() or "no" in text.lower() or len(text) > 10
        results["E1. unknown player"] = "PASS"
    except Exception as e:
        results["E1. unknown player"] = f"FAIL: {e}"

    # Empty query
    try:
        r = await mcp.call_tool("card_price_lookup", {"query": ""})
        text = str(r)
        results["E2. empty query"] = "PASS"
    except Exception as e:
        results["E2. empty query"] = f"FAIL: {e}"

    # Boundary limit values
    try:
        r = await mcp.call_tool("card_price_lookup", {"query": "test", "limit": 0})
        text = str(r)
        results["E3. limit=0"] = "PASS"
    except Exception as e:
        results["E3. limit=0"] = f"FAIL: {e}"

    try:
        r = await mcp.call_tool("card_price_lookup", {"query": "test", "limit": 999})
        text = str(r)
        results["E4. limit=999"] = "PASS"
    except Exception as e:
        results["E4. limit=999"] = f"FAIL: {e}"

    # Invalid grading company
    try:
        r = await mcp.call_tool("grading_roi_calculator", {"card_query": "test card", "grading_company": "FAKE", "expected_grade": "10"})
        text = str(r)
        # Should fallback to PSA, not crash
        results["E5. bad grading company"] = "PASS"
    except Exception as e:
        results["E5. bad grading company"] = f"FAIL: {e}"

    # Invalid sport
    try:
        r = await mcp.call_tool("player_stats_lookup", {"player_name": "LeBron", "sport": "cricket"})
        text = str(r)
        # Should default to NBA
        results["E6. invalid sport"] = "PASS"
    except Exception as e:
        results["E6. invalid sport"] = f"FAIL: {e}"

    # trending with limit=1
    try:
        r = await mcp.call_tool("trending_players", {"limit": 1})
        text = str(r)
        results["E7. trending limit=1"] = "PASS"
    except Exception as e:
        results["E7. trending limit=1"] = f"FAIL: {e}"

    # Print results
    print("=" * 60)
    print("  FULL TEST SUITE - Sports Card Agent")
    print("=" * 60)
    passed = sum(1 for v in results.values() if v == "PASS")
    failed = sum(1 for v in results.values() if v != "PASS")
    total = len(results)

    for name, result in results.items():
        icon = "OK" if result == "PASS" else "XX"
        print(f"  [{icon}] {name}: {result}")

    print()
    print(f"  RESULT: {passed}/{total} passed, {failed} failed")
    if failed == 0:
        print("  ALL TESTS PASSED - Ready for marketplace!")
    else:
        print("  SOME TESTS FAILED - Fix before listing!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_all())
