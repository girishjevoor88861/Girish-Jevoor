"""
CivicAI - Comprehensive Demo Data Generator
Seeds 50+ realistic fictional complaints, 10 deliberate duplicates, 5 critical safety hazards,
3 geographic clusters, 7 departments, 8 field officers, complete status timelines, and audit logs.
"""

import random
import json
from datetime import datetime, timedelta
from backend.database import get_db_connection, init_db
from backend.auth import hash_password
from backend.ai_engine import (
    classify_complaint_text,
    calculate_priority_score,
    generate_action_brief,
    detect_duplicates,
    analyze_hotspots,
    haversine_distance_meters
)

# Realistic SVG Image representations stored as data-URI or clean URLs
DEFAULT_REPORT_IMG = "/uploads/complaint_sample.svg"
DEFAULT_BEFORE_IMG = "/uploads/before_work.svg"
DEFAULT_AFTER_IMG = "/uploads/after_work.svg"

DEPARTMENTS_DATA = [
    {
        "name": "Roads and Infrastructure",
        "code": "ROADS",
        "description": "Maintenance of arterial roads, asphalt resurfacing, bridges, pavements, and traffic signage.",
        "contact_email": "roads@civicai.gov",
        "head_name": "Chief Eng. Robert Vance",
        "sla_hours": 36
    },
    {
        "name": "Drainage and Water Management",
        "code": "DRAIN",
        "description": "Stormwater drains, monsoon flood mitigation, sewage network inspection and maintenance.",
        "contact_email": "drainage@civicai.gov",
        "head_name": "Dir. Anita Desai",
        "sla_hours": 24
    },
    {
        "name": "Sanitation",
        "code": "SAN",
        "description": "Solid waste management, garbage clearance, debris cleanup, and public hygiene enforcement.",
        "contact_email": "sanitation@civicai.gov",
        "head_name": "Sup. Marcus Chen",
        "sla_hours": 24
    },
    {
        "name": "Electricity and Streetlights",
        "code": "ELEC",
        "description": "Grid power inspection, public lighting poles, transformer servicing, and electrical hazard safety.",
        "contact_email": "electricity@civicai.gov",
        "head_name": "Eng. Vikram Malhotra",
        "sla_hours": 18
    },
    {
        "name": "Public Safety",
        "code": "SAFE",
        "description": "Emergency hazard mitigation, manhole covers, structural safety, tree removal, and perimeter security.",
        "contact_email": "safety@civicai.gov",
        "head_name": "Capt. Linda Sterling",
        "sla_hours": 12
    },
    {
        "name": "Water Supply",
        "code": "WATER",
        "description": "Municipal drinking water distribution, pipeline leak repairs, and water quality testing.",
        "contact_email": "water@civicai.gov",
        "head_name": "Dir. Tariq Mansoor",
        "sla_hours": 24
    },
    {
        "name": "Parks and Public Spaces",
        "code": "PARKS",
        "description": "Urban greenery, public parks maintenance, recreation equipment safety, and tree pruning.",
        "contact_email": "parks@civicai.gov",
        "head_name": "Curator Maya Patel",
        "sla_hours": 72
    }
]

# 3 Primary Geographic Hotspot Centers (Metro City)
# Cluster A: Downtown Market Hub (Lat: 12.9716, Lng: 77.5946)
# Cluster B: North Tech Corridor & Highway (Lat: 12.9850, Lng: 77.6100)
# Cluster C: Green Valley Residential Ward (Lat: 12.9550, Lng: 77.5800)

