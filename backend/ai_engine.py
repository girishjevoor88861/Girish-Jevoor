"""
CivicAI - AI Intelligence Engine
Implements:
1. Automatic Classification (NLP taxonomy matching, department routing, keyword extraction, urgency detection)
2. Intelligent Duplicate Detection (Semantic text similarity + Haversine geographic distance + category + time window)
3. Explainable Priority Engine (Safety 30%, Impact 25%, Urgency 20%, Concentration 15%, Frequency 10%, Safety Overrides)
4. Action Brief Generator (Authority-ready operational briefs)
5. Geographic Hotspot Intelligence (DBSCAN-based municipal cluster analysis)
"""

import math
import re
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
from backend.config import PRIORITY_WEIGHTS, PRIORITY_THRESHOLDS, DUPLICATE_CONFIG, HOTSPOT_CONFIG
from backend.database import get_db_connection, rows_to_list, row_to_dict

# -------------------------------------------------------------
# Municipal Taxonomy and Department Routing Knowledge Base
# -------------------------------------------------------------
TAXONOMY = {
    "Roads & Infrastructure": {
        "department": "Roads and Infrastructure",
        "keywords": ["pothole", "crater", "asphalt", "road", "pavement", "sidewalk", "divider", "guardrail", "bridge", "flyover", "speed breaker", "traffic light", "signal", "zebra crossing", "manhole cover damaged", "cave-in", "tarmac"],
        "subcategories": {
            "Potholes & Surface Damage": ["pothole", "crater", "broken road", "asphalt cracked", "damaged tarmac", "uneven road"],
            "Damaged Sidewalk & Footpaths": ["sidewalk", "footpath", "broken slab", "pedestrian walkway", "curb"],
            "Traffic Signals & Signage": ["traffic light", "signal not working", "broken sign", "missing stop sign", "signal blink"],
            "Road Dividers & Guardrails": ["divider", "median broken", "guardrail damaged", "barricade"],
            "Bridges & Flyovers": ["flyover", "bridge joint", "overpass", "expansion joint"]
        }
    },
    "Drainage & Water Management": {
        "department": "Drainage and Water Management",
        "keywords": ["waterlogging", "flood", "drain", "drainage", "sewage", "gutter", "stormwater", "overflow", "stagnant water", "culvert", "manhole overflowing", "water stagnation", "clogged drain", "sludge"],
        "subcategories": {
            "Severe Waterlogging": ["waterlogging", "knee deep water", "flooded street", "submerged", "stagnant water pool"],
            "Blocked Storm Drains": ["blocked drain", "clogged gutter", "stormwater choke", "grate blocked"],
            "Sewage Overflow": ["sewage leak", "gutter overflow", "smelly drainage", "foul water", "septic"],
            "Canal & Culvert Blockage": ["canal clogged", "culvert silt", "nallah overflow"]
        }
    },
    "Sanitation": {
        "department": "Sanitation",
        "keywords": ["garbage", "trash", "waste", "dump", "litter", "rubbish", "dustbin", "dead animal", "stench", "debris", "plastic waste", "uncollected garbage", "overflowing bin", "carcass", "sanitation"],
        "subcategories": {
            "Uncollected Garbage": ["uncollected garbage", "missed collection", "garbage pile", "trash bin full", "litter heap"],
            "Illegal Dumping Site": ["illegal dump", "open dumping", "commercial waste", "construction debris", "rubble"],
            "Dead Animal Carcass": ["dead animal", "carcass", "dead dog", "dead bird", "decaying animal"],
            "Overflowing Public Dustbins": ["overflowing dustbin", "broken trash can", "bin spillage"]
        }
    },
    "Electricity & Streetlights": {
        "department": "Electricity and Streetlights",
        "keywords": ["streetlight", "street lamp", "light pole", "dark street", "wiring", "sparking", "transformer", "power cable", "hanging wire", "electric shock", "blackout", "lamp post", "short circuit", "voltage"],
        "subcategories": {
            "Streetlight Outage": ["dark street", "light pole not working", "streetlights off", "lamp dark", "flickering streetlight"],
            "Sparking & Dangerous Wires": ["sparking wire", "hanging electric wire", "live cable", "short circuit", "sparking transformer", "open wire"],
            "Damaged Light Pole": ["tilted pole", "bent electric pole", "fallen light post", "exposed junction box"],
            "Transformer Issues": ["transformer spark", "oil leak transformer", "transformer humming loudly"]
        }
    },
    "Public Safety": {
        "department": "Public Safety",
        "keywords": ["open manhole", "manhole uncovered", "fallen tree", "collapsed wall", "fire hazard", "gas leak", "hazard", "danger", "electrocution risk", "sinkhole", "unauthorized structure", "deep trench"],
        "subcategories": {
            "Open & Missing Manhole": ["open manhole", "missing manhole cover", "uncovered sewer pit", "gaping hole"],
            "Fallen Trees & Heavy Branches": ["fallen tree", "hanging branch", "uprooted tree", "blocking road tree"],
            "Structural Hazard & Collapsing Walls": ["collapsing wall", "cracked structure", "falling plaster", "unsafe building"],
            "Immediate Fire / Chemical Hazard": ["gas smell", "fire hazard", "chemical leak", "smoke from waste"]
        }
    },
    "Water Supply": {
        "department": "Water Supply",
        "keywords": ["pipe burst", "water leak", "pipeline", "drinking water", "contaminated water", "muddy water", "no water supply", "low pressure", "valve broken", "water tanker", "pipe rupture"],
        "subcategories": {
            "Main Pipeline Burst": ["pipeline burst", "broken main pipe", "water gushing out", "street flooded clean water"],
            "Contaminated Drinking Water": ["dirty water", "smelly tap water", "yellow water", "muddy tap water", "drinking water pollution"],
            "Water Supply Disruption": ["no water", "dry taps for days", "extremely low water pressure"],
            "Damaged Water Meter / Valve": ["leaking valve", "broken water meter", "public tap broken"]
        }
    },
    "Parks & Public Spaces": {
        "department": "Parks and Public Spaces",
        "keywords": ["park", "garden", "playground", "swing", "bench", "overgrown", "grass", "tree trimming", "vandalism", "public fountain", "fence broken", "jogging track"],
        "subcategories": {
            "Broken Playground Equipment": ["broken swing", "damaged slide", "unsafe play area", "children park broken"],
            "Damaged Park Amenities": ["broken bench", "vandalized railing", "jogging track damaged", "broken lights in park"],
            "Overgrown Vegetation & Weeds": ["overgrown grass", "wild bushes", "snake hazard weeds", "park unmaintained"]
        }
    }
}

