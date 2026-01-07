"""
Kill criteria engine - combines all gatekeeper checks.
Applies Pathway Property business rules to determine verdict.
"""

from typing import Optional, Tuple, List

from models import (
    StreetLevelAnalysis,
    Verdict,
    CheckScore,
)
from services.gatekeeper.social_housing import check_social_housing
from services.gatekeeper.flood_fire import check_flood_risk, check_bushfire_risk
from services.gatekeeper.zoning import check_zoning
from services.gatekeeper.flight_paths import check_flight_paths


# Kill criteria thresholds
SOCIAL_HOUSING_REVIEW_THRESHOLD = 15.0  # % in SA1
SOCIAL_HOUSING_KILL_THRESHOLD = 20.0    # % on street
ANEF_KILL_THRESHOLD = 20
N70_KILL_THRESHOLD = 20
YIELD_WARNING_THRESHOLD = 4.0  # Gross yield %


async def run_gatekeeper(
    address: str,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    state: str = "VIC",
    gross_yield: Optional[float] = None
) -> Tuple[StreetLevelAnalysis, Verdict, List[str]]:
    """
    Run all street-level checks and determine verdict.
    
    Returns:
    - StreetLevelAnalysis: All check results
    - Verdict: PROCEED, REVIEW, or REJECT
    - List[str]: Kill reasons (if REJECT)
    """
    print(f"\n{'='*60}")
    print(f"[Gatekeeper] Starting analysis for: {address}")
    print(f"[Gatekeeper] Coordinates: lat={lat}, lng={lng}, state={state}")
    print(f"{'='*60}")
    
    # Run all checks in parallel
    social_housing = await check_social_housing(lat, lng, address)
    flood_risk = await check_flood_risk(lat, lng, address, state)
    bushfire_risk = await check_bushfire_risk(lat, lng, address, state)
    zoning = await check_zoning(lat, lng, address, state)
    flight_path = await check_flight_paths(lat, lng, address)
    
    # Build analysis object
    analysis = StreetLevelAnalysis(
        social_housing=social_housing,
        flight_path=flight_path,
        flood_risk=flood_risk,
        bushfire_risk=bushfire_risk,
        zoning=zoning
    )
    
    # Apply kill criteria
    kill_reasons = []
    
    # 1. Social Housing Kill
    if social_housing.score == CheckScore.FAIL:
        kill_reasons.append(
            f"Social housing density too high: {social_housing.density_percent:.1f}% "
            f"(threshold: {SOCIAL_HOUSING_REVIEW_THRESHOLD}%)"
        )
    
    # 2. Flight Path Kill
    if flight_path.score == CheckScore.FAIL:
        kill_reasons.append(
            f"Aircraft noise too high: ANEF {flight_path.anef}, N70 {flight_path.n70} flights/day "
            f"(threshold: ANEF>{ANEF_KILL_THRESHOLD} or N70>{N70_KILL_THRESHOLD})"
        )
    
    # 3. Flood Kill
    if flood_risk.score == CheckScore.FAIL and flood_risk.building_at_risk:
        kill_reasons.append(
            "Building footprint intersects 1% AEP flood extent"
        )
    
    # 4. Bushfire - Not an auto-kill, but severe warning
    # BAL-40 and BAL-FZ require significant cost buffers
    
    # Determine verdict
    if kill_reasons:
        verdict = Verdict.REJECT
    elif any(check.score == CheckScore.WARNING for check in [
        social_housing, flood_risk, bushfire_risk, zoning, flight_path
    ]):
        verdict = Verdict.REVIEW
    else:
        verdict = Verdict.PROCEED
    
    print(f"\n[Gatekeeper] RESULTS:")
    print(f"  - Social Housing: {social_housing.score.value} ({social_housing.density_percent:.1f}%)")
    print(f"  - Flight Path: {flight_path.score.value} (ANEF={flight_path.anef}, N70={flight_path.n70})")
    print(f"  - Flood Risk: {flood_risk.score.value}")
    print(f"  - Bushfire: {bushfire_risk.score.value} (BAL={bushfire_risk.bal_rating})")
    print(f"  - Zoning: {zoning.score.value} ({zoning.code})")
    print(f"  >>> VERDICT: {verdict.value}")
    if kill_reasons:
        print(f"  >>> KILL REASONS: {kill_reasons}")
    print(f"{'='*60}\n")
    
    # Additional warnings (not kills)
    warnings = []
    
    if bushfire_risk.bal_rating in ["BAL-40", "BAL-FZ"]:
        warnings.append(
            f"High bushfire risk ({bushfire_risk.bal_rating}) - "
            "significant construction cost buffer required"
        )
    
    if zoning.heritage_overlay:
        warnings.append(
            "Heritage Overlay - restrictions on demolition and external alterations"
        )
    
    if gross_yield is not None and gross_yield < YIELD_WARNING_THRESHOLD:
        warnings.append(
            f"Low gross yield ({gross_yield:.1f}%) - "
            f"below {YIELD_WARNING_THRESHOLD}% threshold unless capital growth play"
        )
    
    return analysis, verdict, kill_reasons


def get_kill_criteria_summary() -> dict:
    """Get summary of all kill criteria for display."""
    return {
        "auto_kill": [
            {
                "name": "Social Housing Cluster",
                "description": f">{SOCIAL_HOUSING_KILL_THRESHOLD}% of street owned by state authority",
                "action": "AUTO KILL"
            },
            {
                "name": "Flight Path Noise",
                "description": f"ANEF >{ANEF_KILL_THRESHOLD} or N70 >{N70_KILL_THRESHOLD} flights/day",
                "action": "AUTO KILL"
            },
            {
                "name": "Flood Risk",
                "description": "Building intersects 1% AEP (1-in-100 year) flood extent",
                "action": "AUTO KILL"
            }
        ],
        "review": [
            {
                "name": "Social Housing Density",
                "description": f">{SOCIAL_HOUSING_REVIEW_THRESHOLD}% in SA1 statistical area",
                "action": "MANUAL REVIEW"
            },
            {
                "name": "Bushfire Risk",
                "description": "BAL-40 or Flame Zone rating",
                "action": "RED FLAG - cost buffer required"
            },
            {
                "name": "Heritage Overlay",
                "description": "Property in heritage overlay zone",
                "action": "WARNING - restrictions apply"
            }
        ],
        "warning": [
            {
                "name": "Low Yield",
                "description": f"Gross yield <{YIELD_WARNING_THRESHOLD}%",
                "action": "WARNING - unless capital growth play"
            },
            {
                "name": "Title Issues",
                "description": "Life Estate or Company Share title",
                "action": "FLAG - hard to finance"
            }
        ]
    }




