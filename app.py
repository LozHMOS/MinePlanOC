"""
MOS MinePlan OC – Enhanced Production Prototype
================================================
Open Cut Coal Mine Daily Planning & Morning Meeting Tool

Password: mos2025 (planner) | super2025 (supervisor) | viewer2025 (view only)
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from datetime import date, timedelta, datetime
import io

# ══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="MOS MinePlan OC",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# GLOBAL STYLING
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
    [data-testid="stSidebar"] { background: #0d1b2a; }
    [data-testid="stSidebar"] * { color: #d0d8e0 !important; }
    [data-testid="stAppViewContainer"] { background: #111d2b; }
    [data-testid="stAppViewContainer"] .stMarkdown,
    [data-testid="stAppViewContainer"] p,
    [data-testid="stAppViewContainer"] label { color: #c8d4e0; }
    .mos-header {
        display:flex; align-items:center; gap:14px;
        background: linear-gradient(135deg,#0d1b2a 0%,#1a2e42 100%);
        border-left: 5px solid #e63946; border-radius: 10px;
        padding: 0.9rem 1.4rem; margin-bottom: 1rem;
    }
    .mos-logo { font-size:1.6rem; font-weight:900; color:#e63946; letter-spacing:3px; margin:0; }
    .mos-subtitle { font-size:0.85rem; color:#8fa8c0; margin:0; }
    .mos-site { font-size:1rem; font-weight:700; color:#ffffff; margin:0; }
    .equip-card {
        background:#1a2a3a; border:1px solid #253545;
        border-radius:10px; padding:1rem; margin:0.5rem 0;
    }
    .equip-operating   { border-left:5px solid #4CAF50; }
    .equip-maintenance { border-left:5px solid #F44336; }
    .equip-available   { border-left:5px solid #FF9800; }
    .equip-standby     { border-left:5px solid #2196F3; }
    .handover-note {
        background:rgba(255,193,7,0.08); border-left:3px solid #FFC107;
        padding:7px 10px; border-radius:5px; font-size:0.85rem;
        color:#FFD54F; margin:4px 0;
    }
    .handover-label { font-size:0.72rem; color:#8a7a2a; text-transform:uppercase; letter-spacing:1px; margin-bottom:2px; }
    .badge { padding:2px 8px; border-radius:12px; font-size:0.75rem; font-weight:700; }
    .badge-critical { background:#c62828; color:white; }
    .badge-high     { background:#e65100; color:white; }
    .badge-medium   { background:#f9a825; color:#1a1a1a; }
    .badge-low      { background:#2e7d32; color:white; }
    .section-heading {
        font-size:0.85rem; font-weight:700; color:#a0c0e0;
        text-transform:uppercase; letter-spacing:1.5px;
        border-bottom:1px solid #253545; padding-bottom:4px; margin:1rem 0 0.6rem;
    }
    .gps-live {
        background:rgba(76,175,80,0.2); border:1px solid #4CAF50;
        color:#81C784; padding:2px 8px; border-radius:12px;
        font-size:0.75rem; font-weight:700;
    }
    .report-box {
        background:#0d1b2a; border:1px solid #1e3a5a; border-radius:8px;
        padding:1.2rem; font-family:monospace; font-size:0.82rem;
        color:#a0c8e0; white-space:pre-wrap; max-height:420px; overflow-y:auto;
    }
    [data-testid="metric-container"] {
        background: #1a2332; border: 1px solid #2d3a4a; border-radius: 8px; padding: 8px;
    }
    .stSelectbox > div, .stTextInput > div, .stTextArea > div { min-height:44px; }
    .stButton > button { min-height:44px; }
    #MainMenu {visibility:hidden;}
    footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS – MINE COORDINATE SYSTEM
# ══════════════════════════════════════════════════════════════════════════════

MINE_SITES = [
    "North Pit Colliery – Bowen Basin",
    "Central Queensland Colliery",
    "Bowen Basin Site A",
]
ACCESS_CODES = {
    "mos2025":    ("Mine Planner",        "planner"),
    "super2025":  ("Supervisor",          "supervisor"),
    "viewer2025": ("Viewer (Read Only)",  "viewer"),
}
E_MIN, E_MAX = 22000, 23500   # Local grid easting  (metres)
N_MIN, N_MAX = 14500, 15800   # Local grid northing (metres)

# ── Equipment Fleet ───────────────────────────────────────────────────────────
BASE_FLEET = [
    {"id":"EX-01","type":"Excavator","model":"Liebherr R9400","icon":"⛏️","symbol":"diamond","easting":22685,"northing":15325,
     "shift_status":"Operating","operator":"J. Thompson","assignment":"Pit 1 – Strip advance bench 18, push to waste",
     "smu_hours":14820,"fuel_level":72,
     "prev_notes":"Minor hydraulic seep on bucket cylinder – monitor only. Changed teeth at 06:30. No lost time."},
    {"id":"EX-02","type":"Excavator","model":"Komatsu PC5500","icon":"⛏️","symbol":"diamond","easting":22855,"northing":15485,
     "shift_status":"Available","operator":"S. Patel","assignment":"Pit 2 – Coal loading, target 3,200 t this shift",
     "smu_hours":9340,"fuel_level":88,
     "prev_notes":"Completed scheduled 500hr service overnight. All systems checked. Ready for full shift."},
    {"id":"HT-01","type":"Haul Truck","model":"Cat 793F","icon":"🚛","symbol":"square","easting":22725,"northing":15285,
     "shift_status":"Operating","operator":"K. Wilson","assignment":"Pit 1 → Waste Dump 1 (overburden)",
     "smu_hours":22100,"fuel_level":65,
     "prev_notes":"RF tyre pressure low – inflated to spec at shift change. Monitor closely."},
    {"id":"HT-02","type":"Haul Truck","model":"Cat 793F","icon":"🚛","symbol":"square","easting":22765,"northing":15265,
     "shift_status":"Operating","operator":"M. Chen","assignment":"Pit 1 → Waste Dump 1 (overburden)",
     "smu_hours":19870,"fuel_level":80,
     "prev_notes":"No issues reported. Completed 480 t in last shift."},
    {"id":"HT-03","type":"Haul Truck","model":"Cat 793F","icon":"🚛","symbol":"square","easting":22805,"northing":15245,
     "shift_status":"Operating","operator":"B. Nguyen","assignment":"Pit 2 → ROM Pad (coal)",
     "smu_hours":17540,"fuel_level":91,
     "prev_notes":"Payload system recalibrated last shift – reading correctly now."},
    {"id":"HT-04","type":"Haul Truck","model":"Cat 793F","icon":"🚛","symbol":"square","easting":22200,"northing":14780,
     "shift_status":"Maintenance","operator":"Unassigned","assignment":"Workshop – 1000hr scheduled service",
     "smu_hours":22000,"fuel_level":40,
     "prev_notes":"In for 1000hr service. ETA back to fleet: 14:00 today. Tyre rotation also being done."},
    {"id":"HT-05","type":"Haul Truck","model":"Cat 793F","icon":"🚛","symbol":"square","easting":22845,"northing":15225,
     "shift_status":"Operating","operator":"C. O'Brien","assignment":"Pit 2 → ROM Pad (coal)",
     "smu_hours":11230,"fuel_level":77,
     "prev_notes":"All good. Strong performance last shift."},
    {"id":"DR-01","type":"Drill Rig","model":"Atlas Copco Pit Viper 271","icon":"🔩","symbol":"triangle-up","easting":22605,"northing":15405,
     "shift_status":"Operating","operator":"T. Roberts","assignment":"Blast Pattern BP-24A – 14 holes remaining",
     "smu_hours":8910,"fuel_level":68,
     "prev_notes":"Drill steel changed. Pattern on track for noon completion. Blasting scheduled 13:00."},
    {"id":"DR-02","type":"Drill Rig","model":"Atlas Copco Pit Viper 271","icon":"🔩","symbol":"triangle-up","easting":22660,"northing":15455,
     "shift_status":"Standby","operator":"R. Singh","assignment":"Standby – move to BP-25 post-blast",
     "smu_hours":7650,"fuel_level":95,
     "prev_notes":"Ready. Awaiting BP-24A completion before relocating."},
    {"id":"GR-01","type":"Grader","model":"Cat 16M","icon":"🚧","symbol":"circle-x","easting":22955,"northing":15155,
     "shift_status":"Operating","operator":"D. Harris","assignment":"Haul road maintenance – northern ramp to Pit 1",
     "smu_hours":6300,"fuel_level":82,
     "prev_notes":"Post-rain maintenance on northern ramp. Road in good condition for shift start."},
    {"id":"WT-01","type":"Water Truck","model":"Cat 785C Water","icon":"💧","symbol":"circle","easting":22505,"northing":15205,
     "shift_status":"Operating","operator":"R. Gallagher","assignment":"Dust suppression – main haul road and ROM approach",
     "smu_hours":5140,"fuel_level":88,
     "prev_notes":"Dust levels elevated after yesterday's wind. Prioritise ROM approach road."},
    {"id":"D11-01","type":"Dozer","model":"Cat D11","icon":"🔨","symbol":"pentagon","easting":22705,"northing":15455,
     "shift_status":"Available","operator":"A. Morrison","assignment":"Pit 1 floor cleanup – push loose on bench 16",
     "smu_hours":10890,"fuel_level":73,
     "prev_notes":"Completed waste dump push-up yesterday. All good – ready for pit floor."},
]

# ── Mine Zone polygons (easting / northing) ───────────────────────────────────
MINE_ZONES = {
    "Pit 1 (Active)":     {"coords":[(22580,15250),(22580,15530),(22905,15530),(22905,15250)],"fill":"rgba(255,107,53,0.10)","line":"#FF6B35","dash":"solid"},
    "Pit 2 (Expansion)":  {"coords":[(22760,15440),(22760,15630),(23060,15630),(23060,15440)],"fill":"rgba(33,150,243,0.10)","line":"#2196F3","dash":"solid"},
    "Waste Dump 1":       {"coords":[(22080,15390),(22080,15660),(22390,15660),(22390,15390)],"fill":"rgba(121,85,72,0.18)","line":"#795548","dash":"solid"},
    "ROM Pad":            {"coords":[(23110,14990),(23110,15210),(23410,15210),(23410,14990)],"fill":"rgba(76,175,80,0.15)","line":"#4CAF50","dash":"solid"},
    "Workshop / Parking": {"coords":[(22040,14680),(22040,14900),(22370,14900),(22370,14680)],"fill":"rgba(158,158,158,0.15)","line":"#9E9E9E","dash":"dot"},
    "Haul Road Corridor": {"coords":[(22390,14780),(22390,14840),(23110,14840),(23110,14780)],"fill":"rgba(200,200,100,0.10)","line":"#CDDC39","dash":"dot"},
}

# ── Safety / Hazard Layer polygons ────────────────────────────────────────────
SAFETY_LAYERS = {
    "⚠️ Blast Exclusion – BP-24A":          {"coords":[(22530,15330),(22530,15490),(22690,15490),(22690,15330)],"fill":"rgba(244,67,54,0.28)","line":"#F44336","dash":"dash","severity":"critical","description":"300 m exclusion zone active during drilling. Blast scheduled 13:00 today."},
    "🪨 Geohazard – Pit 1 North Highwall":   {"coords":[(22580,15490),(22580,15530),(22905,15530),(22905,15490)],"fill":"rgba(255,152,0,0.30)","line":"#FF9800","dash":"dash","severity":"high","description":"Geotech radar monitoring active. Cracking on bench 20. No access without geotechnical sign-off."},
    "💧 Sump – Pit 1 Floor":                 {"coords":[(22685,15285),(22685,15340),(22745,15340),(22745,15285)],"fill":"rgba(0,188,212,0.40)","line":"#00BCD4","dash":"dash","severity":"medium","description":"Active sump. Water depth ~0.8 m. Pump operating. 15 m vehicle standoff required."},
    "📡 Geotech Radar – GR Zone 3":          {"coords":[(22825,15485),(22825,15535),(22890,15535),(22890,15485)],"fill":"rgba(156,39,176,0.28)","line":"#9C27B0","dash":"dash","severity":"medium","description":"SSR radar monitoring sector. Check displacement readings before shift entry."},
    "🔒 Exclusion – Geotech Investigation":  {"coords":[(22600,15550),(22600,15620),(22700,15620),(22700,15550)],"fill":"rgba(244,67,54,0.20)","line":"#E91E63","dash":"dashdot","severity":"high","description":"Active geotechnical investigation. No plant or personnel without Geotech approval."},
}

MEETING_STEPS = [
    {"id":1,"title":"Overnight Incidents","icon":"🔴"},
    {"id":2,"title":"JSA & Permits",       "icon":"📋"},
    {"id":3,"title":"Actions Review",      "icon":"✅"},
    {"id":4,"title":"Production Numbers",  "icon":"📊"},
    {"id":5,"title":"Geotechnical Update", "icon":"🪨"},
    {"id":6,"title":"Equipment Walkthrough","icon":"🚛"},
    {"id":7,"title":"Today's Plan Commit", "icon":"📅"},
    {"id":8,"title":"Close & Send Report", "icon":"📧"},
]

# ══════════════════════════════════════════════════════════════════════════════
# DEFAULT DATA FACTORIES
# ══════════════════════════════════════════════════════════════════════════════

def _default_kpis():
    today = date.today()
    return pd.DataFrame({
        "Date":            [str(today - timedelta(days=i)) for i in range(14)],
        "BCM Moved":       [48200,45800,51200,42900,54100,49750,52500,47300,50100,44800,53200,48900,46500,51800],
        "Coal Tonnes":     [12450,11800,13200,10900,14100,12750,13500,11200,13800,10500,14500,12100,11900,13100],
        "Stripping Ratio": [8.2,7.9,8.5,8.1,7.8,8.3,8.0,8.6,7.7,8.4,7.6,8.2,8.0,8.3],
        "Advance Rate m":  [42,38,45,35,48,41,44,37,46,33,49,40,43,42],
        "Drill Metres":    [320,290,345,270,380,310,355,285,365,260,395,305,320,340],
        "Target BCM":      [50000]*14,
        "Target Coal":     [13000]*14,
    })

def _default_actions():
    return pd.DataFrame([
        {"ID":"ACT-001","Raised":str(date.today()-timedelta(days=3)),"Description":"Inspect northern highwall cracking – sector 7B","Owner":"Geotech Team","Status":"In Progress","Due":str(date.today())},
        {"ID":"ACT-002","Raised":str(date.today()-timedelta(days=5)),"Description":"Service WT-01 spray nozzles – reduced output reported","Owner":"Maintenance","Status":"Complete","Due":str(date.today()-timedelta(days=1))},
        {"ID":"ACT-003","Raised":str(date.today()-timedelta(days=1)),"Description":"Review haul road crossing signage – near ROM entrance","Owner":"Mine Supervisor","Status":"Open","Due":str(date.today())},
        {"ID":"ACT-004","Raised":str(date.today()-timedelta(days=7)),"Description":"Update blast exclusion zone fence markers – BP-24 area","Owner":"Blast Crew","Status":"Open","Due":str(date.today()+timedelta(days=1))},
        {"ID":"ACT-005","Raised":str(date.today()-timedelta(days=2)),"Description":"Verify HT-04 tyre replacement schedule with procurement","Owner":"Mine Planner","Status":"Complete","Due":str(date.today()-timedelta(days=1))},
    ])

def _default_jsa():
    return pd.DataFrame([
        {"Task":"Overburden Excavation – Pit 1","JSA Ref":"JSA-2025-041","Personnel":"Shift A – 12 persons","Risk Level":"High","Reviewed":True,"Reviewer":"Mine Supervisor","Expiry":str(date.today())},
        {"Task":"Drill & Blast – Pattern BP-24A","JSA Ref":"JSA-2025-042","Personnel":"Blast Crew – 4 persons","Risk Level":"Critical","Reviewed":True,"Reviewer":"Blast Supervisor","Expiry":str(date.today())},
        {"Task":"Coal Loading & Haulage – Pit 2","JSA Ref":"JSA-2025-039","Personnel":"Shift B – 8 persons","Risk Level":"High","Reviewed":True,"Reviewer":"Mine Supervisor","Expiry":str(date.today())},
        {"Task":"Haul Road Maintenance (Grader)","JSA Ref":"JSA-2025-035","Personnel":"GR-01 Operator","Risk Level":"Medium","Reviewed":False,"Reviewer":"—","Expiry":str(date.today())},
        {"Task":"Dust Suppression Operations","JSA Ref":"JSA-2025-030","Personnel":"WT-01 Operator","Risk Level":"Low","Reviewed":True,"Reviewer":"Shift Supervisor","Expiry":str(date.today()+timedelta(days=2))},
    ])

def _default_incidents():
    return pd.DataFrame([{
        "Time":"02:15","Date":str(date.today()-timedelta(days=1)),"Shift":"Night","Category":"Near Miss","Severity":"Medium",
        "Description":"HT-03 operator reported loss of road edge visibility on northern ramp descent due to dust. Slowed to standstill safely.",
        "Immediate Action":"Reduced speed limit to 15 km/h on northern ramp. WT-01 dispatched for suppression.",
        "Status":"Under Investigation","Reported By":"HT-03 Operator",
    }])

def _default_handover():
    return pd.DataFrame([
        {"Shift":"Night","Date":str(date.today()-timedelta(days=1)),"Equipment":"EX-01","Notes":"Hydraulic seep on bucket cylinder – marked for monitoring. Crew aware.","Author":"Night Supervisor"},
        {"Shift":"Night","Date":str(date.today()-timedelta(days=1)),"Equipment":"HT-01","Notes":"RF tyre pressure low – inflated. Watch closely first 2 hours.","Author":"Night Supervisor"},
        {"Shift":"Night","Date":str(date.today()-timedelta(days=1)),"Equipment":"DR-01","Notes":"14 holes remaining on BP-24A. Pattern on schedule for 12:00 completion.","Author":"Night Supervisor"},
        {"Shift":"Night","Date":str(date.today()-timedelta(days=1)),"Equipment":"HT-04","Notes":"Pulled for 1000hr service. Maintenance expects return by 14:00.","Author":"Night Supervisor"},
        {"Shift":"Night","Date":str(date.today()-timedelta(days=1)),"Equipment":"GENERAL","Notes":"Northern ramp near-miss logged. Geotech monitoring on sector 7B showing 2 mm displacement overnight – escalated to morning meeting.","Author":"Night Supervisor"},
    ])

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════

def init_session_state():
    defaults = {
        "page":             "🏗️ Morning Meeting",
        "meeting_step":     1,
        "steps_complete":   set(),
        "fleet":            [e.copy() for e in BASE_FLEET],
        "fleet_updates":    {},
        "kpi_data":         _default_kpis(),
        "actions":          _default_actions(),
        "jsa_data":         _default_jsa(),
        "incidents":        _default_incidents(),
        "handover_notes":   _default_handover(),
        "meeting_notes":    {},
        "show_layers":      {k: True for k in SAFETY_LAYERS},
        "show_zones":       True,
        "show_equipment":   True,
        "selected_equip":   None,
        "map_markers":      [],
        "gps_offset":       0,
        "attendees":        "Mine Planner, Mine Supervisor, Geotech Engineer, Blast Coordinator, Maintenance Foreman",
        "last_report":      "",
        "report_generated": False,
        "drone_images":     {},
        "topo_image":       None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session_state()

# ══════════════════════════════════════════════════════════════════════════════
# TOPOGRAPHIC MAP GENERATION
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner=False)
def _elevation_grid():
    """Generate a realistic synthetic open-cut mine topography (cached)."""
    e = np.linspace(E_MIN, E_MAX, 160)
    n = np.linspace(N_MIN, N_MAX, 130)
    E, N = np.meshgrid(e, n)
    Z = 198.0 * np.ones_like(E)
    # Pit 1 – main active pit
    Z -= 88 * np.exp(-(((E-22742)/285)**2 + ((N-15390)/205)**2) * 2.2)
    # Pit 2 – newer, shallower
    Z -= 44 * np.exp(-(((E-22910)/185)**2 + ((N-15535)/130)**2) * 2.8)
    # Waste dump mound
    Z += 38 * np.exp(-(((E-22235)/155)**2 + ((N-15525)/125)**2) * 2.0)
    # ROM pad plateau
    Z +=  6 * np.exp(-(((E-23260)/180)**2 + ((N-15100)/120)**2) * 1.5)
    # Terrain undulation
    Z += 5 * np.sin((E-22000)/220) * np.cos((N-14500)/190)
    Z += 3 * np.cos((E-22000)/160) + 2 * np.sin((N-14500)/140)
    # Haul road depression
    road = (np.abs(N-14810) < 40) & (E > 22380) & (E < 23120)
    Z[road] -= 3
    return e, n, Z


def build_topo_figure(mine_site, show_zones=True, active_safety_layers=None,
                      show_equipment=True, highlighted_equip=None,
                      map_markers=None, fleet=None, gps_offset=0):
    e_vals, n_vals, Z = _elevation_grid()
    if active_safety_layers is None: active_safety_layers = {}
    if map_markers is None: map_markers = []
    if fleet is None: fleet = BASE_FLEET

    fig = go.Figure()

    # Topo contour
    fig.add_trace(go.Contour(
        z=Z, x=e_vals, y=n_vals,
        colorscale=[
            [0.00,"#3d2b1f"],[0.15,"#5c3d28"],[0.30,"#7a5230"],
            [0.45,"#967a4a"],[0.60,"#b8a060"],[0.75,"#cfc080"],
            [0.90,"#e8e0a8"],[1.00,"#f5f0d0"],
        ],
        contours=dict(start=110, end=232, size=5, showlabels=True,
                      labelfont=dict(size=8, color="rgba(255,255,255,0.55)")),
        colorbar=dict(title=dict(text="Elevation (m RL)", font=dict(color="white", size=11)),
                      tickfont=dict(color="white", size=9), thickness=10, len=0.5, x=1.01),
        line=dict(width=0.6, color="rgba(255,255,255,0.22)"),
        name="Topography",
        hovertemplate="E: %{x:.0f} m | N: %{y:.0f} m | Elev: %{z:.1f} m RL<extra>Topo</extra>",
    ))

    # Mine zones
    if show_zones:
        for zname, zd in MINE_ZONES.items():
            xs = [c[0] for c in zd["coords"]] + [zd["coords"][0][0]]
            ys = [c[1] for c in zd["coords"]] + [zd["coords"][0][1]]
            fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", fill="toself",
                fillcolor=zd["fill"], line=dict(color=zd["line"], width=2, dash=zd["dash"]),
                name=zname, hoverinfo="text", text=zname, showlegend=True))
            cx = sum(c[0] for c in zd["coords"]) / len(zd["coords"])
            cy = sum(c[1] for c in zd["coords"]) / len(zd["coords"])
            fig.add_annotation(x=cx, y=cy, text=f"<b>{zname}</b>", showarrow=False,
                font=dict(size=9, color=zd["line"]), bgcolor="rgba(10,20,30,0.7)", borderpad=2)

    # Safety/hazard layers
    for lname, ld in SAFETY_LAYERS.items():
        if active_safety_layers.get(lname, False):
            xs = [c[0] for c in ld["coords"]] + [ld["coords"][0][0]]
            ys = [c[1] for c in ld["coords"]] + [ld["coords"][0][1]]
            fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", fill="toself",
                fillcolor=ld["fill"], line=dict(color=ld["line"], width=2.5, dash=ld["dash"]),
                name=lname, hoverinfo="text",
                text=f"{lname}<br>{ld['description']}", showlegend=True))

    # Equipment markers
    status_color = {"Operating":"#4CAF50","Maintenance":"#F44336","Available":"#FF9800","Standby":"#2196F3"}
    if show_equipment:
        for eq in fleet:
            np.random.seed(hash(eq["id"]) % 2**31)
            je = int(np.random.randint(-5,6)) * (gps_offset % 3)
            jn = int(np.random.randint(-5,6)) * (gps_offset % 3)
            eq_e = eq["easting"] + je
            eq_n = eq["northing"] + jn
            upd    = st.session_state.fleet_updates.get(eq["id"], {})
            status = upd.get("status", eq["shift_status"])
            assign = upd.get("assignment", eq["assignment"])
            col    = status_color.get(status, "#9E9E9E")
            is_hl  = (highlighted_equip == eq["id"])

            if is_hl:
                fig.add_trace(go.Scatter(x=[eq_e], y=[eq_n], mode="markers",
                    marker=dict(size=40, color="rgba(255,215,0,0.18)", symbol="circle",
                                line=dict(color="#FFD700", width=2)),
                    showlegend=False, hoverinfo="skip"))

            fig.add_trace(go.Scatter(
                x=[eq_e], y=[eq_n], mode="markers+text",
                marker=dict(size=22 if is_hl else 14, color=col, symbol=eq["symbol"],
                            line=dict(color="#FFD700" if is_hl else "white", width=3 if is_hl else 2)),
                text=[eq["id"]], textposition="top center",
                textfont=dict(size=9, color="white"),
                name=f"{eq['id']} ({status})",
                hovertemplate=(f"<b>{eq['id']} – {eq['model']}</b><br>Status: {status}<br>"
                               f"Operator: {eq['operator']}<br>E:{eq_e} | N:{eq_n}<br>"
                               f"<i>{assign[:55]}{'…' if len(assign)>55 else ''}</i><extra></extra>"),
                showlegend=False,
            ))

    # Custom map markers
    for m in map_markers:
        fig.add_trace(go.Scatter(
            x=[m["easting"]], y=[m["northing"]], mode="markers+text",
            marker=dict(size=18, color=m.get("color","#FFD700"), symbol="star",
                        line=dict(color="white", width=1)),
            text=[m.get("label","")], textposition="top center",
            textfont=dict(size=9, color="white"), name=m.get("label","Marker"),
            hovertemplate=f"{m.get('label','Marker')}<br>E:{m['easting']} N:{m['northing']}<extra></extra>",
            showlegend=False,
        ))

    # Annotations
    fig.add_annotation(x=E_MAX-60, y=N_MAX-50, text="<b>N ↑</b>", showarrow=False,
        font=dict(size=14, color="white"), bgcolor="rgba(0,0,0,0.5)", borderpad=4,
        borderwidth=1, bordercolor="rgba(255,255,255,0.3)")
    fig.add_annotation(x=E_MIN+60, y=N_MAX-50, text="● GPS LIVE", showarrow=False,
        font=dict(size=10, color="#4CAF50"), bgcolor="rgba(0,30,0,0.7)",
        borderpad=4, borderwidth=1, bordercolor="#4CAF50")

    fig.update_layout(
        height=560, plot_bgcolor="#0a141e", paper_bgcolor="#0a141e",
        font=dict(color="white", size=11),
        legend=dict(bgcolor="rgba(10,20,30,0.85)", bordercolor="rgba(255,255,255,0.2)",
                    borderwidth=1, font=dict(size=9), x=0.01, y=0.01,
                    xanchor="left", yanchor="bottom"),
        xaxis=dict(title="Easting (m)", gridcolor="rgba(255,255,255,0.07)",
                   showgrid=True, range=[E_MIN, E_MAX], tickfont=dict(size=9)),
        yaxis=dict(title="Northing (m)", gridcolor="rgba(255,255,255,0.07)",
                   showgrid=True, range=[N_MIN, N_MAX], scaleanchor="x", scaleratio=1,
                   tickfont=dict(size=9)),
        margin=dict(l=65, r=80, t=45, b=55),
        title=dict(text=f"<b>{mine_site}</b>  ·  Survey Topo  ·  {date.today().strftime('%A %d %B %Y')}",
                   font=dict(size=13, color="white"), x=0.0, xanchor="left"),
        hoverlabel=dict(bgcolor="#1a2a3a", font_size=12, font_color="white"),
        uirevision="stable",
    )
    return fig

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

def render_sidebar():
    with st.sidebar:
        st.markdown(
            '<div style="font-size:1.5rem;font-weight:900;color:#e63946;letter-spacing:3px">⛏ MOS</div>'
            '<div style="color:#6a8a9a;font-size:0.72rem;letter-spacing:2px;margin-bottom:0.8rem">MINEPLAN OC  ·  v2.0</div>',
            unsafe_allow_html=True)

        mine_site = st.selectbox("Mine Site", MINE_SITES, key="mine_site_sel", label_visibility="collapsed")
        pwd = st.text_input("Access Code", type="password", placeholder="Enter access code…", label_visibility="collapsed")

        if pwd not in ACCESS_CODES:
            st.markdown(
                '<div style="background:rgba(230,57,70,0.12);border-left:3px solid #e63946;'
                'padding:8px 10px;border-radius:6px;color:#e07070;font-size:0.82rem">'
                '🔐 Enter access code to unlock<br>'
                '<span style="color:#557a8a;font-size:0.78rem">mos2025 · super2025 · viewer2025</span></div>',
                unsafe_allow_html=True)
            st.stop()

        role_label, role = ACCESS_CODES[pwd]
        st.markdown(
            f'<div style="background:rgba(76,175,80,0.12);border-left:3px solid #4CAF50;'
            f'padding:6px 10px;border-radius:6px;font-size:0.82rem;color:#81C784;margin-bottom:0.5rem">'
            f'✓ {role_label}</div>', unsafe_allow_html=True)

        st.markdown("---")

        nav_options = ["🏗️ Morning Meeting","⚙️  Setup & Data","📊 KPI Dashboard","🔄 Shift Handover","📄 Reports"]
        page = st.radio("Navigate", nav_options, key="nav_radio", label_visibility="collapsed",
                        index=nav_options.index(st.session_state.page) if st.session_state.page in nav_options else 0)
        st.session_state.page = page

        st.markdown("---")

        if "Morning Meeting" in page:
            st.markdown("**📋 Meeting Progress**")
            for step in MEETING_STEPS:
                sid        = step["id"]
                is_active  = (sid == st.session_state.meeting_step)
                is_done    = (sid in st.session_state.steps_complete)
                btn_type   = "primary" if is_active else "secondary"
                tick       = "✓ " if is_done else ("▶ " if is_active else "○ ")
                if st.button(f"{step['icon']} {tick}{step['title']}", key=f"snav_{sid}",
                             use_container_width=True, type=btn_type):
                    st.session_state.meeting_step = sid
                    st.rerun()

            progress = len(st.session_state.steps_complete) / len(MEETING_STEPS)
            st.progress(progress, text=f"{len(st.session_state.steps_complete)}/{len(MEETING_STEPS)} complete")
            st.markdown("---")

            # Map layer toggles
            st.markdown("**🗺️ Map Layers**")
            ca, cb = st.columns(2)
            with ca:
                st.session_state.show_zones     = st.toggle("Zones",    value=st.session_state.show_zones,     key="tog_zones")
                st.session_state.show_equipment = st.toggle("Fleet GPS",value=st.session_state.show_equipment, key="tog_equip")
            with cb:
                all_on = all(st.session_state.show_layers.values())
                label  = "⚠️ Hide Hazards" if all_on else "⚠️ Show Hazards"
                if st.button(label, key="tog_all_hz", use_container_width=True,
                             type="primary" if all_on else "secondary"):
                    nv = not all_on
                    for k in st.session_state.show_layers:
                        st.session_state.show_layers[k] = nv
                    st.rerun()

            with st.expander("Individual hazard layers"):
                for lname in SAFETY_LAYERS:
                    st.session_state.show_layers[lname] = st.checkbox(
                        lname, value=st.session_state.show_layers[lname], key=f"lyr_{hash(lname)}")

            st.markdown("---")

        # Quick fleet stats
        ops   = sum(1 for e in st.session_state.fleet
                    if st.session_state.fleet_updates.get(e["id"],{}).get("status",e["shift_status"]) == "Operating")
        maint = sum(1 for e in st.session_state.fleet
                    if st.session_state.fleet_updates.get(e["id"],{}).get("status",e["shift_status"]) == "Maintenance")
        st.markdown(
            f'<div style="font-size:0.8rem;color:#8fa8c0;line-height:2">'
            f'🟢 Operating: <b style="color:#4CAF50">{ops}</b> &nbsp; '
            f'🔴 Maintenance: <b style="color:#F44336">{maint}</b><br>'
            f'📅 {date.today().strftime("%d %b %Y")}  ·  Shift 06:00</div>',
            unsafe_allow_html=True)

    return mine_site, role

# ══════════════════════════════════════════════════════════════════════════════
# SHARED STEP UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

def step_header(step):
    st.markdown(
        f'<div style="background:rgba(33,150,243,0.12);border-left:4px solid #2196F3;'
        f'padding:0.8rem 1rem;border-radius:8px;margin-bottom:0.8rem">'
        f'<span style="font-size:1.3rem">{step["icon"]}</span> '
        f'<span style="font-size:1.05rem;font-weight:700;color:white"> Step {step["id"]}: {step["title"]}</span>'
        f'</div>', unsafe_allow_html=True)


def complete_step_button(step_id):
    c1, c2 = st.columns([3,1])
    with c1:
        note = st.text_area("Notes for this step (optional)",
                            value=st.session_state.meeting_notes.get(step_id,""),
                            height=65, key=f"note_{step_id}")
        st.session_state.meeting_notes[step_id] = note
    with c2:
        st.write("")
        if step_id not in st.session_state.steps_complete:
            if st.button("✓ Complete", key=f"done_{step_id}", type="primary", use_container_width=True):
                st.session_state.steps_complete.add(step_id)
                if step_id < len(MEETING_STEPS):
                    st.session_state.meeting_step = step_id + 1
                st.rerun()
        else:
            st.success("✓ Done")
            if st.button("↩ Reopen", key=f"reopen_{step_id}", use_container_width=True):
                st.session_state.steps_complete.discard(step_id)
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# MEETING STEP RENDERERS
# ══════════════════════════════════════════════════════════════════════════════

# ── Step 1 ────────────────────────────────────────────────────────────────────
def render_step_1():
    step_header(MEETING_STEPS[0])

    gen = st.session_state.handover_notes[st.session_state.handover_notes["Equipment"]=="GENERAL"]
    if not gen.empty:
        st.markdown("**📟 Night Shift – General Handover:**")
        for _, r in gen.iterrows():
            st.markdown(
                f'<div class="handover-note">'
                f'<div class="handover-label">🌙 Night Shift – {r["Author"]}</div>'
                f'{r["Notes"]}</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-heading">Incidents & Near Misses</div>', unsafe_allow_html=True)
    sev_cls = {"Critical":"badge-critical","High":"badge-high","Medium":"badge-medium","Low":"badge-low"}
    for _, inc in st.session_state.incidents.iterrows():
        card_cls = "equip-maintenance" if inc["Severity"] in ["Critical","High"] else "equip-available"
        st.markdown(
            f'<div class="equip-card {card_cls}">'
            f'<div style="display:flex;justify-content:space-between;align-items:center">'
            f'<b style="color:white">{inc["Time"]} – {inc["Category"]}</b>'
            f'<span class="badge {sev_cls.get(inc["Severity"],"badge-low")}">{inc["Severity"]}</span></div>'
            f'<div style="margin:6px 0;color:#c8d4e0">{inc["Description"]}</div>'
            f'<div style="font-size:0.82rem;color:#8fa8c0">⚡ {inc["Immediate Action"]}</div>'
            f'<div style="font-size:0.78rem;color:#6a8a9a;margin-top:4px">'
            f'By: {inc["Reported By"]}  ·  Status: {inc["Status"]}</div></div>',
            unsafe_allow_html=True)

    with st.expander("➕ Log New Incident / Near Miss"):
        with st.form("inc_form"):
            ca, cb, cc = st.columns(3)
            with ca: t  = st.text_input("Time", value=datetime.now().strftime("%H:%M"))
            with cb: cat= st.selectbox("Category", ["Near Miss","First Aid","Property Damage","Environmental","LTI"])
            with cc: sev= st.selectbox("Severity", ["Low","Medium","High","Critical"])
            desc = st.text_area("Description", height=70)
            act  = st.text_area("Immediate Actions Taken", height=55)
            by   = st.text_input("Reported By")
            if st.form_submit_button("Log Incident", type="primary"):
                new = pd.DataFrame([{"Time":t,"Date":str(date.today()),"Shift":"Day","Category":cat,
                    "Severity":sev,"Description":desc,"Immediate Action":act,"Status":"Open","Reported By":by}])
                st.session_state.incidents = pd.concat([st.session_state.incidents, new], ignore_index=True)
                st.success("Incident logged.")
                st.rerun()
    st.divider()
    complete_step_button(1)


# ── Step 2 ────────────────────────────────────────────────────────────────────
def render_step_2():
    step_header(MEETING_STEPS[1])
    risk_col = {"Critical":"#F44336","High":"#FF9800","Medium":"#FFC107","Low":"#4CAF50"}
    pending = st.session_state.jsa_data[~st.session_state.jsa_data["Reviewed"]]
    if not pending.empty:
        st.warning(f"⚠️ {len(pending)} JSA(s) not yet reviewed – sign off before work commences.")

    for _, r in st.session_state.jsa_data.iterrows():
        col = risk_col.get(r["Risk Level"],"#9E9E9E")
        rev = "✅" if r["Reviewed"] else "❌"
        st.markdown(
            f'<div class="equip-card" style="border-left:4px solid {col}">'
            f'<div style="display:flex;justify-content:space-between">'
            f'<b style="color:white">{r["Task"]}</b>'
            f'<span style="color:{col};font-weight:700">{r["Risk Level"]}</span></div>'
            f'<div style="color:#8fa8c0;font-size:0.82rem;margin:4px 0">'
            f'{r["JSA Ref"]}  ·  {r["Personnel"]}  ·  Expiry: {r["Expiry"]}</div>'
            f'<div>{rev} Reviewed by: <b style="color:#a0c0e0">{r["Reviewer"]}</b></div></div>',
            unsafe_allow_html=True)

    if st.button("✅ Mark all JSAs reviewed", type="primary"):
        st.session_state.jsa_data["Reviewed"] = True
        st.session_state.jsa_data["Reviewer"] = "Mine Supervisor"
        st.success("All JSAs marked reviewed.")
        st.rerun()
    st.divider()
    complete_step_button(2)


# ── Step 3 ────────────────────────────────────────────────────────────────────
def render_step_3():
    step_header(MEETING_STEPS[2])
    open_c = (st.session_state.actions["Status"] != "Complete").sum()
    if open_c:
        st.warning(f"📌 {open_c} open action(s) – review and update status.")
    edited = st.data_editor(
        st.session_state.actions, use_container_width=True,
        column_config={"Status": st.column_config.SelectboxColumn(
            options=["Open","In Progress","Complete","Overdue"])},
        num_rows="dynamic", key="act_editor")
    st.session_state.actions = edited
    st.divider()
    complete_step_button(3)


# ── Step 4 ────────────────────────────────────────────────────────────────────
def render_step_4():
    step_header(MEETING_STEPS[3])
    df = st.session_state.kpi_data
    latest, prev = df.iloc[0], df.iloc[1]
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric("BCM Yesterday",   f"{int(latest['BCM Moved']):,}", f"{int(latest['BCM Moved']-latest['Target BCM']):+,} vs target")
    with c2: st.metric("Coal Tonnes",     f"{int(latest['Coal Tonnes']):,} t", f"{int(latest['Coal Tonnes']-latest['Target Coal']):+,} vs target")
    with c3: st.metric("Stripping Ratio", f"{latest['Stripping Ratio']:.2f}", f"{latest['Stripping Ratio']-prev['Stripping Ratio']:+.2f}")
    with c4: st.metric("Advance Rate",    f"{int(latest['Advance Rate m'])} m", f"{int(latest['Advance Rate m']-prev['Advance Rate m']):+} m")

    st.markdown('<div class="section-heading">14-Day Trend</div>', unsafe_allow_html=True)
    t1,t2,t3 = st.tabs(["BCM & Coal","Stripping Ratio","Drill Metres"])
    with t1: st.line_chart(df.set_index("Date")[["BCM Moved","Target BCM","Coal Tonnes","Target Coal"]])
    with t2: st.line_chart(df.set_index("Date")[["Stripping Ratio"]])
    with t3: st.line_chart(df.set_index("Date")[["Drill Metres"]])
    st.divider()
    complete_step_button(4)


# ── Step 5 ────────────────────────────────────────────────────────────────────
def render_step_5():
    step_header(MEETING_STEPS[4])
    st.warning("⚠️ **Active Advisory** – Pit 1 North Highwall (Sector 7B): Cracking on bench 20. "
               "SSR radar: 2 mm overnight displacement. Monitor continuously.")
    st.markdown('<div class="section-heading">Hazard Layer Status</div>', unsafe_allow_html=True)
    sev_icon = {"critical":"🔴","high":"🟠","medium":"🟡","low":"🟢"}
    for lname, ld in SAFETY_LAYERS.items():
        active = st.session_state.show_layers.get(lname, True)
        st.markdown(
            f'<div class="equip-card" style="border-left:4px solid {ld["line"]}">'
            f'<div style="display:flex;justify-content:space-between">'
            f'<span style="color:white;font-weight:700">{sev_icon.get(ld["severity"],"🟡")} {lname}</span>'
            f'<span style="font-size:0.8rem;color:{"#4CAF50" if active else "#F44336"}">'
            f'{"● Visible" if active else "○ Hidden"}</span></div>'
            f'<div style="font-size:0.84rem;color:#a0c0e0;margin-top:4px">{ld["description"]}</div></div>',
            unsafe_allow_html=True)
    st.info("💡 Toggle layers in the sidebar to show/hide on the topo map.")
    c1,c2,c3 = st.columns(3)
    with c1: st.metric("Pit 1 Sump Level","0.8 m","+0.1 m overnight")
    with c2: st.metric("Rainfall 24hr","4.2 mm","Clearing")
    with c3: st.metric("Wind Speed","12 km/h","NNW – Improving")
    st.divider()
    complete_step_button(5)


# ── Step 6 ────────────────────────────────────────────────────────────────────
def render_step_6():
    step_header(MEETING_STEPS[5])
    equip_ids = [e["id"] for e in st.session_state.fleet]
    sel_idx   = equip_ids.index(st.session_state.selected_equip) if st.session_state.selected_equip in equip_ids else 0
    selected  = st.selectbox("Select equipment to review:", equip_ids, index=sel_idx, key="eq_sel")
    st.session_state.selected_equip = selected

    eq  = next(e for e in st.session_state.fleet if e["id"] == selected)
    upd = st.session_state.fleet_updates.get(eq["id"], {})
    cur_status = upd.get("status", eq["shift_status"])
    cur_assign = upd.get("assignment", eq["assignment"])
    status_cls = {"Operating":"equip-operating","Maintenance":"equip-maintenance",
                  "Available":"equip-available","Standby":"equip-standby"}.get(cur_status,"equip-available")

    st.markdown(
        f'<div class="equip-card {status_cls}">'
        f'<div style="display:flex;justify-content:space-between;align-items:center">'
        f'<span style="font-size:1.1rem">{eq["icon"]}</span>'
        f'<b style="color:white;font-size:1rem"> {eq["id"]} – {eq["model"]}</b>'
        f'<span style="color:#8fa8c0;font-size:0.82rem">{eq["type"]}</span></div>'
        f'<div style="margin:6px 0;color:#a0c0e0">Operator: <b style="color:white">{eq["operator"]}</b></div>'
        f'<div style="font-size:0.8rem;color:#8fa8c0">'
        f'SMU: {eq["smu_hours"]:,} hrs  ·  Fuel: {eq["fuel_level"]}%  ·  '
        f'E {eq["easting"]} / N {eq["northing"]}</div></div>',
        unsafe_allow_html=True)

    prev_notes = st.session_state.handover_notes[st.session_state.handover_notes["Equipment"]==eq["id"]]
    if not prev_notes.empty:
        st.markdown("**📟 Night Shift Notes:**")
        for _, r in prev_notes.iterrows():
            st.markdown(
                f'<div class="handover-note"><div class="handover-label">🌙 {r["Author"]}</div>'
                f'{r["Notes"]}</div>', unsafe_allow_html=True)

    new_status = st.selectbox("Status",["Operating","Available","Maintenance","Standby"],
        index=["Operating","Available","Maintenance","Standby"].index(cur_status)
        if cur_status in ["Operating","Available","Maintenance","Standby"] else 0,
        key=f"st_{eq['id']}")
    new_assign = st.text_area("Assignment / Task", value=cur_assign, height=75, key=f"as_{eq['id']}")
    new_notes  = st.text_area("Day shift notes (carries to handover)", height=55,
        value=upd.get("day_notes",""), key=f"dn_{eq['id']}")

    if st.button(f"💾 Save {eq['id']}", type="primary", use_container_width=True):
        st.session_state.fleet_updates[eq["id"]] = {
            "status": new_status, "assignment": new_assign, "day_notes": new_notes}
        st.success(f"{eq['id']} updated.")
        st.rerun()

    with st.expander("📋 Full Fleet Summary"):
        rows = [{"ID":e["id"],"Type":e["type"],
                 "Status":st.session_state.fleet_updates.get(e["id"],{}).get("status",e["shift_status"]),
                 "Operator":e["operator"],
                 "Assignment":st.session_state.fleet_updates.get(e["id"],{}).get("assignment",e["assignment"])[:50]+"…"}
                for e in st.session_state.fleet]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.divider()
    complete_step_button(6)


# ── Step 7 ────────────────────────────────────────────────────────────────────
def render_step_7():
    step_header(MEETING_STEPS[6])
    st.info("Confirm today's targets and priorities. Equipment assignments set in Step 6.")
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("**Production Targets:**")
        st.number_input("BCM Target",          value=50000, step=500, key="plan_bcm")
        st.number_input("Coal Tonnes Target",  value=13000, step=100, key="plan_coal")
        st.number_input("Drill Metres Target", value=340,   step=10,  key="plan_drill")
    with c2:
        st.markdown("**Blast Schedule:**")
        st.selectbox("Blast Pattern", ["BP-24A (13:00 today)","BP-25 (Tomorrow)","No blast today"])
        st.time_input("Planned Blast Time", value=datetime.strptime("13:00","%H:%M").time())
        st.text_input("Blast Coordinator", value="T. Roberts")
    st.markdown("**Priorities & Special Instructions:**")
    st.text_area("Key focus areas for today's shift",
        value="1. Complete BP-24A drill pattern by 12:00 – blast at 13:00\n"
              "2. Maintain advance rate on Pit 1 bench 18\n"
              "3. Monitor HT-01 RF tyre – operator to report 2-hourly\n"
              "4. Geotech to re-check sector 7B at 10:00 and 14:00\n"
              "5. HT-04 returns from service at 14:00 – integrate into haul cycle",
        height=120, key="priorities")
    st.markdown("**Meeting Attendees:**")
    att = st.text_area("Attendees", value=st.session_state.attendees, height=55, key="att_in")
    st.session_state.attendees = att
    st.divider()
    complete_step_button(7)


# ── Step 8 ────────────────────────────────────────────────────────────────────
def render_step_8(mine_site):
    step_header(MEETING_STEPS[7])
    done = len(st.session_state.steps_complete)
    total = len(MEETING_STEPS)
    if done < total - 1:
        st.warning(f"⚠️ {total-1-done} step(s) not yet complete – you can still generate the report.")

    df = st.session_state.kpi_data
    latest = df.iloc[0]
    inc_lines = "\n".join(
        f"  • [{r['Severity']}] {r['Time']} – {r['Category']}: {r['Description'][:75]}…"
        for _, r in st.session_state.incidents.iterrows()) or "  No incidents."
    open_act = st.session_state.actions[st.session_state.actions["Status"] != "Complete"]
    act_lines = "\n".join(
        f"  • [{r['Status']}] {r['ID']}: {r['Description'][:65]}… (Owner: {r['Owner']})"
        for _, r in open_act.iterrows()) or "  No open actions."
    eq_lines = "\n".join(
        f"  • {e['id']} ({st.session_state.fleet_updates.get(e['id'],{}).get('status',e['shift_status'])}): "
        f"{st.session_state.fleet_updates.get(e['id'],{}).get('assignment',e['assignment'])[:55]}…"
        for e in st.session_state.fleet)
    note_lines = "\n".join(
        f"  Step {sid}: {txt[:100]}{'…' if len(txt)>100 else ''}"
        for sid,txt in st.session_state.meeting_notes.items() if txt.strip()) or "  No notes."
    steps_done = ", ".join(MEETING_STEPS[i-1]["title"] for i in sorted(st.session_state.steps_complete)) or "None"

    report = f"""
