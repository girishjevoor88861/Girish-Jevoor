# CivicAI - Artificial Intelligence & Algorithmic Architecture

CivicAI implements a transparent, explainable AI pipeline designed specifically for municipal public administration. Unlike black-box models, all scoring dimensions, duplicate thresholds, and classification confidence ratings are fully interpretable and adjustable by city commissioners.

---

## Module 1: Automatic Natural Language Classification

### Architecture & Approach
When a citizen lodges a complaint, the text (title and description) undergoes tokenization, stop-word filtering, and domain-specific semantic matching against the Municipal Taxonomy Knowledge Base.

### Domain Taxonomy
- **7 Primary Departments**:
  1. Roads & Infrastructure
  2. Drainage & Water Management
  3. Sanitation
  4. Electricity & Streetlights
  5. Public Safety
  6. Water Supply
  7. Parks & Public Spaces
- **35+ Specialized Subcategories**:
  - E.g., `Potholes & Surface Damage`, `Sparking & Dangerous Wires`, `Main Pipeline Burst`, `Severe Waterlogging`.

### Outputs Generated
- **Predicted Category & Subcategory**: Best-matching node in taxonomy.
- **Assigned Department**: Automatic routing to responsible municipal agency.
- **Urgency Detection**: Signal detection via critical temporal and danger tokens (`immediate`, `emergency`, `hazard`, `fatal`, `open manhole`).
- **Confidence Rating**: Normalized score between 0.65 and 0.98 based on keyword density and score margins.
- **Crisp Executive Summary**: Summarized single-sentence representation for commissioner review.

---

## Module 2: Intelligent Duplicate Detection

### Composite Multi-Modal Matching Formula
To distinguish identical complaints from merely nearby incidents, CivicAI computes a composite similarity index:

$$\text{Composite Score} = (0.50 \times S_{\text{text}}) + (0.35 \times P_{\text{geo}}) + (0.15 \times C_{\text{cat}})$$

Where:
1. **$S_{\text{text}}$ (Semantic Text Similarity)**:
   Combined Jaccard token overlap and character 3-gram similarity:
   $$S_{\text{text}} = 0.6 \times \frac{|W_1 \cap W_2|}{|W_1 \cup W_2|} + 0.4 \times \frac{|\text{Tri}_1 \cap \text{Tri}_2|}{|\text{Tri}_1 \cup \text{Tri}_2|}$$
2. **$P_{\text{geo}}$ (Geographic Proximity)**:
   Computed using the Haversine great-circle distance formula:
   $$d = 2R \arcsin \left(\sqrt{\sin^2\left(\frac{\Delta\phi}{2}\right) + \cos\phi_1\cos\phi_2\sin^2\left(\frac{\Delta\lambda}{2}\right)}\right)$$
   Normalized over a maximum duplicate radius of $350\text{ meters}$:
   $$P_{\text{geo}} = \max\left(0, 1 - \frac{d}{350}\right)$$
3. **$C_{\text{cat}}$ (Category Match)**: $1.0$ if identical municipal category, $0.4$ if neighboring category.

### Decision Boundaries
- $\text{Composite} \ge 0.75$: **Confirmed Duplicate** candidate (flagged for one-click admin linking).
- $0.45 \le \text{Composite} < 0.75$: **Potential Duplicate** candidate.
- $\text{Composite} < 0.45$: Distinct complaint.

> **Safety Rule**: CivicAI never automatically merges unrelated reports. Administrators are given an interactive side-by-side review drawer with Confirm, Link, and Reject actions.

---

## Module 3: Explainable Priority Scoring Engine

### Scoring Dimensions & Configurable Weights
CivicAI evaluates 5 distinct, explainable dimensions:

$$\text{Priority Score} = w_1 S + w_2 P + w_3 U + w_4 G + w_5 F$$

| Factor | Weight ($w$) | Measurement Methodology |
| :--- | :---: | :--- |
| **Safety Risk ($S$)** | 30% | Danger indicators, injury hazards, electrocution risks, open pits, chemical leaks |
| **Public Impact ($P$)** | 25% | Location importance: hospitals, school zones, metro stations, arterial highways |
| **Urgency ($U$)** | 20% | Temporal urgency, escalation speed, active water flooding |
| **Geographic Concentration ($G$)** | 15% | Number of active unresolved complaints within a 500-meter radius |
| **Report Frequency ($F$)** | 10% | Number of independent citizen reports corroborating the same event |

### Priority Levels
- **Critical (80 – 100)**: Immediate life hazard dispatch; SLA: 2–6 hours.
- **High (60 – 79)**: Priority field inspection; SLA: 24 hours.
- **Medium (35 – 59)**: Standard operational queue; SLA: 48 hours.
- **Low (0 – 34)**: Scheduled maintenance cycle; SLA: 72+ hours.

### Life-Safety Hazard Override
For credible immediate life hazards (such as open manholes on roadways, sparking high-voltage cables, or gas leaks), CivicAI's safety override triggers automatically:
- Priority score is clamped to a minimum of **85 (Critical)**.
- Flagged with: `"SAFETY OVERRIDE ACTIVATED: Immediate life-safety hazard detected"`.

---

## Module 4: Authority Action Brief Generator

Produces structured, action-oriented briefs formatted for municipal commissioners and field crews:

```
ISSUE: SEVERE WATERLOGGING IN CENTRAL MARKET ROAD (Drainage & Water Management)
LOCATION: Central Market Road, Block A, Commercial Center
SEVERITY: CRITICAL (Priority Score: 88.0/100)
RELATED REPORTS: 4
PUBLIC IMPACT: Located near or impacts key public zone: 'market'
RECOMMENDED DEPARTMENT: Drainage and Water Management
RECOMMENDED ACTION: Immediate dispatch of municipal emergency response team within 2 hours.
```

---

## Module 5: Geographic Hotspot Intelligence (DBSCAN Clustering)

### Algorithm & Parameters
CivicAI uses distance-based spatial density clustering:
- **Metric**: Haversine distance.
- **$\epsilon$ (Neighborhood Radius)**: $0.65\text{ km}$ ($650\text{ meters}$).
- **MinPts (Minimum Complaints to form cluster)**: $3$ complaints.

### Cluster Extraction
For each discovered cluster:
1. Computes the geometric centroid $(\bar{\phi}, \bar{\lambda})$.
2. Determines the cluster radius $r = \max(\text{distance}(\text{centroid}, p_i))$.
3. Identifies the dominant civic category and average priority score.
4. Saves records to `hotspot_clusters` table and renders translucent glowing circles on the Leaflet map.