RAW_COMPLAINTS_SEED = [
    # 5 Critical Safety Hazards (Guaranteed Priority >= 85)
    {
        "title": "Open manhole on pedestrian crosswalk near St. Jude School",
        "description": "Deep open manhole without cover or warning barrier directly on the pedestrian pathway right outside school gates. Immense danger of children falling in. Immediate emergency intervention required.",
        "category": "Public Safety",
        "subcategory": "Open & Missing Manhole",
        "ward": "Ward 12 - Downtown",
        "address": "45 Cathedral Cross Road, near St. Jude School",
        "lat": 12.9721,
        "lng": 77.5952,
        "status": "in_progress",
        "dept_code": "SAFE",
        "days_ago": 1
    },
    {
        "title": "Sparking high-voltage electric wire hanging over bus shelter",
        "description": "Overhead high voltage power line snapped and is sparking intensely against the metal roof of City Bus Stop 4. Commuters running away in panic. High electrocution hazard.",
        "category": "Electricity & Streetlights",
        "subcategory": "Sparking & Dangerous Wires",
        "ward": "Ward 07 - Tech Hub",
        "address": "Opposite Cyber Heights Tower, Outer Ring Road",
        "lat": 12.9855,
        "lng": 77.6108,
        "status": "assigned",
        "dept_code": "ELEC",
        "days_ago": 0
    },
    {
        "title": "Main drinking water pipeline burst causing road cave-in",
        "description": "High pressure municipal main pipeline ruptured under asphalt. Clean water gushing at enormous pressure, undermining the roadbed. Surface asphalt has collapsed into a deep sinkhole.",
        "category": "Water Supply",
        "subcategory": "Main Pipeline Burst",
        "ward": "Ward 15 - West Valley",
        "address": "128 West Boulevard, near Government Hospital",
        "lat": 12.9610,
        "lng": 77.5750,
        "status": "in_progress",
        "dept_code": "WATER",
        "days_ago": 2
    },
    {
        "title": "Massive fallen Banyan tree crushing power lines and blocking hospital road",
        "description": "Huge storm blew down ancient tree completely blocking emergency ambulance entrance to Civic General Hospital. Live power wires entangled in branches.",
        "category": "Public Safety",
        "subcategory": "Fallen Trees & Heavy Branches",
        "ward": "Ward 12 - Downtown",
        "address": "Hospital Road entrance, Civic Center",
        "lat": 12.9730,
        "lng": 77.5935,
        "status": "resolved",
        "dept_code": "SAFE",
        "days_ago": 3
    },
    {
        "title": "Severe gas odor leaking from open culvert excavation",
        "description": "Strong combustible gas smell emerging from open pipeline trench near residential apartment block. Multiple residents reporting dizziness. Urgent fire hazard.",
        "category": "Public Safety",
        "subcategory": "Immediate Fire / Chemical Hazard",
        "ward": "Ward 07 - Tech Hub",
        "address": "Plot 88, 5th Main, Silicon Layout",
        "lat": 12.9862,
        "lng": 77.6095,
        "status": "in_progress",
        "dept_code": "SAFE",
        "days_ago": 1
    },

    # Cluster A: Downtown Market Drainage & Waterlogging (Includes 4 deliberate duplicates)
    {
        "title": "Severe waterlogging in Central Market Road after rainfall",
        "description": "Knee-deep stagnant water flooding the entire Central Market commercial stretch. Stormwater grates are completely clogged with silt. Shopkeepers unable to open.",
        "category": "Drainage & Water Management",
        "subcategory": "Severe Waterlogging",
        "ward": "Ward 12 - Downtown",
        "address": "Central Market Road, Block A, Commercial Center",
        "lat": 12.9718,
        "lng": 77.5948,
        "status": "under_review",
        "dept_code": "DRAIN",
        "days_ago": 2
    },
    # Duplicate 1 of above
    {
        "title": "Heavy flooding and clogged drain in Central Market Road",
        "description": "Water accumulated up to two feet near Block A Central Market. Storm drains are blocked and overflowing onto pedestrian sidewalk.",
        "category": "Drainage & Water Management",
        "subcategory": "Severe Waterlogging",
        "ward": "Ward 12 - Downtown",
        "address": "Central Market Road, near Block A Grocery Alley",
        "lat": 12.9719,
        "lng": 77.5949,
        "status": "submitted",
        "dept_code": "DRAIN",
        "days_ago": 1
    },
    # Duplicate 2 of above
    {
        "title": "Stagnant stormwater submerging Central Market shops",
        "description": "Entire street is under water. Vehicles cannot pass Central Market commercial road due to deep water stagnation. Drain choke.",
        "category": "Drainage & Water Management",
        "subcategory": "Severe Waterlogging",
        "ward": "Ward 12 - Downtown",
        "address": "Shop 14, Central Market Avenue",
        "lat": 12.9717,
        "lng": 77.5947,
        "status": "submitted",
        "dept_code": "DRAIN",
        "days_ago": 1
    },
    # Duplicate 3 of above
    {
        "title": "Stormwater grates blocked causing waterlogging Central Market",
        "description": "Water logging on Central Market main road. Storm drain grates blocked with plastic and debris.",
        "category": "Drainage & Water Management",
        "subcategory": "Blocked Storm Drains",
        "ward": "Ward 12 - Downtown",
        "address": "Central Market Road junction",
        "lat": 12.9720,
        "lng": 77.5946,
        "status": "submitted",
        "dept_code": "DRAIN",
        "days_ago": 0
    },

    # Cluster B: Tech Corridor Roads & Potholes (Includes 3 deliberate duplicates)
    {
        "title": "Dangerous series of deep potholes near Tech Park Main Gate",
        "description": "Cluster of four large deep craters in the tarmac right at the entrance of Tech Park. Two motorcycle riders skidded and injured yesterday.",
        "category": "Roads & Infrastructure",
        "subcategory": "Potholes & Surface Damage",
        "ward": "Ward 07 - Tech Hub",
        "address": "Innovation Way, Gate 2, Tech Park Corridor",
        "lat": 12.9848,
        "lng": 77.6102,
        "status": "assigned",
        "dept_code": "ROADS",
        "days_ago": 4
    },
    # Duplicate 4 of above
    {
        "title": "Deep crater pothole outside Tech Park Gate 2",
        "description": "Huge pothole breaking vehicle axles at Tech Park entrance gate 2 on Innovation Way. Needs immediate asphalt patch.",
        "category": "Roads & Infrastructure",
        "subcategory": "Potholes & Surface Damage",
        "ward": "Ward 07 - Tech Hub",
        "address": "Innovation Way Gate 2, Tech Park",
        "lat": 12.9849,
        "lng": 77.6103,
        "status": "submitted",
        "dept_code": "ROADS",
        "days_ago": 3
    },
    # Duplicate 5 of above
    {
        "title": "Multiple asphalt craters causing accidents near Tech Park entrance",
        "description": "Big potholes on road leading into Tech Park. Heavy traffic jamming and two-wheelers losing balance.",
        "category": "Roads & Infrastructure",
        "subcategory": "Potholes & Surface Damage",
        "ward": "Ward 07 - Tech Hub",
        "address": "Innovation Way, Outer Ring Road side",
        "lat": 12.9847,
        "lng": 77.6101,
        "status": "under_review",
        "dept_code": "ROADS",
        "days_ago": 2
    },

    # Cluster C: Green Valley Garbage Dumps (Includes 3 deliberate duplicates)
    {
        "title": "Massive uncollected garbage dump overflowing into residential road",
        "description": "Municipal waste collection truck has not visited in 8 days. Huge pile of rotting household trash, stray animals scavenging, unbearable stench.",
        "category": "Sanitation",
        "subcategory": "Uncollected Garbage",
        "ward": "Ward 15 - West Valley",
        "address": "Corner of 4th Cross & Maple Avenue, Green Valley",
        "lat": 12.9554,
        "lng": 77.5802,
        "status": "assigned",
        "dept_code": "SAN",
        "days_ago": 3
    },
    # Duplicate 6 of above
    {
        "title": "Rotting trash pile not collected for over a week at Maple Avenue",
        "description": "Garbage dump is overflowing on 4th cross Maple avenue. Stench and hygiene hazard for neighboring houses.",
        "category": "Sanitation",
        "subcategory": "Uncollected Garbage",
        "ward": "Ward 15 - West Valley",
        "address": "4th Cross, Green Valley Residential Layout",
        "lat": 12.9555,
        "lng": 77.5803,
        "status": "submitted",
        "dept_code": "SAN",
        "days_ago": 2
    },
    # Duplicate 7 of above
    {
        "title": "Overflowing waste bin and animal scavenging on Maple Avenue",
        "description": "Dustbin broken and garbage strewn across road near Maple Ave corner. Needs immediate compactor truck clearance.",
        "category": "Sanitation",
        "subcategory": "Overflowing Public Dustbins",
        "ward": "Ward 15 - West Valley",
        "address": "Maple Avenue, corner junction, Ward 15",
        "lat": 12.9553,
        "lng": 77.5801,
        "status": "submitted",
        "dept_code": "SAN",
        "days_ago": 1
    },

    # Deliberate Duplicate Pair 8 & 9: Streetlights in North Avenue
    {
        "title": "Entire row of streetlights blacked out on North Boulevard",
        "description": "All 14 streetlight poles completely dark from Metro Station to North Flyover for past three nights. Rising mugging concerns.",
        "category": "Electricity & Streetlights",
        "subcategory": "Streetlight Outage",
        "ward": "Ward 07 - Tech Hub",
        "address": "North Boulevard between Metro Pillar 110 to 124",
        "lat": 12.9835,
        "lng": 77.6120,
        "status": "in_progress",
        "dept_code": "ELEC",
        "days_ago": 3
    },
    {
        "title": "Dark streetlights stretch from metro station to North Flyover",
        "description": "Street lamps not turning on in evening. Total blackout on North Boulevard, creating very unsafe conditions for women walkers.",
        "category": "Electricity & Streetlights",
        "subcategory": "Streetlight Outage",
        "ward": "Ward 07 - Tech Hub",
        "address": "North Boulevard, near Metro Pillar 115",
        "lat": 12.9836,
        "lng": 77.6122,
        "status": "submitted",
        "dept_code": "ELEC",
        "days_ago": 2
    },

    # Deliberate Duplicate Pair 10: Broken Children Playground Slide
    {
        "title": "Broken metal slide with sharp jagged edges at Harmony Park",
        "description": "Children's playground spiral slide has rusted through with sharp exposed iron edges. One toddler suffered a cut today. Needs immediate cordon.",
        "category": "Parks & Public Spaces",
        "subcategory": "Broken Playground Equipment",
        "ward": "Ward 15 - West Valley",
        "address": "Harmony Community Park, Children Play Section",
        "lat": 12.9565,
        "lng": 77.5815,
        "status": "resolved",
        "dept_code": "PARKS",
        "days_ago": 6
    },
    {
        "title": "Hazardous rusted slide in Harmony Park children section",
        "description": "Play equipment slide broken and sharp metal sticking out. Dangerous for small children at Harmony Park.",
        "category": "Parks & Public Spaces",
        "subcategory": "Broken Playground Equipment",
        "ward": "Ward 15 - West Valley",
        "address": "Harmony Park, Ward 15 play area",
        "lat": 12.9566,
        "lng": 77.5816,
        "status": "resolved",
        "dept_code": "PARKS",
        "days_ago": 5
    }
]