═══════════════════════════════════════════════════════════════
  MOS MinePlan OC – DAILY PLANNING MEETING MINUTES
  {mine_site}
  Generated: {datetime.now().strftime('%d %b %Y  %H:%M')}
═══════════════════════════════════════════════════════════════

ATTENDEES
  {st.session_state.attendees}

STEPS COMPLETED
  {steps_done}

─────────────────────────────────────────────
PRODUCTION REVIEW (Previous Day)
  BCM Moved:       {int(latest['BCM Moved']):,} bcm  (Target: {int(latest['Target BCM']):,})
  Coal Tonnes:     {int(latest['Coal Tonnes']):,} t   (Target: {int(latest['Target Coal']):,})
  Stripping Ratio: {latest['Stripping Ratio']:.2f}
  Advance Rate:    {int(latest['Advance Rate m'])} m

─────────────────────────────────────────────
INCIDENTS & NEAR MISSES
{inc_lines}

─────────────────────────────────────────────
OPEN ACTIONS
{act_lines}

─────────────────────────────────────────────
EQUIPMENT ASSIGNMENTS
{eq_lines}

─────────────────────────────────────────────
TODAY'S TARGETS
  BCM:   {st.session_state.get('plan_bcm', 50000):,} bcm
  Coal:  {st.session_state.get('plan_coal', 13000):,} t
  Drill: {st.session_state.get('plan_drill', 340)} m
  Blast: BP-24A at 13:00