# Immediate safety hazard override triggers
SAFETY_OVERRIDE_PATTERNS = [
    r"open\s+manhole",
    r"missing\s+manhole",
    r"sparking\s+(?:wire|transformer|pole)",
    r"live\s+(?:wire|cable|electric)",
    r"hanging\s+(?:wire|cable|high\s+voltage)",
    r"electrocution",
    r"gas\s+leak",
    r"deep\s+sinkhole",
    r"collapsing\s+(?:wall|structure|bridge)",
    r"pipeline\s+burst.*gushing"
]

# -------------------------------------------------------------
# Module 1: Automatic Classification
# -------------------------------------------------------------
def classify_complaint_text(title: str, description: str) -> Dict[str, Any]:
    """
    Analyzes complaint text using tokenization, domain taxonomy keyword matching,
    sentiment/urgency detection, and department routing.
    """
    combined_text = f"{title} {description}".lower()
    
    # Tokenize words
    words = re.findall(r'\b[a-z]{3,}\b', combined_text)
    word_set = set(words)
    
    best_category = "Roads & Infrastructure"
    best_subcategory = "Potholes & Surface Damage"
    best_dept = "Roads and Infrastructure"
    highest_score = 0
    category_scores = {}

    for cat_name, cat_data in TAXONOMY.items():
        score = 0
        # Check main keywords
        for kw in cat_data["keywords"]:
            if kw in combined_text:
                score += 3
            elif any(w in kw for w in words):
                score += 1

        # Check subcategories
        cat_sub = None
        highest_sub_score = -1
        for sub_name, sub_kws in cat_data["subcategories"].items():
            sub_score = 0
            for skw in sub_kws:
                if skw in combined_text:
                    sub_score += 4
                elif any(w in skw for w in words):
                    sub_score += 1
            if sub_score > highest_sub_score:
                highest_sub_score = sub_score
                cat_sub = sub_name
        
        score += max(0, highest_sub_score)
        category_scores[cat_name] = score
        
        if score > highest_score:
            highest_score = score
            best_category = cat_name
            best_subcategory = cat_sub or list(cat_data["subcategories"].keys())[0]
            best_dept = cat_data["department"]

    # Calculate confidence score (normalized between 0.65 and 0.98)
    total_score = sum(category_scores.values()) or 1
    raw_confidence = (highest_score / (total_score + 2)) * 1.3
    confidence = round(min(0.98, max(0.68, raw_confidence)), 2)

    # Detect urgency keywords
    urgency = "medium"
    critical_terms = ["immediate", "danger", "emergency", "fatal", "hazard", "sparking", "shock", "burst", "open manhole", "severe", "drowning", "flood"]
    high_terms = ["major", "urgent", "overflow", "blocked", "heavy", "terrible", "accident", "broken", "huge"]
    low_terms = ["minor", "aesthetic", "small", "paint", "trimming", "slight"]

    if any(term in combined_text for term in critical_terms):
        urgency = "critical"
    elif any(term in combined_text for term in high_terms):
        urgency = "high"
    elif any(term in combined_text for term in low_terms):
        urgency = "low"

    # Extract top keywords
    all_cat_keywords = []
    for cd in TAXONOMY.values():
        all_cat_keywords.extend(cd["keywords"])
    found_keywords = [kw for kw in set(all_cat_keywords) if kw in combined_text]
    if not found_keywords:
        found_keywords = [w for w in words[:5] if len(w) > 4]

    # Generate concise summary
    clean_title = title.strip().capitalize()
    if len(description) > 90:
        summary_body = description[:87].rsplit(' ', 1)[0] + '...'
    else:
        summary_body = description.strip()
    short_summary = f"{clean_title}: {summary_body}"

    return {
        "category": best_category,
        "subcategory": best_subcategory,
        "department": best_dept,
        "short_summary": short_summary,
        "keywords": ", ".join(found_keywords[:6]),
        "urgency": urgency,
        "confidence": confidence
    }