# Additional 35+ complaints across various categories, wards, and statuses
ADDITIONAL_COMPLAINTS_TEMPLATES = [
    # Roads & Infrastructure
    ("Damaged pedestrian footpath with missing concrete tiles", "Sidewalk paving stones loose and fractured over a 30m stretch. Elderly pedestrians constantly stumbling.", "Roads & Infrastructure", "Damaged Sidewalk & Footpaths", "ROADS", "high", "resolved"),
    ("Broken central road divider with exposed iron rods", "Central median broken by vehicle collision. Sharp rebar rods protruding into driving lane.", "Roads & Infrastructure", "Road Dividers & Guardrails", "ROADS", "high", "in_progress"),
    ("Traffic signal stuck constantly on red at busy intersection", "Automatic traffic light controller malfunctioning. Constant red signal creating massive 2km gridlock.", "Roads & Infrastructure", "Traffic Signals & Signage", "ROADS", "high", "resolved"),
    ("Bridge expansion joint rubber seal detached and rattling", "Expansion joint on flyover ramp loose, creating severe bump for speeding vehicles.", "Roads & Infrastructure", "Bridges & Flyovers", "ROADS", "medium", "assigned"),
    ("Severe uneven asphalt surface after private utility trenching", "Contractor left road unpaved after fiber-optic pipe laying. Mud and loose gravel everywhere.", "Roads & Infrastructure", "Potholes & Surface Damage", "ROADS", "medium", "under_review"),
    
    # Drainage & Water Management
    ("Sewage line overflow into residential front yards", "Underground drainage backing up and bubbling out of inspection chambers into private driveways. Extreme foul odor.", "Drainage & Water Management", "Sewage Overflow", "DRAIN", "high", "resolved"),
    ("Stormwater culvert choked with plastic sacks and silt", "Pre-monsoon check revealed main storm canal blocked under railway bridge. Risk of flash flooding.", "Drainage & Water Management", "Canal & Culvert Blockage", "DRAIN", "medium", "assigned"),
    ("Broken concrete drain cover along commercial market lane", "Precast slab covering roadside gutter has cracked in half. Wheelchair access impeded.", "Drainage & Water Management", "Blocked Storm Drains", "DRAIN", "medium", "in_progress"),
    ("Stagnant green water pool breeding mosquitoes near clinic", "Water accumulation from broken storm drainage creating active dengue and mosquito breeding hotspot.", "Drainage & Water Management", "Severe Waterlogging", "DRAIN", "high", "resolved"),
    ("Underground sewer pipe collapsed causing road depression", "Sewer line leak underneath asphalt causing sunken surface of about 1 meter diameter.", "Drainage & Water Management", "Sewage Overflow", "DRAIN", "high", "under_review"),

    # Sanitation
    ("Illegal commercial construction debris dumped on open public plot", "Truckloads of broken concrete and plaster discarded on public vacant corner lot.", "Sanitation", "Illegal Dumping Site", "SAN", "medium", "resolved"),
    ("Decaying dead canine carcass near bus terminal", "Deceased stray dog lying on roadside curb near pedestrian foot overbridge. Urgent removal needed.", "Sanitation", "Dead Animal Carcass", "SAN", "high", "resolved"),
    ("Unsegregated bio-waste discarded behind fish market", "Rotting organic waste dumped in open barrels attracting vultures and flies.", "Sanitation", "Uncollected Garbage", "SAN", "medium", "in_progress"),
    ("Litter bins vandalized and burnt in downtown plaza", "Three stainless steel municipal trash receptacles set on fire and melted.", "Sanitation", "Overflowing Public Dustbins", "SAN", "low", "assigned"),
    ("Persistent open garbage burning in empty municipal land", "Unauthorized scavengers burning plastic wire insulation creating toxic thick black smoke.", "Sanitation", "Illegal Dumping Site", "SAN", "high", "resolved"),

    # Electricity & Streetlights
    ("Tilted street lighting pole threatening to collapse onto roadway", "Light post hit by truck is leaning at 45 degree angle. Supported only by overhead tension wires.", "Electricity & Streetlights", "Damaged Light Pole", "ELEC", "critical", "resolved"),
    ("Flickering halogen streetlight causing strobe effect near corner", "Streetlamp pulsing continuously all night, causing headache and driving hazard.", "Electricity & Streetlights", "Streetlight Outage", "ELEC", "low", "closed"),
    ("Public park perimeter high-mast floodlights completely inactive", "Central 30-meter high-mast lighting tower not functioning, leaving entire public park pitch dark.", "Electricity & Streetlights", "Streetlight Outage", "ELEC", "medium", "resolved"),
    ("Open transformer fence door with accessible live fuses", "Security chain link gate to distribution transformer is unlatched. Direct access for curious children.", "Electricity & Streetlights", "Sparking & Dangerous Wires", "ELEC", "critical", "resolved"),
    ("Transformer oil leaking profusely onto sidewalk", "Substation transformer dripping cooling oil onto public footpath, creating slippery puddle.", "Electricity & Streetlights", "Transformer Issues", "ELEC", "medium", "in_progress"),

    # Public Safety
    ("Cracked retaining wall bulging towards busy sidewalk", "Masonry retaining wall behind bus terminal shows 2-inch wide vertical crack and noticeable outward bulge.", "Public Safety", "Structural Hazard & Collapsing Walls", "SAFE", "critical", "in_progress"),
    ("Large dry tree limb hanging dangerously over kindergarten roof", "Massive dead branch dangling by thin bark over preschool play yard.", "Public Safety", "Fallen Trees & Heavy Branches", "SAFE", "high", "resolved"),
    ("Missing sewer grating on rain gutter along cycle track", "Wide drain opening right in middle of dedicated bicycle path. Severe fall danger.", "Public Safety", "Open & Missing Manhole", "SAFE", "high", "resolved"),
    ("Deep unbarricaded trench dug by telecom contractor", "Six-foot deep trench left completely unlit and without warning tape along poorly lit street.", "Public Safety", "Structural Hazard & Collapsing Walls", "SAFE", "high", "assigned"),

    # Water Supply
    ("Heavily contaminated muddy brown water coming from taps", "Water supply contaminated with soil and sewage odor. Residents cannot drink or cook.", "Water Supply", "Contaminated Drinking Water", "WATER", "critical", "resolved"),
    ("Public drinking water fountain broken and leaking continuously", "Community water kiosk tap head sheared off, wasting thousands of liters per hour.", "Water Supply", "Damaged Water Meter / Valve", "WATER", "medium", "resolved"),
    ("Zero water pressure for 4 consecutive days in Sector 9", "Entire neighborhood of 400 families receiving no water through municipal supply lines.", "Water Supply", "Water Supply Disruption", "WATER", "high", "in_progress"),
    ("Ruptured distribution line flooding basement parking", "Sub-main pipe cracked under driveway, water entering basement elevator shafts.", "Water Supply", "Main Pipeline Burst", "WATER", "high", "resolved"),
    ("Underground valve box cover broken and flooding street", "Water control sluice valve chamber leaking pressurized water onto main roadway.", "Water Supply", "Damaged Water Meter / Valve", "WATER", "medium", "closed"),

    # Parks & Public Spaces
    ("Vandalized public park benches and broken stone tables", "Three granite sitting benches overturned and smashed in Central Rose Garden.", "Parks & Public Spaces", "Damaged Park Amenities", "PARKS", "low", "resolved"),
    ("Dense overgrown wild weeds obscuring walking track", "Waist-high thorny shrubs encroaching onto jogging trail, attracting stray snakes.", "Parks & Public Spaces", "Overgrown Vegetation & Weeds", "PARKS", "medium", "in_progress"),
    ("Broken infant swings with snapped chain links", "Toddler swing set chains snapped; exposed rusty metal hanging in neighborhood park.", "Parks & Public Spaces", "Broken Playground Equipment", "PARKS", "medium", "assigned"),
    ("Park boundary fencing stolen, cattle entering garden", "Metal perimeter fence panels removed overnight, stray cows destroying flowerbeds.", "Parks & Public Spaces", "Damaged Park Amenities", "PARKS", "low", "closed"),
    ("Public park decorative fountain water stagnant and foul", "Fountain motor seized, pool filled with slimy algae and mosquito larvae.", "Parks & Public Spaces", "Damaged Park Amenities", "PARKS", "low", "resolved"),
    ("Jogging track asphalt disintegrated by tree roots", "Tree roots broke through rubberized jogging path, causing multiple running injuries.", "Parks & Public Spaces", "Damaged Park Amenities", "PARKS", "medium", "under_review")
]