─────────────────────────────────────────────
MEETING NOTES
{note_lines}

─────────────────────────────────────────────
  Auto-generated by MOS MinePlan OC
  Official meeting record – retain for audit purposes
═══════════════════════════════════════════════════════════════
""".strip()
    st.session_state.last_report = report

    c1,c2 = st.columns(2)
    with c1:
        if st.button("📄 Generate Report", type="primary", use_container_width=True):
            st.session_state.report_generated = True
            st.rerun()
    with c2:
        if st.session_state.report_generated:
            st.download_button("⬇️ Download Report (.txt)", data=report.encode(),
                file_name=f"MOS_MinePlan_{date.today()}.txt", mime="text/plain",
                use_container_width=True, type="primary")

    if st.session_state.report_generated:
        st.success("✅ Report ready. In production this is emailed to all attendees automatically and archived.")
        st.markdown(f'<div class="report-box">{report.replace(chr(10),"<br>")}</div>', unsafe_allow_html=True)
        export = pd.concat([
            st.session_state.incidents.assign(Section="Incidents"),
            st.session_state.actions.assign(Section="Actions"),
        ], ignore_index=True)
        st.download_button("⬇️ Full Data Export (.csv)", data=export.to_csv(index=False).encode(),
            file_name=f"MOS_Data_{date.today()}.csv", mime="text/csv")
    st.divider()
    complete_step_button(8)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: MORNING MEETING
# ══════════════════════════════════════════════════════════════════════════════

def page_morning_meeting(mine_site, role):
    st.markdown(
        f'<div class="mos-header">'
        f'<div><div class="mos-logo">⛏ MOS MinePlan OC</div>'
        f'<div class="mos-site">{mine_site}</div>'
        f'<div class="mos-subtitle">Daily Planning Meeting  ·  {date.today().strftime("%A %d %B %Y")}  ·  Shift Start 06:00</div></div>'
        f'<div style="margin-left:auto;text-align:right">'
        f'<span class="gps-live">● GPS LIVE</span><br>'
        f'<span style="font-size:0.73rem;color:#557a8a;margin-top:3px;display:block">'
        f'Updated {datetime.now().strftime("%H:%M:%S")}</span></div></div>',
        unsafe_allow_html=True)

    # Action row above the map
    gps_col, _, marker_col = st.columns([1,3,1])
    with gps_col:
        if st.button("🔄 Refresh GPS Feed", use_container_width=True):
            st.session_state.gps_offset += 1
            st.rerun()
    with marker_col:
        with st.popover("📍 Drop Marker", use_container_width=True):
            st.caption("In production: click directly on the topo to place. "
                       "GPS coordinates auto-captured from live feed.")
            mk_label = st.text_input("Label", key="mk_lbl")
            mc1,mc2  = st.columns(2)
            with mc1: mk_e = st.number_input("Easting",  value=22750, min_value=E_MIN, max_value=E_MAX, key="mk_e")
            with mc2: mk_n = st.number_input("Northing", value=15400, min_value=N_MIN, max_value=N_MAX, key="mk_n")
            mk_color = st.color_picker("Colour", "#FFD700", key="mk_col")
            if st.button("Drop Marker", type="primary", key="mk_add"):
                st.session_state.map_markers.append({
                    "label": mk_label or f"Marker {len(st.session_state.map_markers)+1}",
                    "easting": mk_e, "northing": mk_n, "color": mk_color})
                st.rerun()
            if st.session_state.map_markers:
                if st.button("🗑 Clear Markers", key="mk_clear"):
                    st.session_state.map_markers = []
                    st.rerun()

    # Main layout: map 3/5, step panel 2/5
    map_col, step_col = st.columns([3, 2], gap="medium")

    with map_col:
        hl = st.session_state.selected_equip if st.session_state.meeting_step == 6 else None
        fig = build_topo_figure(
            mine_site=mine_site,
            show_zones=st.session_state.show_zones,
            active_safety_layers=st.session_state.show_layers,
            show_equipment=st.session_state.show_equipment,
            highlighted_equip=hl,
            map_markers=st.session_state.map_markers,
            fleet=st.session_state.fleet,
            gps_offset=st.session_state.gps_offset,
        )
        event = st.plotly_chart(fig, use_container_width=True, on_select="rerun",
                                selection_mode=["points"], key="topo_map")
        if event and hasattr(event,"selection") and event.selection:
            pts = event.selection.get("points",[])
            if pts:
                pt = pts[0]
                st.info(f"📍 Map click: E {pt.get('x',0):.0f} m / N {pt.get('y',0):.0f} m  "
                        f"— use 'Drop Marker' above to save this location.")

        # Context hint per step
        hints = {
            1: "🔴 Safety & hazard layers active – all incidents relate to highlighted zones",
            2: "📋 Work zones shown – confirm JSA coverage for each active area",
            4: "📊 Pit 1 & Pit 2 production zones visible",
            5: "🪨 All geotech/hazard layers shown – toggle in sidebar",
            6: f"🚛 {st.session_state.selected_equip or '—'} highlighted in gold on the map",
        }
        hint = hints.get(st.session_state.meeting_step)
        if hint:
            st.caption(hint)

    with step_col:
        s = st.session_state.meeting_step
        if   s == 1: render_step_1()
        elif s == 2: render_step_2()
        elif s == 3: render_step_3()
        elif s == 4: render_step_4()
        elif s == 5: render_step_5()
        elif s == 6: render_step_6()
        elif s == 7: render_step_7()
        elif s == 8: render_step_8(mine_site)

        # Prev / Next
        nav1, nav2 = st.columns(2)
        with nav1:
            if s > 1:
                if st.button("◀ Previous", use_container_width=True):
                    st.session_state.meeting_step = s - 1; st.rerun()
        with nav2:
            if s < len(MEETING_STEPS):
                if st.button("Next ▶", use_container_width=True, type="primary"):
                    st.session_state.meeting_step = s + 1; st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SETUP & DATA
# ══════════════════════════════════════════════════════════════════════════════

def page_setup(role):
    st.title("⚙️ Setup & Data Management")
    st.caption("Configure mine site data, manage topo and drone imagery, and configure integrations. "
               "Changes here feed the morning meeting automatically.")
    if role == "viewer":
        st.warning("Read-only access – contact your Mine Planner to make changes.")

    tabs = st.tabs(["🗺️ Topo / Survey","🚁 Drone Imagery","🚛 Fleet Config","🔗 System Integration"])

    with tabs[0]:
        st.subheader("Survey Topographic Data")
        st.info("In production this connects directly to your survey software export (12d Model, MineScape, Vulcan, Deswik) "
                "and auto-updates after each survey flight. The topo is the master visual for all meetings – "
                "same coordinate system used for GPS equipment tracking and safety layer placement.")
        topo = st.file_uploader("Upload survey topo (JPG/PNG overlay or GeoTIFF)", type=["jpg","jpeg","png","tif","tiff"])
        if topo:
            st.session_state.topo_image = topo.read()
            st.success("Topo uploaded – in production replaces generated contour layer.")
            from PIL import Image
            st.image(Image.open(io.BytesIO(st.session_state.topo_image)), use_container_width=True)
        c1,c2 = st.columns(2)
        with c1:
            st.text_input("Datum",            value="GDA2020 / MGA Zone 54")
            st.text_input("Local Grid Origin E", value="22000 m")
        with c2:
            st.text_input("Projection",       value="MGA Zone 54")
            st.text_input("Local Grid Origin N", value="14500 m")

    with tabs[1]:
        st.subheader("Drone Imagery – Linked to Topo Zones")
        st.info("Drone imagery is linked to specific mine zones, not used as the base map. "
                "During the meeting, clicking a zone pulls up the latest drone photo for that area. "
                "Avoids alignment and coordinate system issues inherent in using drone imagery directly.")
        target_zone = st.selectbox("Link imagery to zone:", list(MINE_ZONES.keys()))
        drone_up = st.file_uploader(f"Upload drone image for '{target_zone}'",
                                    type=["jpg","jpeg","png"], key=f"drone_{target_zone}")
        if drone_up:
            st.session_state.drone_images[target_zone] = drone_up.read()
            st.success(f"Image linked to {target_zone}.")
        if st.session_state.drone_images:
            st.markdown("**Linked Images:**")
            for zone, img_bytes in st.session_state.drone_images.items():
                from PIL import Image
                with st.expander(f"📷 {zone}"):
                    st.image(Image.open(io.BytesIO(img_bytes)), use_container_width=True)

    with tabs[2]:
        st.subheader("Equipment Fleet Configuration")
        st.info("In production syncs with your MMS (Pronto, SAP PM, Infor EAM) for live maintenance status.")
        fleet_df = pd.DataFrame([{
            "ID":e["id"],"Type":e["type"],"Model":e["model"],"Operator":e["operator"],
            "Easting":e["easting"],"Northing":e["northing"],
            "Status":st.session_state.fleet_updates.get(e["id"],{}).get("status",e["shift_status"])
        } for e in st.session_state.fleet])
        st.dataframe(fleet_df, use_container_width=True, hide_index=True)
        with st.expander("➕ Add Equipment"):
            with st.form("add_eq"):
                c1,c2,c3 = st.columns(3)
                with c1:
                    nid  = st.text_input("Equipment ID")
                    ntyp = st.selectbox("Type",["Excavator","Haul Truck","Drill Rig","Dozer","Grader","Water Truck","Other"])
                with c2:
                    nmod = st.text_input("Model")
                    nop  = st.text_input("Operator")
                with c3:
                    ne   = st.number_input("Easting",  value=22750, min_value=E_MIN, max_value=E_MAX)
                    nn   = st.number_input("Northing", value=15350, min_value=N_MIN, max_value=N_MAX)
                if st.form_submit_button("Add to Fleet", type="primary"):
                    st.session_state.fleet.append({
                        "id":nid,"type":ntyp,"model":nmod,"icon":"🚛","symbol":"square",
                        "easting":ne,"northing":nn,"shift_status":"Available","operator":nop,
                        "assignment":"Unassigned","smu_hours":0,"fuel_level":100,"prev_notes":""})
                    st.success(f"{nid} added.")
                    st.rerun()

    with tabs[3]:
        st.subheader("External System Integration")
        st.info("Production version connects to mine systems via REST API or scheduled file-based data feeds.")
        integrations = [
            {"System":"MinView",              "Purpose":"Production actuals, KPIs, shift reports",              "Status":"🟡 Simulated"},
            {"System":"Prism / GPS Dispatch", "Purpose":"Live equipment GPS positions & haul cycle data",       "Status":"🟡 Simulated"},
            {"System":"HazView",              "Purpose":"Live geohazard monitoring & radar displacement alerts", "Status":"🟡 Simulated"},
            {"System":"Pronto / SAP PM",      "Purpose":"Equipment maintenance status & service schedules",     "Status":"🔴 Not connected"},
            {"System":"Weather API",          "Purpose":"Pit-level forecast & wind data",                       "Status":"🟡 Simulated"},
            {"System":"Blast Management",     "Purpose":"Blast patterns, timing & exclusion zones",             "Status":"🔴 Not connected"},
            {"System":"Email / MS Teams",     "Purpose":"Auto-distribute meeting reports to attendees",         "Status":"🔴 Not connected"},
        ]
        st.dataframe(pd.DataFrame(integrations), use_container_width=True, hide_index=True)
        st.caption("🟡 Simulated = demo data used  ·  🔴 Not connected = available for production build")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: KPI DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

def page_kpi_dashboard(mine_site):
    st.title("📊 KPI Dashboard")
    st.caption(f"{mine_site}  ·  Production metrics  ·  {date.today().strftime('%d %b %Y')}")
    df = st.session_state.kpi_data
    latest, prev = df.iloc[0], df.iloc[1]
    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: st.metric("BCM Yesterday",   f"{int(latest['BCM Moved']):,}",     f"{int(latest['BCM Moved']-latest['Target BCM']):+,} vs target")
    with c2: st.metric("Coal Tonnes",     f"{int(latest['Coal Tonnes']):,} t",  f"{int(latest['Coal Tonnes']-latest['Target Coal']):+,} vs target")
    with c3: st.metric("Stripping Ratio", f"{latest['Stripping Ratio']:.2f}",   f"{latest['Stripping Ratio']-prev['Stripping Ratio']:+.2f}")
    with c4: st.metric("Advance Rate",    f"{int(latest['Advance Rate m'])} m", f"{int(latest['Advance Rate m']-prev['Advance Rate m']):+} m")
    with c5: st.metric("Drill Metres",    f"{int(latest['Drill Metres'])} m",   f"{int(latest['Drill Metres']-prev['Drill Metres']):+} m")
    st.divider()
    t1,t2,t3,t4 = st.tabs(["BCM & Coal","Stripping Ratio","Drill Metres","Full Data"])
    with t1: st.line_chart(df.set_index("Date")[["BCM Moved","Target BCM","Coal Tonnes","Target Coal"]])
    with t2: st.line_chart(df.set_index("Date")[["Stripping Ratio"]])
    with t3: st.line_chart(df.set_index("Date")[["Drill Metres"]])
    with t4: st.dataframe(df, use_container_width=True)
    st.divider()
    st.subheader("Fleet Status")
    rows = [{"ID":e["id"],"Type":e["type"],"Model":e["model"],
             "Status":st.session_state.fleet_updates.get(e["id"],{}).get("status",e["shift_status"]),
             "Operator":e["operator"],"Fuel %":e["fuel_level"],"SMU hrs":f"{e['smu_hours']:,}",
             "Assignment":st.session_state.fleet_updates.get(e["id"],{}).get("assignment",e["assignment"])[:50]+"…"}
            for e in st.session_state.fleet]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: SHIFT HANDOVER
# ══════════════════════════════════════════════════════════════════════════════

def page_shift_handover(role):
    st.title("🔄 Digital Shift Handover")
    st.caption("End-of-shift notes per equipment item. Automatically surfaced in the next morning's meeting – "
               "no paper, no corridor conversations.")
    if role == "viewer":
        st.warning("Read-only access.")

    t1,t2 = st.tabs(["📝 Record Handover","📋 Handover History"])

    with t1:
        st.info("Complete notes for each machine. They appear in Step 6 (Equipment Walkthrough) "
                "of the next morning's meeting, linked directly to the equipment card on the topo map.")
        shift  = st.selectbox("Shift", ["Day Shift","Night Shift","Afternoon Shift"])
        author = st.text_input("Supervisor Name")
        with st.form("ho_form"):
            new_rows = []
            for eq in st.session_state.fleet:
                u    = st.session_state.fleet_updates.get(eq["id"],{})
                note = st.text_area(
                    f"{eq['icon']} {eq['id']} – {eq['model']} ({u.get('status',eq['shift_status'])})",
                    value=u.get("day_notes",""), height=65, key=f"ho_{eq['id']}")
                if note.strip():
                    new_rows.append({"Shift":shift,"Date":str(date.today()),
                        "Equipment":eq["id"],"Notes":note,"Author":author or "Supervisor"})
            gen = st.text_area("General Notes (site conditions, road status, weather, priorities)",
                               height=90, key="ho_gen")
            if gen.strip():
                new_rows.append({"Shift":shift,"Date":str(date.today()),
                    "Equipment":"GENERAL","Notes":gen,"Author":author or "Supervisor"})
            if st.form_submit_button("✅ Submit Handover", type="primary"):
                if new_rows:
                    st.session_state.handover_notes = pd.concat(
                        [pd.DataFrame(new_rows), st.session_state.handover_notes], ignore_index=True)
                    st.success(f"Handover submitted for "
                               f"{sum(1 for r in new_rows if r['Equipment']!='GENERAL')} equipment items. "
                               "Notes will appear in tomorrow's morning meeting.")
                else:
                    st.warning("No notes entered.")

    with t2:
        st.dataframe(st.session_state.handover_notes, use_container_width=True, hide_index=True)
        st.download_button("⬇️ Download Handover Log",
            data=st.session_state.handover_notes.to_csv(index=False).encode(),
            file_name=f"MOS_Handover_{date.today()}.csv", mime="text/csv")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: REPORTS
# ══════════════════════════════════════════════════════════════════════════════

def page_reports(mine_site):
    st.title("📄 Reports & Export")
    st.caption("Generate compliance-ready reports from meeting and operational data.")
    t1,t2,t3,t4 = st.tabs(["📅 Meeting Report","📊 Production","⚠️ Incident Register","🔄 Handover Log"])

    with t1:
        st.subheader("Daily Planning Meeting Report")
        if st.session_state.last_report:
            st.success("Latest report available (generated in morning meeting Step 8).")
            st.markdown(f'<div class="report-box">{st.session_state.last_report.replace(chr(10),"<br>")}</div>',
                        unsafe_allow_html=True)
            st.download_button("⬇️ Download Report (.txt)",
                data=st.session_state.last_report.encode(),
                file_name=f"MOS_MeetingReport_{date.today()}.txt", mime="text/plain", type="primary")
        else:
            st.info("No report generated yet. Complete the morning meeting (Step 8) to generate.")
        st.markdown("**Auto-distribution (production):**")
        att = st.text_area("Email recipients", value=st.session_state.attendees, height=55, key="rep_att")
        if st.button("📧 Simulate Send Report", type="primary"):
            st.success("In production: report emailed to all attendees and archived with full audit trail.")

    with t2:
        st.dataframe(st.session_state.kpi_data, use_container_width=True)
        st.download_button("⬇️ Download Production Data",
            data=st.session_state.kpi_data.to_csv(index=False).encode(),
            file_name=f"MOS_Production_{date.today()}.csv", mime="text/csv")

    with t3:
        st.dataframe(st.session_state.incidents, use_container_width=True)
        st.download_button("⬇️ Download Incident Register",
            data=st.session_state.incidents.to_csv(index=False).encode(),
            file_name=f"MOS_Incidents_{date.today()}.csv", mime="text/csv")

    with t4:
        st.dataframe(st.session_state.handover_notes, use_container_width=True)
        st.download_button("⬇️ Download Handover Log",
            data=st.session_state.handover_notes.to_csv(index=False).encode(),
            file_name=f"MOS_Handover_{date.today()}.csv", mime="text/csv")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ROUTER
# ══════════════════════════════════════════════════════════════════════════════

def main():
    mine_site, role = render_sidebar()
    page = st.session_state.page
    if   "Morning Meeting" in page: page_morning_meeting(mine_site, role)
    elif "Setup"           in page: page_setup(role)
    elif "KPI"             in page: page_kpi_dashboard(mine_site)
    elif "Handover"        in page: page_shift_handover(role)
    elif "Reports"         in page: page_reports(mine_site)


main()
