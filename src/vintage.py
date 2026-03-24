"""
Vintage card analysis module.
Provides specialized analysis for pre-2000 sports cards including
era-specific pricing factors, condition sensitivity, and investment outlook.
"""

from dataclasses import dataclass, field
from .ebay_client import EbayClient, PriceResult


# Key vintage sets and their significance
ICONIC_SETS = {
    # Baseball
    "1952 topps": {"sport": "baseball", "significance": "The holy grail of post-war baseball sets. #311 Mickey Mantle is the most iconic post-war card.", "era": "post-war"},
    "1951 bowman": {"sport": "baseball", "significance": "Mickey Mantle's true rookie card (#253). Willie Mays rookie (#305).", "era": "post-war"},
    "1933 goudey": {"sport": "baseball", "significance": "First major gum card set. Babe Ruth #53, #149, #181 are crown jewels.", "era": "pre-war"},
    "1909 t206": {"sport": "baseball", "significance": "The 'Monster' of vintage sets. Honus Wagner is the most valuable card ever printed.", "era": "pre-war"},
    "1955 topps": {"sport": "baseball", "significance": "Roberto Clemente rookie (#164). Sandy Koufax rookie (#123).", "era": "post-war"},
    "1954 topps": {"sport": "baseball", "significance": "Hank Aaron rookie (#128). First full Topps set with real competition from Bowman.", "era": "post-war"},
    "1969 topps": {"sport": "baseball", "significance": "Reggie Jackson rookie (#260). Last year of the classic Topps design era.", "era": "post-war"},
    "1989 upper deck": {"sport": "baseball", "significance": "Ken Griffey Jr rookie (#1). Revolutionized card quality. Start of the modern era.", "era": "junk-wax"},
    "1986 donruss": {"sport": "baseball", "significance": "Jose Canseco Rated Rookie. Peak junk wax — high supply limits value.", "era": "junk-wax"},
    "1993 sp": {"sport": "baseball", "significance": "Derek Jeter rookie (#279). The most valuable junk-wax era card.", "era": "junk-wax"},
    # Basketball
    "1986 fleer": {"sport": "basketball", "significance": "THE basketball set. Michael Jordan rookie (#57) defines the hobby.", "era": "post-war"},
    "1969 topps basketball": {"sport": "basketball", "significance": "Lew Alcindor (Kareem) rookie (#25). Early basketball cards are scarce.", "era": "post-war"},
    "1961 fleer basketball": {"sport": "basketball", "significance": "Wilt Chamberlain rookie (#8). Oscar Robertson rookie (#36). Very scarce.", "era": "post-war"},
    "1996 topps chrome": {"sport": "basketball", "significance": "Kobe Bryant rookie (#138). Key refractor is a five-figure card.", "era": "modern-vintage"},
    "1997 metal universe": {"sport": "basketball", "significance": "Precious Metal Gems (PMG) are among the most valuable 90s inserts.", "era": "modern-vintage"},
    # Football
    "1958 topps football": {"sport": "football", "significance": "Jim Brown rookie (#62). One of the most valuable football cards.", "era": "post-war"},
    "1965 topps football": {"sport": "football", "significance": "Joe Namath rookie (#122). Broadway Joe in his AFL days.", "era": "post-war"},
    "1981 topps football": {"sport": "football", "significance": "Joe Montana rookie (#216). Defines the modern football card market.", "era": "post-war"},
    "1984 topps football": {"sport": "football", "significance": "Dan Marino (#123) and John Elway (#63) rookies.", "era": "post-war"},
    "2000 playoff contenders": {"sport": "football", "significance": "Tom Brady rookie auto (#144). THE football card of the modern era.", "era": "modern-vintage"},
    # Hockey
    "1979 o-pee-chee": {"sport": "hockey", "significance": "Wayne Gretzky rookie (#18). The most iconic hockey card ever.", "era": "post-war"},
    "1966 topps hockey": {"sport": "hockey", "significance": "Bobby Orr rookie (#35). Key card for hockey collectors.", "era": "post-war"},
    "1951 parkhurst": {"sport": "hockey", "significance": "Gordie Howe rookie (#66). First major post-war hockey set.", "era": "post-war"},
}

