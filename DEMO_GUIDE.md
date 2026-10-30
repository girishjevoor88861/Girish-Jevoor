# CivicAI - 5-Minute End-to-End Demonstration Guide

Follow this step-by-step walkthrough to evaluate the complete CivicAI platform lifecycle across all 4 interfaces. All actions operate on the same persistent database records in real time.

---

## Pre-requisite: Open CivicAI
Ensure the server is running on `http://localhost:8000` (or double click `start_server.bat`).

---

## Step 1: Citizen Login & Lodging a Waterlogging Complaint
1. Open **[http://localhost:8000](http://localhost:8000)**.
2. In the top-right navbar, click **⚡ Demo Roles** -> select **Citizen (Alice)**.
   - *Result*: Notification appears confirming authentication as `Alice Morgan`.
3. Click **Citizen Portal** in the navigation bar.
4. In the **Report a Civic Problem** multi-step wizard:
   - **Step 1: Problem Details**:
     - Title: `Severe waterlogging flooding Central Market Road`
     - Category: `Drainage & Water Management`
     - Description: `Knee-deep stagnant water flooding the market road after rain. Storm drains completely choked with silt.`
     - Click **Next: Select Location &rarr;**
   - **Step 2: Location Selection**:
     - Click **📍 Use My Current GPS** (or click on the map near Central Market).
     - Address: `Central Market Road, Block A`
     - Click **Next: Review & AI Analysis &rarr;**
   - **Step 3: Review & Submit**:
     - Observe the **Live AI Triage Preview** displaying predicted department (`Drainage and Water Management`), detected urgency, and AI confidence.
     - Click **Confirm & Submit to City Authority**.
5. **Confirmation**:
   - The screen displays the generated **Tracking Reference** (e.g. `CIV-2026-XXXXX`), assigned priority (`Critical` or `High`), and the generated AI Action Brief.
   - Note down or copy the tracking reference number.

---

## Step 2: AI Duplicate Detection & Priority Verification
1. Click **View in My Complaints**.
2. Click **View Status & Timeline &rarr;** on your newly lodged report.
3. Observe:
   - **Explainable Priority Breakdown**: 5 distinct factor scores (Safety Risk 30%, Public Impact 25%, Urgency 20%, Concentration 15%, Frequency 10%).
   - **AI Action Brief**: Structured authority-ready operational directive.

---

## Step 3: Geographic Hotspot Map Exploration
1. In the top navigation bar, click **🗺️ City Map**.
2. Observe:
   - Priority color-coded pins across Metro City.
   - Translucent glowing **Hotspot Circles** showing dense problem areas detected by the DBSCAN spatial clustering algorithm.
   - Click on the glowing circle over **Downtown / Central Market** to view cluster concentration details (e.g., `4 reports in 0.6km radius`).

---

## Step 4: Administrator Review & Officer Assignment
1. In the top-right navbar, click **⚡ Demo Roles** -> select **Municipal Admin**.
   - *Result*: Role transitions to `Commissioner Sarah Mitchell`.
2. Click **Admin Center** in the navigation bar.
3. Observe:
   - **8 Live KPI Cards**: Total Reports, New Reports Today, Pending Reports, etc.
   - **Chart.js Analytics**: Category doughnut, priority bars, weekly trend line, and department SLA resolution rates.
4. In the **Complaint Management Center** table:
   - Type your tracking ID into the search input or look at the top row.
   - Click the **👤 (Assign)** button next to your complaint.
   - Select **Officer Sarah Jenkins (Drainage Operations Lead)**.
   - Enter dispatch instructions: `Deploy vacuum tanker and clear storm grates immediately.`
   - Click **Confirm Assignment**.
   - *Result*: Complaint status immediately updates to `ASSIGNED` in the database.

---

## Step 5: Field Officer Work & Photographic Evidence Upload
1. In the top-right navbar, click **⚡ Demo Roles** -> select **Field Officer (John/Sarah)**.
2. Click **Field Officer** in the navigation bar.
3. In the officer task queue:
   - Click the **Pending Acceptance** tab.
   - Locate the assigned complaint and click **Accept Assignment & Dispatch Crew &rarr;**.
   - *Result*: Complaint status transitions to `IN_PROGRESS`.
4. Switch to the **Active On-Site Work** tab:
   - Click **Submit Resolution Evidence & Finish**.
   - Enter summary: `Cleared 150kg silt blockage, replaced broken grate cover, restored full stormwater drainage.`
   - Notice the Before & After photographic evidence pre-attached.
   - Labor hours: `3.5 hrs`.
   - Click **Verify Resolution & Mark Complete**.
   - *Result*: Complaint status transitions to `RESOLVED` and officer resolved count increments.

---

## Step 6: Citizen Resolution Verification
1. Click **Track Issue** in the top navigation bar.
2. Enter the tracking reference ID (e.g. `CIV-2026-XXXXX`) and click **Track Live Status**.
3. Observe the full resolution report:
   - Visual milestone progress bar shows 100% completed.
   - **Verified Field Resolution Evidence** section displays the Before and After photos side-by-side.
   - **Complete Verification Timeline** shows every actor (Citizen Alice &rarr; AI System &rarr; Admin Commissioner &rarr; Officer Sarah) with exact timestamps and explanations.
4. Switch back to **Citizen (Alice)** via **⚡ Demo Roles**, click on the complaint details, and submit a 5-star rating feedback (`⭐⭐⭐⭐⭐ Excellent response time!`).

**End of 5-Minute Demonstration: Complete end-to-end civic issue resolution verified.**