# -------------------------------------------------------------
# Module 2: Intelligent Duplicate Detection
# -------------------------------------------------------------
def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates the great-circle distance between two GPS points on Earth in meters."""
    R = 6371000.0 # Earth's radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def compute_text_similarity(text1: str, text2: str) -> float:
    """Computes combined Jaccard word token overlap and 3-gram character similarity."""
    t1 = set(re.findall(r'\b[a-z]{3,}\b', text1.lower()))
    t2 = set(re.findall(r'\b[a-z]{3,}\b', text2.lower()))
    if not t1 or not t2:
        return 0.0
    
    # Word Jaccard
    intersection = t1.intersection(t2)
    union = t1.union(t2)
    word_sim = len(intersection) / len(union)

    # Substring trigram overlap
    clean1 = "".join(re.findall(r'[a-z0-9]', text1.lower()))
    clean2 = "".join(re.findall(r'[a-z0-9]', text2.lower()))
    ngrams1 = {clean1[i:i+3] for i in range(len(clean1) - 2)}
    ngrams2 = {clean2[i:i+3] for i in range(len(clean2) - 2)}
    
    ngram_sim = 0.0
    if ngrams1 and ngrams2:
        ngram_sim = len(ngrams1.intersection(ngrams2)) / len(ngrams1.union(ngrams2))

    return round((0.6 * word_sim) + (0.4 * ngram_sim), 3)

def detect_duplicates(complaint_id: int, title: str, description: str, category: str, lat: float, lng: float, exclude_id: int = None) -> List[Dict[str, Any]]:
    """
    Compares a complaint against recent database reports using semantic text similarity,
    geographic proximity (Haversine formula), category matching, and time window.
    """
    conn = get_db_connection()
    duplicates = []
    try:
        # Fetch complaints within the last 60 days
        cutoff_date = (datetime.utcnow() - timedelta(days=DUPLICATE_CONFIG["time_window_days"])).strftime("%Y-%m-%d %H:%M:%S")
        
        query = """
            SELECT c.id, c.tracking_id, c.title, c.description, c.category, c.priority, c.status, c.created_at,
                   l.latitude, l.longitude, l.address
            FROM complaints c
            JOIN complaint_locations l ON c.id = l.complaint_id
            WHERE c.created_at >= ? AND c.status NOT IN ('closed', 'rejected')
        """
        params = [cutoff_date]
        if exclude_id:
            query += " AND c.id != ?"
            params.append(exclude_id)
        elif complaint_id:
            query += " AND c.id != ?"
            params.append(complaint_id)

        rows = conn.execute(query, params).fetchall()
        candidate_list = rows_to_list(rows)

        for candidate in candidate_list:
            cand_lat = float(candidate["latitude"])
            cand_lng = float(candidate["longitude"])
            distance_m = haversine_distance_meters(lat, lng, cand_lat, cand_lng)

            # Skip if outside maximum duplicate radius (350 meters)
            if distance_m > DUPLICATE_CONFIG["max_distance_meters"]:
                continue

            # Calculate text similarity
            text_sim = compute_text_similarity(f"{title} {description}", f"{candidate['title']} {candidate['description']}")
            
            # Category match bonus
            cat_match = 1.0 if candidate["category"] == category else 0.4
            
            # Geo proximity score: 1.0 at 0m distance, decays to 0.0 at 350m
            geo_proximity = max(0.0, 1.0 - (distance_m / DUPLICATE_CONFIG["max_distance_meters"]))

            # Composite similarity score (Weights: 50% Text, 35% Geo, 15% Category)
            composite_score = round((0.50 * text_sim) + (0.35 * geo_proximity) + (0.15 * cat_match), 3)

            if composite_score >= DUPLICATE_CONFIG["similarity_threshold_potential"]:
                status = "confirmed" if composite_score >= DUPLICATE_CONFIG["similarity_threshold_high"] else "potential"
                
                # Generate explanation
                dist_str = f"{int(distance_m)}m away" if distance_m >= 5 else "at the exact same spot"
                explanation = (
                    f"{status.capitalize()} duplicate of complaint {candidate['tracking_id']}. "
                    f"Reported {dist_str} at '{candidate['address']}'. "
                    f"Text similarity {int(text_sim * 100)}%, overall civic match {int(composite_score * 100)}%."
                )

                duplicates.append({
                    "primary_complaint_id": complaint_id,
                    "duplicate_complaint_id": candidate["id"],
                    "duplicate_tracking_id": candidate["tracking_id"],
                    "duplicate_title": candidate["title"],
                    "similarity_score": composite_score,
                    "similarity_pct": int(composite_score * 100),
                    "geo_distance_m": round(distance_m, 1),
                    "address": candidate["address"],
                    "status": status,
                    "explanation": explanation
                })

        # Sort by similarity descending
        duplicates.sort(key=lambda x: x["similarity_score"], reverse=True)
        return duplicates[:5]
    finally:
        conn.close()

# -------------------------------------------------------------
# Module 3: Explainable Priority Engine
# -------------------------------------------------------------
def calculate_priority_score(
    title: str,
    description: str,
    category: str,
    lat: float,
    lng: float,
    recent_complaints_count: int = 1
) -> Dict[str, Any]:
    """
    Evaluates 5 transparent dimensions:
    - Safety Risk (30%)
    - Public Impact (25%)
    - Urgency (20%)
    - Geographic Concentration (15%)
    - Report Frequency (10%)
    Calculates 0-100 score, priority level, factor explanations, and enforces safety overrides.
    """
    combined_text = f"{title} {description}".lower()
    
    # 1. Safety Risk Evaluation (0 - 100)
    safety_score = 30.0
    safety_reasons = []
    
    high_safety_terms = ["hazard", "fatal", "injury", "shock", "sparking", "fire", "open manhole", "deep hole", "cave-in", "poison", "collapse", "electrocution", "gas leak", "submerged"]
    med_safety_terms = ["danger", "slippery", "skid", "broken glass", "sharp", "dark street", "septic", "stench"]

    for term in high_safety_terms:
        if term in combined_text:
            safety_score += 25.0
            safety_reasons.append(f"Contains high-hazard indicator '{term}'")
    for term in med_safety_terms:
        if term in combined_text:
            safety_score += 12.0
            safety_reasons.append(f"Contains moderate risk term '{term}'")

    if category in ["Public Safety", "Electricity & Streetlights"]:
        safety_score += 20.0
        safety_reasons.append(f"Category '{category}' has inherent safety implications")
    elif category in ["Drainage & Water Management"]:
        safety_score += 15.0
        safety_reasons.append("Drainage failures present waterborne contamination and vector risks")
        
    safety_score = min(100.0, max(10.0, safety_score))
    if not safety_reasons:
        safety_reasons.append("Standard municipal baseline risk")

    # 2. Public Impact Evaluation (0 - 100)
    impact_score = 35.0
    impact_reasons = []

    traffic_terms = ["main road", "highway", "junction", "intersection", "market", "school", "hospital", "bus stop", "metro", "commercial area", "hundreds", "commuters", "residents"]
    for term in traffic_terms:
        if term in combined_text:
            impact_score += 18.0
            impact_reasons.append(f"Located near or impacts key public zone: '{term}'")

    if category in ["Roads & Infrastructure", "Water Supply"]:
        impact_score += 15.0
        impact_reasons.append("Broad population dependency on this infrastructure")
        
    impact_score = min(100.0, max(15.0, impact_score))
    if not impact_reasons:
        impact_reasons.append("Localized residential impact")

    # 3. Urgency Evaluation (0 - 100)
    urgency_score = 30.0
    urgency_reasons = []

    urgent_terms = ["immediately", "emergency", "rapidly", "urgent", "escalating", "now", "critical", "since morning", "spreading", "hours"]
    for term in urgent_terms:
        if term in combined_text:
            urgency_score += 20.0
            urgency_reasons.append(f"Temporal urgency signaled by '{term}'")

    urgency_score = min(100.0, max(15.0, urgency_score))
    if not urgency_reasons:
        urgency_reasons.append("Standard operational queue urgency")

    # 4. Geographic Concentration Evaluation (0 - 100)
    # Check number of active complaints within 500m
    concentration_score = 25.0
    concentration_reasons = []
    
    conn = get_db_connection()
    try:
        nearby_rows = conn.execute("""
            SELECT l.latitude, l.longitude 
            FROM complaint_locations l 
            JOIN complaints c ON l.complaint_id = c.id
            WHERE c.status NOT IN ('closed', 'resolved')
        """).fetchall()
        
        nearby_count = 0
        for r in nearby_rows:
            dist = haversine_distance_meters(lat, lng, float(r["latitude"]), float(r["longitude"]))
            if dist <= 500.0:
                nearby_count += 1
        
        if nearby_count >= 6:
            concentration_score = 90.0
            concentration_reasons.append(f"Dense cluster: {nearby_count} active complaints in 500m radius")
        elif nearby_count >= 3:
            concentration_score = 65.0
            concentration_reasons.append(f"Moderate cluster: {nearby_count} active complaints in 500m radius")
        else:
            concentration_score = 30.0
            concentration_reasons.append(f"Isolated issue: {nearby_count} other complaint(s) in vicinity")
    except Exception:
        concentration_reasons.append("Standard density assessment")
    finally:
        conn.close()

    # 5. Report Frequency Evaluation (0 - 100)
    frequency_score = min(100.0, max(20.0, 20.0 + (recent_complaints_count * 15.0)))
    frequency_reasons = [f"Corroborated by {recent_complaints_count} related or duplicate report(s)"]

    # Calculate Weighted Composite Score
    weights = PRIORITY_WEIGHTS
    composite = (
        (weights["safety_risk"] * safety_score) +
        (weights["public_impact"] * impact_score) +
        (weights["urgency"] * urgency_score) +
        (weights["geographic_concentration"] * concentration_score) +
        (weights["report_frequency"] * frequency_score)
    )

    # Check Safety Overrides for Credible Immediate Hazards
    safety_override = False
    override_reason = None
    for pattern in SAFETY_OVERRIDE_PATTERNS:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            safety_override = True
            override_reason = f"SAFETY OVERRIDE ACTIVATED: Immediate life-safety hazard detected ('{match.group(0)}'). Overriding score to minimum 85."
            composite = max(composite, 88.0)
            safety_score = max(safety_score, 95.0)
            break

    total_score = round(min(100.0, max(0.0, composite)), 1)

    # Classify Priority Level
    if total_score >= PRIORITY_THRESHOLDS["critical"]:
        priority_level = "critical"
        recommended_action = "Immediate dispatch of municipal emergency response team within 2 hours."
    elif total_score >= PRIORITY_THRESHOLDS["high"]:
        priority_level = "high"
        recommended_action = "Assign field inspector and schedule remediation within 24 hours."
    elif total_score >= PRIORITY_THRESHOLDS["medium"]:
        priority_level = "medium"
        recommended_action = "Queue for routine departmental work order within standard 48-hour SLA."
    else:
        priority_level = "low"
        recommended_action = "Schedule during scheduled ward maintenance cycle."

    return {
        "total_score": total_score,
        "priority_level": priority_level,
        "safety_score": round(safety_score, 1),
        "public_impact_score": round(impact_score, 1),
        "urgency_score": round(urgency_score, 1),
        "concentration_score": round(concentration_score, 1),
        "frequency_score": round(frequency_score, 1),
        "safety_override": safety_override,
        "override_reason": override_reason,
        "recommended_action": recommended_action,
        "confidence": 0.94 if safety_override else 0.88,
        "factor_breakdown": {
            "safety_risk": {"score": round(safety_score, 1), "weight": f"{int(weights['safety_risk']*100)}%", "reasons": safety_reasons},
            "public_impact": {"score": round(impact_score, 1), "weight": f"{int(weights['public_impact']*100)}%", "reasons": impact_reasons},
            "urgency": {"score": round(urgency_score, 1), "weight": f"{int(weights['urgency']*100)}%", "reasons": urgency_reasons},
            "geographic_concentration": {"score": round(concentration_score, 1), "weight": f"{int(weights['geographic_concentration']*100)}%", "reasons": concentration_reasons},
            "report_frequency": {"score": round(frequency_score, 1), "weight": f"{int(weights['report_frequency']*100)}%", "reasons": frequency_reasons}
        }
    }

# -------------------------------------------------------------
# Module 4: Action Brief Generator
# -------------------------------------------------------------
def generate_action_brief(
    title: str,
    location_address: str,
    priority_level: str,
    priority_score: float,
    related_reports_count: int,
    department: str,
    category: str,
    public_impact_desc: str,
    recommended_action: str
) -> str:
    """
    Produces authority-ready, concise action brief formatted for municipal commissioners,
    department heads, and field crews.
    """
    brief = (
        f"ISSUE: {title.strip().upper()} ({category})\n"
        f"LOCATION: {location_address.strip()}\n"
        f"SEVERITY: {priority_level.upper()} (Priority Score: {priority_score}/100)\n"
        f"RELATED REPORTS: {related_reports_count}\n"
        f"PUBLIC IMPACT: {public_impact_desc}\n"
        f"RECOMMENDED DEPARTMENT: {department}\n"
        f"RECOMMENDED ACTION: {recommended_action}"
    )
    return brief

# -------------------------------------------------------------
# Module 5: Geographic Hotspot Intelligence (DBSCAN / Distance Clustering)
# -------------------------------------------------------------
def analyze_hotspots() -> List[Dict[str, Any]]:
    """
    Executes distance-based clustering across all active and recent complaints in the database.
    Identifies geographic clusters, recurring problem areas, category concentration, and severity.
    Saves and updates hotspot_clusters table.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Fetch complaints with valid coordinates
        query = """
            SELECT c.id, c.tracking_id, c.title, c.category, c.priority, c.status,
                   l.latitude, l.longitude, l.address, l.ward,
                   COALESCE(a.total_priority_score, 50.0) as score
            FROM complaints c
            JOIN complaint_locations l ON c.id = l.complaint_id
            LEFT JOIN ai_analysis a ON c.id = a.complaint_id
            WHERE c.status NOT IN ('rejected')
        """
        rows = rows_to_list(conn.execute(query).fetchall())
        if len(rows) < 3:
            return []

        # Simple & robust distance clustering (Haversine DBSCAN implementation)
        eps_meters = HOTSPOT_CONFIG["eps_km"] * 1000.0
        min_pts = HOTSPOT_CONFIG["min_samples"]
        
        visited = set()
        clusters = []

        for i, point in enumerate(rows):
            if i in visited:
                continue
            visited.add(i)

            # Find neighbors within eps_meters
            neighbors = []
            for j, other in enumerate(rows):
                dist = haversine_distance_meters(
                    float(point["latitude"]), float(point["longitude"]),
                    float(other["latitude"]), float(other["longitude"])
                )
                if dist <= eps_meters:
                    neighbors.append(j)

            if len(neighbors) >= min_pts:
                # Grow cluster
                cluster_indices = set(neighbors)
                queue = list(neighbors)
                while queue:
                    curr = queue.pop(0)
                    if curr not in visited:
                        visited.add(curr)
                        curr_neighbors = []
                        for k, candidate in enumerate(rows):
                            d = haversine_distance_meters(
                                float(rows[curr]["latitude"]), float(rows[curr]["longitude"]),
                                float(candidate["latitude"]), float(candidate["longitude"])
                            )
                            if d <= eps_meters:
                                curr_neighbors.append(k)
                        if len(curr_neighbors) >= min_pts:
                            for n in curr_neighbors:
                                if n not in cluster_indices:
                                    cluster_indices.add(n)
                                    queue.append(n)

                clusters.append([rows[idx] for idx in cluster_indices])

        # Analyze each cluster
        hotspot_results = []
        # Clear existing clusters table
        cursor.execute("DELETE FROM hotspot_clusters;")

        for idx, cluster_points in enumerate(clusters):
            count = len(cluster_points)
            center_lat = sum(float(p["latitude"]) for p in cluster_points) / count
            center_lng = sum(float(p["longitude"]) for p in cluster_points) / count
            
            # Find max distance to point as cluster radius
            max_dist = max(haversine_distance_meters(center_lat, center_lng, float(p["latitude"]), float(p["longitude"])) for p in cluster_points)
            radius_km = round(max(0.3, max_dist / 1000.0), 2)

            # Dominant category
            categories = [p["category"] for p in cluster_points]
            dominant_category = max(set(categories), key=categories.count)

            # Average severity
            avg_score = sum(float(p["score"]) for p in cluster_points) / count
            if avg_score >= 75:
                severity_level = "critical"
            elif avg_score >= 55:
                severity_level = "high"
            elif avg_score >= 35:
                severity_level = "medium"
            else:
                severity_level = "low"

            ward_names = [p["ward"] for p in cluster_points if p.get("ward")]
            primary_ward = ward_names[0] if ward_names else f"Ward {idx+1}"
            cluster_name = f"{primary_ward} - {dominant_category} Concentration ({count} reports)"

            complaint_ids = [p["id"] for p in cluster_points]
            import json
            ids_json = json.dumps(complaint_ids)

            cursor.execute("""
                INSERT INTO hotspot_clusters (cluster_name, center_lat, center_lng, radius_km, complaint_count, dominant_category, severity_level, complaint_ids_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (cluster_name, center_lat, center_lng, radius_km, count, dominant_category, severity_level, ids_json))

            hotspot_results.append({
                "id": idx + 1,
                "cluster_name": cluster_name,
                "center_lat": round(center_lat, 6),
                "center_lng": round(center_lng, 6),
                "radius_km": radius_km,
                "complaint_count": count,
                "dominant_category": dominant_category,
                "severity_level": severity_level,
                "avg_score": round(avg_score, 1),
                "complaint_ids": complaint_ids
            })

        conn.commit()
        return hotspot_results
    finally:
        conn.close()