# Era-specific pricing factors
ERA_FACTORS = {
    "pre-war": {
        "condition_multiplier": 10,  # PSA 8 can be 10x a PSA 5
        "description": "Pre-1945 cards. Extremely scarce in high grade. Even low-grade examples command strong premiums.",
        "tip": "Centering and paper quality are the main grading challenges. A PSA 4-5 is considered a strong example for this era.",
    },
    "post-war": {
        "condition_multiplier": 6,
        "description": "1945-1979 cards. Condition is king. High-grade examples (PSA 7+) trade at massive premiums over lower grades.",
        "tip": "Look for sharp corners and clean backs. Factory centering issues are common and heavily penalized.",
    },
    "junk-wax": {
        "condition_multiplier": 2,
        "description": "1986-1993 era. Massively overproduced. Only key rookies in PSA 10 hold real value.",
        "tip": "Avoid investing in common cards from this era — supply is nearly infinite. Focus exclusively on key rookies in gem mint condition.",
    },
    "modern-vintage": {
        "condition_multiplier": 3,
        "description": "1993-2005 cards. Transitional era with limited print runs returning. Refractors, autos, and low-numbered parallels drive value.",
        "tip": "Parallels and inserts are where the value lives. Base cards have limited upside unless it's a true superstar rookie.",
    },
}


@dataclass
class VintageAnalysis:
    card_query: str
    era: str
    era_description: str
    set_significance: str
    condition_impact: str
    price_by_grade: dict[str, float]  # grade -> avg price
    investment_outlook: str
    tips: list[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"=== Vintage Card Analysis: '{self.card_query}' ===",
            f"",
            f"Era:          {self.era.replace('-', ' ').title()}",
            f"Description:  {self.era_description}",
        ]

        if self.set_significance:
            lines.append(f"Set Notes:    {self.set_significance}")

        lines.append(f"")
        lines.append(f"--- Condition Impact ---")
        lines.append(f"  {self.condition_impact}")

        if self.price_by_grade:
            lines.append(f"")
            lines.append(f"--- Estimated Price by Grade ---")
            for grade, price in sorted(self.price_by_grade.items(), key=lambda x: x[0]):
                lines.append(f"  {grade}: ${price:.2f}")

        lines.append(f"")
        lines.append(f"--- Investment Outlook ---")
        lines.append(f"  {self.investment_outlook}")

        if self.tips:
            lines.append(f"")
            lines.append(f"--- Collector Tips ---")
            for tip in self.tips:
                lines.append(f"  * {tip}")

        return "\n".join(lines)


async def analyze_vintage_card(
    client: EbayClient,
    card_query: str,
) -> VintageAnalysis:
    """
    Analyze a vintage card with era-specific insights and grade-based pricing.
    """
    # Determine era and set info
    era, set_info = _identify_era_and_set(card_query)
    era_data = ERA_FACTORS.get(era, ERA_FACTORS["post-war"])

    # Get prices at different grades
    price_by_grade = {}
    grades_to_check = ["PSA 10", "PSA 9", "PSA 8", "PSA 7", "PSA 5", "PSA 3"]

    if era == "pre-war":
        grades_to_check = ["PSA 8", "PSA 7", "PSA 5", "PSA 4", "PSA 3", "PSA 1"]
    elif era == "junk-wax":
        grades_to_check = ["PSA 10", "PSA 9", "PSA 8"]

    # Fetch prices for each grade level
    for grade in grades_to_check:
        result = await client.search_sold(f"{card_query} {grade}", limit=10)
        if result.avg_price > 0:
            price_by_grade[grade] = result.avg_price

    # Also get raw price
    raw_result = await client.search_sold(f"{card_query} raw", limit=10)
    if raw_result.avg_price > 0:
        price_by_grade["Raw"] = raw_result.avg_price

    # Generate condition impact description
    condition_impact = _describe_condition_impact(price_by_grade, era_data)

    # Generate investment outlook
    investment_outlook = _generate_vintage_outlook(
        card_query, era, era_data, price_by_grade, set_info
    )

    # Collect tips
    tips = [era_data["tip"]]
    tips.extend(_generate_vintage_tips(era, price_by_grade, set_info))

    return VintageAnalysis(
        card_query=card_query,
        era=era,
        era_description=era_data["description"],
        set_significance=set_info.get("significance", "") if set_info else "",
        condition_impact=condition_impact,
        price_by_grade=price_by_grade,
        investment_outlook=investment_outlook,
        tips=tips,
    )


def _identify_era_and_set(query: str) -> tuple[str, dict | None]:
    """Identify the era and set from the card query."""
    query_lower = query.lower()

    # Try to match a known set
    for set_key, set_info in ICONIC_SETS.items():
        if set_key in query_lower:
            # Determine era from year
            era = set_info.get("era", "post-war")
            return era, set_info

    # Try to extract year and guess era
    import re
    year_match = re.search(r'\b(19\d{2}|200[0-5])\b', query)
    if year_match:
        year = int(year_match.group(1))
        if year < 1945:
            return "pre-war", None
        elif year < 1980:
            return "post-war", None
        elif year < 1994:
            return "junk-wax", None
        else:
            return "modern-vintage", None

    return "post-war", None


