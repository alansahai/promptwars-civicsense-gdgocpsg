"""Declarative seed data specifications for realistic civic issues.

Provides a frozen tuple of SeedSpec records to separate declarative seed
data from procedural issue instantiation.
"""

from typing import NamedTuple

from app.domain.taxonomy import Department, IssueCategory

COIMBATORE_COORDINATES: dict[str, tuple[float, float]] = {
    "RS_PURAM": (11.0086, 76.9520),
    "GANDHIPURAM": (11.0183, 76.9644),
    "PEELAMEDU": (11.0267, 77.0145),
    "SAIBABA_COLONY": (11.0289, 76.9458),
    "SINGANALLUR": (10.9992, 77.0256),
    "TOWN_HALL": (10.9965, 76.9602),
    "RAMNAGAR": (11.0142, 76.9611),
    "SARAVANAMPATTI": (11.0792, 76.9997),
    "UKKADAM": (10.9880, 76.9554),
    "AVINASHI_ROAD": (11.0210, 76.9850),
}


class SeedSpec(NamedTuple):
    """Declarative specification for generating a deterministic seed issue."""

    ticket_id: str
    title: str
    description: str
    category: str
    department: str
    priority_level: str
    priority_score: int
    sla_hours: int
    status: str
    age_hours: int
    location_key: str
    location_suffix: str
    safety_risk: bool
    urgency: str
    impact: int
    factors: tuple[tuple[str, int, str], ...]
    duplicate_of: str | None = None
    resolved_hours_ago: int | None = None
    custom_coords: tuple[float, float] | None = None