OFFICERS_SEED = [
    {"name": "Officer John Reynolds", "email": "officer.john@civicai.gov", "dept": "ROADS", "badge": "ROADS-901", "rank": "Senior Highway Inspector"},
    {"name": "Officer Sarah Jenkins", "email": "officer.sarah@civicai.gov", "dept": "DRAIN", "badge": "DRAIN-404", "rank": "Drainage Operations Lead"},
    {"name": "Officer Michael Vance", "email": "officer.michael@civicai.gov", "dept": "ELEC", "badge": "ELEC-220", "rank": "Chief Grid Safety Officer"},
    {"name": "Officer Elena Rostova", "email": "officer.elena@civicai.gov", "dept": "SAN", "badge": "SAN-118", "rank": "Sanitation Field Marshall"},
    {"name": "Officer Marcus Thorne", "email": "officer.marcus@civicai.gov", "dept": "SAFE", "badge": "SAFE-550", "rank": "Rapid Hazard Response Lead"},
    {"name": "Officer Priya Nair", "email": "officer.priya@civicai.gov", "dept": "WATER", "badge": "WATER-330", "rank": "Hydraulic Field Engineer"},
    {"name": "Officer David Zhao", "email": "officer.david@civicai.gov", "dept": "PARKS", "badge": "PARKS-712", "rank": "Parks & Arboreal Supervisor"},
    {"name": "Officer Rachel Green", "email": "officer.rachel@civicai.gov", "dept": "ROADS", "badge": "ROADS-902", "rank": "Pavement Maintenance Inspector"}
]