def _describe_condition_impact(
    price_by_grade: dict, era_data: dict
) -> str:
    """Describe how much condition matters for this card."""
    if len(price_by_grade) < 2:
        return (
            f"Condition multiplier for this era: ~{era_data['condition_multiplier']}x "
            f"between low and high grades. Insufficient price data to show exact spread."
        )

    prices = [(k, v) for k, v in price_by_grade.items() if v > 0 and k != "Raw"]
    if len(prices) < 2:
        return "Limited graded sales data available."

    prices.sort(key=lambda x: x[1])
    low_grade, low_price = prices[0]
    high_grade, high_price = prices[-1]

    if low_price > 0:
        multiplier = high_price / low_price
        return (
            f"A {high_grade} sells for ~{multiplier:.1f}x more than a {low_grade} "
            f"(${high_price:.2f} vs ${low_price:.2f}). "
            f"Condition is {'extremely' if multiplier > 5 else 'very' if multiplier > 3 else 'moderately'} "
            f"important for this card."
        )

    return f"Price range: ${low_price:.2f} ({low_grade}) to ${high_price:.2f} ({high_grade})"


def _generate_vintage_outlook(
    query: str, era: str, era_data: dict,
    price_by_grade: dict, set_info: dict | None
) -> str:
    """Generate investment outlook for a vintage card."""
    parts = []

    if era == "pre-war":
        parts.append(
            "Pre-war cards are among the most stable collectibles. "
            "Supply is fixed and shrinking as cards degrade over time."
        )
        if any(v > 1000 for v in price_by_grade.values()):
            parts.append("This is a high-value card with strong institutional collector demand.")
        parts.append("Long-term hold — these cards have appreciated steadily for decades.")

    elif era == "post-war":
        parts.append(
            "Post-war vintage cards (1945-1979) are the backbone of the hobby. "
            "Key rookies and Hall of Famers in high grade are strong long-term holds."
        )
        if set_info:
            parts.append("This is from a recognized key set — strong collector demand.")
        parts.append("Focus on condition — a one-grade difference can mean 2-3x in price.")

    elif era == "junk-wax":
        parts.append(
            "Junk wax era cards were massively overproduced. "
            "Most cards from 1986-1993 will NEVER appreciate significantly."
        )
        parts.append(
            "The ONLY exception: key rookie cards in PSA 10 (gem mint). "
            "A PSA 10 is scarce enough to hold value despite massive raw supply."
        )
        if set_info:
            parts.append("This is a recognized key card from the era — one of the few worth holding.")

    elif era == "modern-vintage":
        parts.append(
            "Late 90s to early 2000s cards are gaining collector interest as "
            "millennials hit peak earning years and buy their childhood cards."
        )
        parts.append("Refractors, low-numbered parallels, and auto rookies are the targets.")

    return " ".join(parts)


def _generate_vintage_tips(
    era: str, price_by_grade: dict, set_info: dict | None
) -> list[str]:
    """Generate era-specific collecting tips."""
    tips = []

    raw_price = price_by_grade.get("Raw", 0)

    if raw_price > 0:
        # Check if grading makes sense
        graded_prices = {k: v for k, v in price_by_grade.items() if k != "Raw" and v > 0}
        if graded_prices:
            min_graded = min(graded_prices.values())
            if min_graded > raw_price * 1.5:
                tips.append(
                    f"Raw cards (${raw_price:.2f}) trade at a significant discount to graded. "
                    f"Consider buying raw and submitting for grading."
                )

    if era == "pre-war":
        tips.append("Authentication is critical — reprints and trimmed cards are common.")
        tips.append("Even 'poor' condition pre-war cards of key players have value.")
    elif era == "junk-wax":
        tips.append("Do NOT buy raw cards from this era for investment — only PSA 10 matters.")
        tips.append("Check PSA population reports — if 10,000+ PSA 10s exist, value is limited.")
    elif era == "post-war":
        tips.append("Check for print defects common to the era (fish-eye, snow, wax stains).")
        tips.append("Registry set collectors drive premiums on high-grade examples.")

    if set_info and set_info.get("sport") == "basketball":
        tips.append("Vintage basketball cards are much scarcer than baseball — smaller collector base but growing fast.")

    return tips