SEED_SPECS: tuple[SeedSpec, ...] = (
    # 1. Critical Exposed Live Wire
    SeedSpec(
        ticket_id="CR-2026-00001",
        title="Exposed high voltage wire sparking near school",
        description="Electric line snapped after wind and is dangling at waist height near Government School entrance. Minor sparking observed when vehicles pass.",
        category=IssueCategory.EXPOSED_WIRE.value,
        department=Department.ELECTRICITY.value,
        priority_level="Critical",
        priority_score=95,
        sla_hours=4,
        status="In Progress",
        age_hours=2,
        location_key="RS_PURAM",
        location_suffix="DB Road near Govt High School, RS Puram",
        safety_risk=True,
        urgency="Critical",
        impact=5,
        factors=(
            ("Live Wire Hazard", 20, "Dangling live cable"),
            ("School Proximity", 12, "Within 30m of primary school"),
        ),
    ),
    # 2. Pothole on busy corridor
    SeedSpec(
        ticket_id="CR-2026-00002",
        title="Severe crater pothole on Avinashi Road flyover descent",
        description="Deep 1.5 foot pothole right at the flyover ramp. Two wheelers skidding during night hours. High risk of fatal collision.",
        category=IssueCategory.POTHOLE.value,
        department=Department.ROADS.value,
        priority_level="High",
        priority_score=78,
        sla_hours=24,
        status="Reported",
        age_hours=5,
        location_key="AVINASHI_ROAD",
        location_suffix="Avinashi Road near Lakshmi Mills",
        safety_risk=True,
        urgency="High",
        impact=4,
        factors=(
            ("Major Arterial Transit", 10, "High speed vehicular corridor"),
            ("Accident Risk", 15, "Two-wheelers losing balance"),
        ),
    ),
    # 3. Overflowing garbage
    SeedSpec(
        ticket_id="CR-2026-00003",
        title="Community garbage bin overflowing across pedestrian sidewalk",
        description="Waste has spilled onto the road for 4 days. Strong foul stench, stray cows gathering and blocking pedestrian passage.",
        category=IssueCategory.GARBAGE.value,
        department=Department.SOLID_WASTE.value,
        priority_level="Medium",
        priority_score=52,
        sla_hours=48,
        status="In Progress",
        age_hours=26,
        location_key="GANDHIPURAM",
        location_suffix="Crosscut Road, Gandhipuram",
        safety_risk=False,
        urgency="Medium",
        impact=3,
        factors=(
            ("Sanitation Risk", 10, "Public health concern"),
            ("Aging", 6, "3 days uncollected"),
        ),
    ),
    # 4. Water main pipeline leak
    SeedSpec(
        ticket_id="CR-2026-00004",
        title="Drinking water main line bursting and flooding street",
        description="Siruvani drinking water supply pipeline ruptured. Gallons of clean water gushing onto the street causing road subsidence.",
        category=IssueCategory.WATER_LEAK.value,
        department=Department.WATER_SEWAGE.value,
        priority_level="Critical",
        priority_score=85,
        sla_hours=8,
        status="In Progress",
        age_hours=4,
        location_key="SAIBABA_COLONY",
        location_suffix="Alagesan Road, Saibaba Colony",
        safety_risk=True,
        urgency="Critical",
        impact=4,
        factors=(
            ("Drinking Water Contamination/Loss", 15, "Potable water infrastructure breach"),
        ),
    ),
    # 5. Damaged street light
    SeedSpec(
        ticket_id="CR-2026-00005",
        title="Series of 5 streetlights dark creating pitch black junction",
        description="Entire stretch of 5 sodium streetlights non-operational for a week. Multiple senior citizens unable to cross safely.",
        category=IssueCategory.STREETLIGHT.value,
        department=Department.ELECTRICITY.value,
        priority_level="Medium",
        priority_score=45,
        sla_hours=48,
        status="Reported",
        age_hours=18,
        location_key="SINGANALLUR",
        location_suffix="Trichy Road, Singanallur",
        safety_risk=False,
        urgency="Medium",
        impact=3,
        factors=(
            ("Pedestrian Safety", 8, "Dark corridor during peak commute"),
        ),
    ),
    # 6. Sewage overflow
    SeedSpec(
        ticket_id="CR-2026-00006",
        title="Black sewage water regurgitating from stormwater drain",
        description="Choked underground drainage spilling contaminated blackwater right in front of vegetable market. Extreme stench and hygiene hazard.",
        category=IssueCategory.SEWAGE_OVERFLOW.value,
        department=Department.WATER_SEWAGE.value,
        priority_level="High",
        priority_score=75,
        sla_hours=24,
        status="Reported",
        age_hours=8,
        location_key="TOWN_HALL",
        location_suffix="Opposite Big Bazaar Street, Town Hall",
        safety_risk=True,
        urgency="High",
        impact=4,
        factors=(
            ("Biological Health Hazard", 15, "Contamination adjacent to fresh produce market"),
        ),
    ),
    # 7. Stray dog pack
    SeedSpec(
        ticket_id="CR-2026-00007",
        title="Aggressive pack of stray dogs chasing night commuters",
        description="Pack of 7 unsterilized dogs lunging at evening joggers and delivery riders near IT corridor junction.",
        category=IssueCategory.STRAY_ANIMALS.value,
        department=Department.ANIMAL_CONTROL.value,
        priority_level="Medium",
        priority_score=50,
        sla_hours=48,
        status="In Progress",
        age_hours=30,
        location_key="SARAVANAMPATTI",
        location_suffix="Near IT Tech Park, Saravanampatti",
        safety_risk=True,
        urgency="Medium",
        impact=3,
        factors=(
            ("Bite Risk", 10, "Aggressive territorial behavior reported"),
        ),
    ),
    # 8. Illegal construction debris dumping
    SeedSpec(
        ticket_id="CR-2026-00008",
        title="Truckload of demolition concrete dumped overnight on vacant lot",
        description="Unauthorized tipping of concrete blocks and crushed tiles blocking access path to local park.",
        category=IssueCategory.ILLEGAL_DUMPING.value,
        department=Department.SOLID_WASTE.value,
        priority_level="Low",
        priority_score=32,
        sla_hours=72,
        status="Reported",
        age_hours=12,
        location_key="RAMNAGAR",
        location_suffix="Siddhapudur, Ramnagar",
        safety_risk=False,
        urgency="Low",
        impact=2,
        factors=(
            ("Obstruction", 5, "Park boundary encroachment"),
        ),
    ),
    # 9. Resolved pothole
    SeedSpec(
        ticket_id="CR-2026-00009",
        title="Pothole filled with cold asphalt mix",
        description="Medium pothole repaired by emergency ward patch team after heavy rain.",
        category=IssueCategory.POTHOLE.value,
        department=Department.ROADS.value,
        priority_level="High",
        priority_score=68,
        sla_hours=24,
        status="Resolved",
        age_hours=40,
        location_key="RS_PURAM",
        location_suffix="Diwan Bahadur Road, RS Puram",
        safety_risk=False,
        urgency="High",
        impact=3,
        factors=(
            ("Rapid Response", 10, "Restored ahead of peak commute"),
        ),
        resolved_hours_ago=16,
    ),
    # 10. Resolved streetlight
    SeedSpec(
        ticket_id="CR-2026-00010",
        title="LED fixture replaced on Ukkadam lake bund road",
        description="Blown fuse replaced and wiring secured with waterproof sleeve by municipal electrical team.",
        category=IssueCategory.STREETLIGHT.value,
        department=Department.ELECTRICITY.value,
        priority_level="Low",
        priority_score=28,
        sla_hours=72,
        status="Resolved",
        age_hours=50,
        location_key="UKKADAM",
        location_suffix="Ukkadam Bypass Road",
        safety_risk=False,
        urgency="Low",
        impact=2,
        factors=(
            ("Routine Maintenance", 5, "Flickering lamp fixed"),
        ),
        resolved_hours_ago=20,
    ),
    # 11. Noise complaint
    SeedSpec(
        ticket_id="CR-2026-00011",
        title="Industrial generator operating past midnight in residential zone",
        description="High decibel unshielded diesel generator disturbing sleep of surrounding residential apartments.",
        category=IssueCategory.NOISE.value,
        department=Department.ENVIRONMENTAL_SAFETY.value,
        priority_level="Low",
        priority_score=30,
        sla_hours=72,
        status="Reported",
        age_hours=15,
        location_key="PEELAMEDU",
        location_suffix="NKR Layout, Peelamedu",
        safety_risk=False,
        urgency="Low",
        impact=2,
        factors=(
            ("Noise Limits", 6, "Residential night zoning violation"),
        ),
    ),
    # 12. Resolved garbage clearing
    SeedSpec(
        ticket_id="CR-2026-00012",
        title="Bulk green waste cleared post cyclone trimming",
        description="Fallen tree branches and pruning debris cleared by automated compactor truck.",
        category=IssueCategory.GARBAGE.value,
        department=Department.SOLID_WASTE.value,
        priority_level="Medium",
        priority_score=42,
        sla_hours=48,
        status="Resolved",
        age_hours=36,
        location_key="GANDHIPURAM",
        location_suffix="100 Feet Road, Gandhipuram",
        safety_risk=False,
        urgency="Medium",
        impact=3,
        factors=(
            ("Transit Clearance", 8, "Bus lane obstruction removed"),
        ),
        resolved_hours_ago=12,
    ),
    # 13. Duplicate issue
    SeedSpec(
        ticket_id="CR-2026-00013",
        title="Water gushing out from pipe near Alagesan Road",
        description="Clean water pipe broken in Saibaba colony road near bakery. High flow.",
        category=IssueCategory.WATER_LEAK.value,
        department=Department.WATER_SEWAGE.value,
        priority_level="Critical",
        priority_score=82,
        sla_hours=8,
        status="Duplicate",
        age_hours=3,
        location_key="SAIBABA_COLONY",
        location_suffix="Alagesan Road, Saibaba Colony",
        safety_risk=True,
        urgency="Critical",
        impact=4,
        factors=(
            ("Correlated Issue", 10, "Merged with master incident CR-2026-00004"),
        ),
        duplicate_of="CR-2026-00004",
        custom_coords=(11.0290, 76.9460),
    ),
    # 14. Multilingual Hindi report (Resolved)
    SeedSpec(
        ticket_id="CR-2026-00014",
        title="सड़क पर गहरा गड्ढा पानी भरा हुआ (Waterlogged road pothole)",
        description="सड़क के बीच में बहुत बड़ा गड्ढा है जिसमें गंदा पानी भर गया है। गाड़ियां फंस रही हैं। (Large pothole in middle of road filled with water. Vehicles getting stuck.)",
        category=IssueCategory.POTHOLE.value,
        department=Department.ROADS.value,
        priority_level="High",
        priority_score=70,
        sla_hours=24,
        status="Resolved",
        age_hours=48,
        location_key="TOWN_HALL",
        location_suffix="Opposite Railway Station",
        safety_risk=True,
        urgency="High",
        impact=4,
        factors=(
            ("Railway Transit Traffic", 12, "Transit station access point"),
        ),
        resolved_hours_ago=24,
    ),
    # 15. Multilingual Tamil report (In Progress)
    SeedSpec(
        ticket_id="CR-2026-00015",
        title="குடிநீர் குழாய் உடைப்பு - தண்ணீர் வீணாகிறது (Drinking water leakage)",
        description="மெயின் ரோட்டில் பெரிய தண்ணீர் குழாய் உடைந்து ரோடே வெள்ளமாக உள்ளது. உடனடியாக சரி செய்யவும். (Main road water pipe burst and road is flooded. Fix immediately.)",
        category=IssueCategory.WATER_LEAK.value,
        department=Department.WATER_SEWAGE.value,
        priority_level="Critical",
        priority_score=88,
        sla_hours=8,
        status="In Progress",
        age_hours=6,
        location_key="PEELAMEDU",
        location_suffix="Peelamedu Main Road",
        safety_risk=True,
        urgency="Critical",
        impact=5,
        factors=(
            ("Drinking Water Waste", 15, "Major municipal pipeline breach"),
        ),
    ),
)