def seed_database(force=True):
    """Populates the database with realistic civic data satisfying all 50+ complaint requirements."""
    init_db(force_recreate=force)
    conn = get_db_connection()
    cursor = conn.cursor()

    print("Seeding CivicAI Departments...")
    dept_map = {} # code -> dept_id
    for d in DEPARTMENTS_DATA:
        cursor.execute("""
            INSERT INTO departments (name, code, description, contact_email, head_name, sla_hours)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (d["name"], d["code"], d["description"], d["contact_email"], d["head_name"], d["sla_hours"]))
        dept_map[d["code"]] = cursor.lastrowid
        dept_map[d["name"]] = cursor.lastrowid

    print("Seeding Administrative and Citizen Users...")
    # Admin User
    admin_pw = hash_password("Admin@1234")
    cursor.execute("""
        INSERT INTO users (email, password_hash, role, full_name, phone)
        VALUES ('admin@civicai.gov', ?, 'admin', 'Commissioner Sarah Mitchell', '+1 (555) 019-2834')
    """, (admin_pw,))
    admin_id = cursor.lastrowid
    cursor.execute("INSERT INTO profiles (user_id, bio, badge_number) VALUES (?, 'CivicAI Lead Municipal Administrator', 'MUNICIPAL-HQ-01')", (admin_id,))

    # Citizen Users
    citizen_pw = hash_password("Citizen@1234")
    citizens = [
        {"name": "Alice Morgan", "email": "citizen.alice@example.com", "phone": "+1 (555) 782-9901"},
        {"name": "Bob Henderson", "email": "citizen.bob@example.com", "phone": "+1 (555) 441-2839"},
        {"name": "Carol Williams", "email": "citizen.carol@example.com", "phone": "+1 (555) 890-1234"},
        {"name": "Daniel Kim", "email": "citizen.daniel@example.com", "phone": "+1 (555) 321-9876"},
        {"name": "Emma Thompson", "email": "citizen.emma@example.com", "phone": "+1 (555) 654-7890"}
    ]
    citizen_ids = []
    for c in citizens:
        cursor.execute("""
            INSERT INTO users (email, password_hash, role, full_name, phone)
            VALUES (?, ?, 'citizen', ?, ?)
        """, (c["email"], citizen_pw, c["name"], c["phone"]))
        cid = cursor.lastrowid
        citizen_ids.append(cid)
        cursor.execute("INSERT INTO profiles (user_id, address) VALUES (?, 'Metro City Resident')", (cid,))

    print("Seeding Field Officers...")
    officer_pw = hash_password("Officer@1234")
    officer_ids = []
    officer_dept_map = {} # dept_id -> list of officer_ids
    for off in OFFICERS_SEED:
        dept_id = dept_map[off["dept"]]
        cursor.execute("""
            INSERT INTO users (email, password_hash, role, full_name, phone)
            VALUES (?, ?, 'officer', ?, '+1 (555) 900-1122')
        """, (off["email"], officer_pw, off["name"]))
        u_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO officers (user_id, department_id, badge_number, rank, status)
            VALUES (?, ?, ?, ?, 'available')
        """, (u_id, dept_id, off["badge"], off["rank"]))
        officer_rec_id = cursor.lastrowid
        officer_ids.append(officer_rec_id)
        
        if dept_id not in officer_dept_map:
            officer_dept_map[dept_id] = []
        officer_dept_map[dept_id].append(officer_rec_id)

        cursor.execute("INSERT INTO profiles (user_id, badge_number, department_id) VALUES (?, ?, ?)", (u_id, off["badge"], dept_id))

    # Update active_officers_count on departments
    for d_code, d_id in dept_map.items():
        if isinstance(d_code, str) and len(d_code) <= 5: # only codes
            cnt = len(officer_dept_map.get(d_id, []))
            cursor.execute("UPDATE departments SET active_officers_count = ? WHERE id = ?", (cnt, d_id))

    print("Assembling 50+ Complaints Dataset...")
    all_complaint_specs = list(RAW_COMPLAINTS_SEED)

    # Add templates to reach >= 52 complaints
    wards = ["Ward 12 - Downtown", "Ward 07 - Tech Hub", "Ward 15 - West Valley", "Ward 03 - Riverfront", "Ward 09 - North Industrial"]
    base_coords = [
        (12.9716, 77.5946), # Downtown
        (12.9850, 77.6100), # Tech Hub
        (12.9550, 77.5800), # West Valley
        (12.9650, 77.6050), # Riverfront
        (12.9920, 77.5850)  # North Industrial
    ]

    for idx, tpl in enumerate(ADDITIONAL_COMPLAINTS_TEMPLATES):
        title, desc, cat, subcat, dept_code, priority_hint, status = tpl
        w_idx = idx % len(wards)
        b_lat, b_lng = base_coords[w_idx]
        # Jitter slightly for geographic realism (+- 0.005)
        c_lat = round(b_lat + random.uniform(-0.006, 0.006), 6)
        c_lng = round(b_lng + random.uniform(-0.006, 0.006), 6)
        days_ago = random.randint(1, 28)

        all_complaint_specs.append({
            "title": title,
            "description": desc,
            "category": cat,
            "subcategory": subcat,
            "ward": wards[w_idx],
            "address": f"Plot {random.randint(10, 240)}, Road {random.randint(1, 15)}, {wards[w_idx]}",
            "lat": c_lat,
            "lng": c_lng,
            "status": status,
            "dept_code": dept_code,
            "days_ago": days_ago
        })

    print(f"Total complaints to seed: {len(all_complaint_specs)}")
    created_complaint_ids = []

    # Insert complaints with full AI analysis, priority scoring, location, images, and history
    for idx, item in enumerate(all_complaint_specs):
        tracking_num = f"CIV-2026-{1000 + idx}"
        user_id = random.choice(citizen_ids)
        dept_id = dept_map[item["dept_code"]]
        
        # Determine assigned officer if status >= assigned
        assigned_officer_id = None
        if item["status"] in ["assigned", "in_progress", "resolved", "closed"]:
            avail_officers = officer_dept_map.get(dept_id, officer_ids)
            assigned_officer_id = random.choice(avail_officers)

        # Dates
        now = datetime.utcnow()
        created_time = (now - timedelta(days=item["days_ago"], hours=random.randint(1, 18))).strftime("%Y-%m-%d %H:%M:%S")
        updated_time = (now - timedelta(days=max(0, item["days_ago"] - 1), hours=random.randint(1, 6))).strftime("%Y-%m-%d %H:%M:%S")
        resolved_time = updated_time if item["status"] in ["resolved", "closed"] else None

        # Run AI Classification & Priority Scoring
        ai_class = classify_complaint_text(item["title"], item["description"])
        priority_res = calculate_priority_score(
            title=item["title"],
            description=item["description"],
            category=ai_class["category"],
            lat=item["lat"],
            lng=item["lng"],
            recent_complaints_count=random.randint(1, 4)
        )

        final_priority = priority_res["priority_level"]

        # Action Brief
        action_brief = generate_action_brief(
            title=item["title"],
            location_address=item["address"],
            priority_level=final_priority,
            priority_score=priority_res["total_score"],
            related_reports_count=random.randint(1, 6),
            department=ai_class["department"],
            category=ai_class["category"],
            public_impact_desc=priority_res["factor_breakdown"]["public_impact"]["reasons"][0],
            recommended_action=priority_res["recommended_action"]
        )

        # Insert Complaint
        cursor.execute("""
            INSERT INTO complaints (
                tracking_id, user_id, title, description, category, subcategory,
                priority, status, department_id, assigned_officer_id,
                created_at, updated_at, resolved_at, public_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tracking_num, user_id, item["title"], item["description"],
            ai_class["category"], item["subcategory"], final_priority,
            item["status"], dept_id, assigned_officer_id,
            created_time, updated_time, resolved_time,
            f"Department assigned: {ai_class['department']}. Field dispatch SLA active."
        ))
        complaint_id = cursor.lastrowid
        created_complaint_ids.append(complaint_id)

        # Insert Location
        cursor.execute("""
            INSERT INTO complaint_locations (complaint_id, latitude, longitude, address, landmark, ward, postal_code)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            complaint_id, item["lat"], item["lng"], item["address"],
            f"Near landmark in {item['ward']}", item["ward"], f"5600{random.randint(10, 99)}"
        ))

        # Insert AI Analysis
        cursor.execute("""
            INSERT INTO ai_analysis (
                complaint_id, category, subcategory, department, short_summary,
                keywords, urgency, confidence, safety_score, public_impact_score,
                urgency_score, concentration_score, frequency_score, total_priority_score,
                priority_level, action_brief, human_reviewed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            complaint_id, ai_class["category"], item["subcategory"], ai_class["department"],
            ai_class["short_summary"], ai_class["keywords"], ai_class["urgency"],
            ai_class["confidence"], priority_res["safety_score"], priority_res["public_impact_score"],
            priority_res["urgency_score"], priority_res["concentration_score"], priority_res["frequency_score"],
            priority_res["total_score"], final_priority, action_brief
        ))

        # Complaint Image
        cursor.execute("""
            INSERT INTO complaint_images (complaint_id, image_url, image_type, caption, uploaded_at)
            VALUES (?, ?, 'report', 'Citizen submitted field observation photo', ?)
        """, (complaint_id, DEFAULT_REPORT_IMG, created_time))

        # Status History Timeline
        cursor.execute("""
            INSERT INTO status_history (complaint_id, previous_status, new_status, changed_by, user_role, timestamp, explanation)
            VALUES (?, NULL, 'submitted', ?, 'citizen', ?, 'Citizen submitted complaint via CivicAI Portal')
        """, (complaint_id, user_id, created_time))

        cursor.execute("""
            INSERT INTO status_history (complaint_id, previous_status, new_status, changed_by, user_role, timestamp, explanation)
            VALUES (?, 'submitted', 'ai_analyzed', ?, 'system', ?, 'AI Engine classified issue, priority evaluated, duplicate search completed')
        """, (complaint_id, admin_id, created_time))

        if item["status"] in ["under_review", "assigned", "in_progress", "resolved", "closed"]:
            cursor.execute("""
                INSERT INTO status_history (complaint_id, previous_status, new_status, changed_by, user_role, timestamp, explanation)
                VALUES (?, 'ai_analyzed', 'under_review', ?, 'admin', ?, 'Administrator reviewed AI brief and validated routing')
            """, (complaint_id, admin_id, updated_time))

        if item["status"] in ["assigned", "in_progress", "resolved", "closed"]:
            cursor.execute("""
                INSERT INTO status_history (complaint_id, previous_status, new_status, changed_by, user_role, timestamp, explanation)
                VALUES (?, 'under_review', 'assigned', ?, 'admin', ?, 'Work order assigned to field inspector')
            """, (complaint_id, admin_id, updated_time))
            # Assignment record
            cursor.execute("""
                INSERT INTO assignments (complaint_id, officer_id, assigned_by, assigned_at, status, notes)
                VALUES (?, ?, ?, ?, 'accepted', 'Proceed with field inspection and dispatch remediation equipment.')
            """, (complaint_id, assigned_officer_id, admin_id, updated_time))

        if item["status"] in ["in_progress", "resolved", "closed"]:
            cursor.execute("""
                INSERT INTO status_history (complaint_id, previous_status, new_status, changed_by, user_role, timestamp, explanation)
                VALUES (?, 'assigned', 'in_progress', ?, 'officer', ?, 'Officer arrived on-site; remediation crew active')
            """, (complaint_id, admin_id, updated_time))

        if item["status"] in ["resolved", "closed"]:
            cursor.execute("""
                INSERT INTO status_history (complaint_id, previous_status, new_status, changed_by, user_role, timestamp, explanation)
                VALUES (?, 'in_progress', 'resolved', ?, 'officer', ?, 'Remediation completed and verified with photographic evidence')
            """, (complaint_id, admin_id, resolved_time))

            # Resolution Evidence
            cursor.execute("""
                INSERT INTO resolution_evidence (
                    complaint_id, officer_id, before_image_url, after_image_url,
                    resolution_summary, equipment_used, labor_hours, resolved_at
                ) VALUES (?, ?, ?, ?, ?, 'Municipal response truck, specialized vacuum suction & asphalt compaction unit', 3.5, ?)
            """, (
                complaint_id, assigned_officer_id, DEFAULT_BEFORE_IMG, DEFAULT_AFTER_IMG,
                f"Full remediation successfully completed for '{item['title']}'. Site restored to safe operating condition.",
                resolved_time
            ))

            # Citizen Feedback
            cursor.execute("""
                INSERT INTO citizen_feedback (complaint_id, user_id, rating, comments, reopen_requested, created_at)
                VALUES (?, ?, 5, 'Issue was resolved very quickly! The before/after photo evidence was very reassuring.', 0, ?)
            """, (complaint_id, user_id, resolved_time))

        # Notifications
        cursor.execute("""
            INSERT INTO notifications (user_id, complaint_id, title, message, type, is_read, created_at)
            VALUES (?, ?, 'Complaint Received', ?, 'info', 1, ?)
        """, (user_id, complaint_id, f"Your report '{item['title']}' was recorded with tracking ID {tracking_num}.", created_time))

        if item["status"] in ["resolved", "closed"]:
            cursor.execute("""
                INSERT INTO notifications (user_id, complaint_id, title, message, type, is_read, created_at)
                VALUES (?, ?, 'Complaint Resolved!', ?, 'success', 0, ?)
            """, (user_id, complaint_id, f"Great news! Your complaint {tracking_num} has been resolved by {ai_class['department']}.", resolved_time))

    conn.commit()
    print("Complaints committed. Computing Cross-Duplicate Matches...")

    # Run Duplicate Matching on all complaints to populate duplicate_matches table
    all_complaints = cursor.execute("""
        SELECT c.id, c.title, c.description, c.category, l.latitude, l.longitude
        FROM complaints c
        JOIN complaint_locations l ON c.id = l.complaint_id
    """).fetchall()

    duplicate_pairs_found = 0
    for comp in all_complaints:
        dups = detect_duplicates(
            complaint_id=comp["id"],
            title=comp["title"],
            description=comp["description"],
            category=comp["category"],
            lat=comp["latitude"],
            lng=comp["longitude"],
            exclude_id=comp["id"]
        )
        for d in dups:
            # Check if pair already exists in reverse
            existing = cursor.execute("""
                SELECT id FROM duplicate_matches 
                WHERE (primary_complaint_id = ? AND duplicate_complaint_id = ?)
                   OR (primary_complaint_id = ? AND duplicate_complaint_id = ?)
            """, (comp["id"], d["duplicate_complaint_id"], d["duplicate_complaint_id"], comp["id"])).fetchone()
            
            if not existing:
                cursor.execute("""
                    INSERT INTO duplicate_matches (primary_complaint_id, duplicate_complaint_id, similarity_score, geo_distance_m, status, explanation)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (comp["id"], d["duplicate_complaint_id"], d["similarity_score"], d["geo_distance_m"], d["status"], d["explanation"]))
                duplicate_pairs_found += 1

    conn.commit()
    print(f"Deliberate duplicate matches linked: {duplicate_pairs_found}")

    # Run Geographic Hotspot Detection
    print("Running Geographic Hotspot Clustering...")
    hotspots = analyze_hotspots()
    print(f"Identified {len(hotspots)} geographic hotspot clusters across the city.")

    conn.close()
    print("CivicAI seed process successfully completed!")

if __name__ == "__main__":
    seed_database()
