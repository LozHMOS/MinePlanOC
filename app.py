import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
from datetime import date, timedelta
import io

# Page configuration
st.set_page_config(
    page_title="MOS MinePlan OC – Full Demonstration",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("MOS MinePlan OC")
st.markdown("**Open Cut Coal Mine Planning Tool** – Complete demonstration with all value add features for management review")

# Sidebar – simple authentication simulation
st.sidebar.header("Mine Site Access")
mine_name = st.sidebar.selectbox(
    "Select mine site",
    ["North Pit Colliery", "Central Queensland Colliery", "Bowen Basin Site A"]
)
password = st.sidebar.text_input("Enter demonstration password", type="password")
if password != "mos2025":
    st.sidebar.warning("Please use password **mos2025** to unlock full features.")
    st.stop()

st.sidebar.success(f"Logged in as Planner – {mine_name}")

# Session state initialisation for persistence (simulates offline caching)
if "images" not in st.session_state:
    st.session_state.images = {}  # date_str: PIL Image
if "assets" not in st.session_state:
    st.session_state.assets = pd.DataFrame(columns=["Date", "Asset Name", "Type", "X", "Y", "Label", "Notes"])
if "safety_markers" not in st.session_state:
    st.session_state.safety_markers = pd.DataFrame(columns=["Date", "Hazard Type", "X", "Y", "Label", "Notes"])
if "plan" not in st.session_state:
    st.session_state.plan = pd.DataFrame({
        "Task": ["Clear overburden", "Drill blast holes", "Load coal", "Haul to ROM", "Maintenance"],
        "Equipment": ["EX-01", "DR-02", "", "", "MT-03"],
        "Assigned To": ["Shift A", "Shift B", "", "", ""],
        "Status": ["Planned", "Planned", "Planned", "Planned", "Planned"]
    })
if "handover_notes" not in st.session_state:
    st.session_state.handover_notes = pd.DataFrame(columns=["Date", "Shift", "Notes", "Updated By"])
if "kpi_data" not in st.session_state:
    st.session_state.kpi_data = pd.DataFrame({
        "Date": [str(date.today() - timedelta(days=i)) for i in range(7)],
        "Tonnes Moved": [12450, 11800, 13200, 10900, 14100, 12750, 13500],
        "Stripping Ratio": [8.2, 7.9, 8.5, 8.1, 7.8, 8.3, 8.0],
        "Advance Rate (m)": [42, 38, 45, 35, 48, 41, 44]
    })

# Tabs – core workflow plus full management suite
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📤 Upload & View Imagery",
    "🔖 Mark Assets & Points of Interest",
    "📊 Compare Daily Imagery",
    "📅 24 Hour Planning",
    "📊 Management & Value-Add Features"
])

with tab1:
    st.subheader("Upload Daily Drone Imagery")
    st.info("Upload one or more geotagged or ortho-rectified drone images.")
    
    # Demonstration imagery loader
    if st.button("Load Demonstration Open Cut Mine Imagery"):
        try:
            demo_img = Image.open("demo_open_cut_mine.jpg")
            yesterday = str(date.today() - timedelta(days=1))
            today_str = str(date.today())
            st.session_state.images[yesterday] = demo_img.copy()
            st.session_state.images[today_str] = demo_img.copy()
            st.success("Demonstration imagery loaded successfully as Day 0 (Yesterday) and Day 1 (Today). You can now explore the comparison and management tabs.")
        except FileNotFoundError:
            st.error("Please ensure the file 'demo_open_cut_mine.jpg' is in the same folder as this app.")
        except Exception as e:
            st.error(f"Error loading demonstration image: {e}")
    
    uploaded_files = st.file_uploader(
        "Choose drone imagery files (JPG/PNG)",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        help="Select files captured today or previous days"
    )
    if uploaded_files:
        for file in uploaded_files:
            img = Image.open(file)
            date_str = st.date_input(f"Date for {file.name}", value=date.today() - timedelta(days=len(st.session_state.images)))
            st.session_state.images[str(date_str)] = img
            st.success(f"Uploaded {file.name} for {date_str}")

    if st.session_state.images:
        st.subheader("Available Imagery")
        selected_date = st.selectbox("View imagery for", options=list(st.session_state.images.keys()))
        st.image(st.session_state.images[selected_date], caption=f"Drone imagery – {selected_date}", use_container_width=True)

with tab2:
    st.subheader("Mark Assets and Points of Interest")
    st.info("Select a day and place markers directly on the imagery using the form on the right.")
    if not st.session_state.images:
        st.warning("Upload imagery in the first tab first (or use the demonstration button above).")
    else:
        mark_date = st.selectbox("Select day to annotate", options=list(st.session_state.images.keys()), key="mark_date")
        current_img = st.session_state.images[mark_date]
        col_left, col_right = st.columns([3, 1])
        with col_left:
            st.image(current_img, caption=f"Drone imagery – {mark_date}", use_container_width=True)
        with col_right:
            st.subheader("Add new asset / POI")
            asset_name = st.text_input("Asset name (e.g. EX-01)")
            asset_type = st.selectbox("Type", ["Excavator", "Haul Truck", "Drill Rig", "Blast Pattern", "Water Truck", "POI – Highwall", "POI – Stockpile", "Other"])
            label = st.text_input("Short label")
            notes = st.text_area("Notes", height=100)
            x = st.number_input("X coordinate (0–image width)", min_value=0, max_value=current_img.width, value=current_img.width // 2)
            y = st.number_input("Y coordinate (0–image height)", min_value=0, max_value=current_img.height, value=current_img.height // 2)
            if st.button("Add marker to imagery"):
                new_row = pd.DataFrame([{"Date": mark_date, "Asset Name": asset_name or f"Asset_{len(st.session_state.assets)+1}", "Type": asset_type, "X": x, "Y": y, "Label": label or asset_type, "Notes": notes}])
                st.session_state.assets = pd.concat([st.session_state.assets, new_row], ignore_index=True)
                st.success("Marker added")
        day_assets = st.session_state.assets[st.session_state.assets["Date"] == mark_date]
        if not day_assets.empty:
            st.subheader("Current markers on this day")
            st.dataframe(day_assets, use_container_width=True)
            annotated = current_img.copy()
            draw = ImageDraw.Draw(annotated)
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()
            for _, row in day_assets.iterrows():
                draw.ellipse((row["X"]-15, row["Y"]-15, row["X"]+15, row["Y"]+15), outline="red", width=4)
                draw.text((row["X"]+20, row["Y"]-10), row["Label"], fill="red", font=font)
            st.image(annotated, caption=f"Annotated imagery – {mark_date}", use_container_width=True)

with tab3:
    st.subheader("Compare Daily Imagery")
    st.info("Side-by-side view with progress highlights – core feature for reviewing change over 24 hours.")
    if len(st.session_state.images) < 2:
        st.warning("Load the demonstration imagery or upload at least two days to enable comparison.")
    else:
        dates = list(st.session_state.images.keys())
        col1, col2 = st.columns(2)
        with col1:
            date_a = st.selectbox("Left image (previous day)", options=dates, index=0)
        with col2:
            date_b = st.selectbox("Right image (today)", options=dates, index=len(dates)-1)
        left_img = st.session_state.images[date_a]
        right_img = st.session_state.images[date_b]
        comp_col1, comp_col2 = st.columns(2)
        with comp_col1:
            st.image(left_img, caption=f"Previous – {date_a}", use_container_width=True)
        with comp_col2:
            st.image(right_img, caption=f"Current – {date_b}", use_container_width=True)
        st.caption("In the full application a difference overlay or change detection layer would appear automatically using computer vision techniques.")

with tab4:
    st.subheader("24 Hour Planning Interface")
    st.info("Assign tasks and assets for the next shift based on current imagery and marked resources.")
    st.data_editor(
        st.session_state.plan,
        num_rows="dynamic",
        use_container_width=True,
        column_config={"Status": st.column_config.SelectboxColumn(options=["Planned", "In Progress", "Completed", "Delayed"])}
    )
    st.subheader("Available equipment (derived from marked assets)")
    available = st.session_state.assets["Asset Name"].unique().tolist() if not st.session_state.assets.empty else ["EX-01", "HT-02", "DR-03"]
    st.multiselect("Select equipment to allocate", available, default=available[:2])
    if st.button("Save 24 hour plan"):
        st.success("Plan saved to database – ready for export or integration with existing mine systems.")

with tab5:
    st.subheader("Management & Value-Add Features")
    st.info("This tab contains every enhancement requested for management review. All data is linked to the imagery and planning already entered.")

    mgmt_tab1, mgmt_tab2, mgmt_tab3, mgmt_tab4, mgmt_tab5, mgmt_tab6 = st.tabs([
        "KPI Dashboard", "Progress Tracking Overlay", "Digital Shift Handover", "Safety & Hazard Layer",
        "Rolling Forecast & Historical Trends", "One-Click Reporting"
    ])

    with mgmt_tab1:
        st.subheader("Centralised KPI Dashboard")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Today’s Tonnes Moved", "13,500 t", "↑ 1,200 t")
        with col2:
            st.metric("Stripping Ratio", "8.1", "↓ 0.2")
        with col3:
            st.metric("Advance Rate", "44 m", "↑ 3 m")
        st.subheader("7-Day Trend")
        st.line_chart(st.session_state.kpi_data, x="Date", y=["Tonnes Moved", "Stripping Ratio", "Advance Rate (m)"], use_container_width=True)

    with mgmt_tab2:
        st.subheader("Automated Progress Tracking – Plan vs Actual")
        st.info("The demonstration imagery (Day 0 and Day 1) is already loaded above. The overlay below shows the workflow.")
        if len(st.session_state.images) >= 2:
            dates = list(st.session_state.images.keys())
            left = st.session_state.images[dates[0]]
            right = st.session_state.images[dates[-1]]
            colA, colB = st.columns(2)
            with colA:
                st.image(left, caption="Yesterday – Day 0", use_container_width=True)
            with colB:
                st.image(right, caption="Today – Day 1", use_container_width=True)
            st.success("Visual difference workflow ready (in a real deployment different daily flights would be used).")
        else:
            st.warning("Load the demonstration imagery first.")

    with mgmt_tab3:
        st.subheader("Digital Shift Handover")
        st.data_editor(
            st.session_state.handover_notes,
            num_rows="dynamic",
            use_container_width=True
        )
        shift = st.selectbox("Shift", ["Day Shift", "Night Shift"])
        notes = st.text_area("Handover notes / issues encountered")
        if st.button("Add handover note"):
            new_note = pd.DataFrame([{"Date": str(date.today()), "Shift": shift, "Notes": notes, "Updated By": "Planner"}])
            st.session_state.handover_notes = pd.concat([st.session_state.handover_notes, new_note], ignore_index=True)
            st.success("Note recorded – full audit trail available in production.")

    with mgmt_tab4:
        st.subheader("Safety & Hazard Management Layer")
        st.info("Toggleable layer for regulatory and safety compliance – separate from normal assets.")
        mark_date = st.selectbox("Select day for safety marking", options=list(st.session_state.images.keys()) if st.session_state.images else ["2025-04-03"], key="safety_date")
        if st.session_state.images:
            current_img = st.session_state.images[mark_date]
            st.image(current_img, caption=f"Safety layer – {mark_date}", use_container_width=True)
            hazard_type = st.selectbox("Hazard type", ["Highwall instability", "Water ponding", "Exclusion zone", "Blast area", "Rehabilitation zone", "Other"])
            sx = st.number_input("X coordinate (safety)", min_value=0, max_value=2000, value=1000)
            sy = st.number_input("Y coordinate (safety)", min_value=0, max_value=2000, value=1000)
            if st.button("Add safety marker"):
                new_safety = pd.DataFrame([{"Date": mark_date, "Hazard Type": hazard_type, "X": sx, "Y": sy, "Label": hazard_type, "Notes": "Immediate action required"}])
                st.session_state.safety_markers = pd.concat([st.session_state.safety_markers, new_safety], ignore_index=True)
                st.success("Safety marker added")
        if not st.session_state.safety_markers.empty:
            st.dataframe(st.session_state.safety_markers, use_container_width=True)

    with mgmt_tab5:
        st.subheader("Rolling Short-Term Forecast & Historical Archive")
        st.info("3-day lookahead plus historical trend viewer.")
        st.write("**3-Day Forecast**")
        forecast_df = pd.DataFrame({
            "Day": ["Tomorrow", "Day +2", "Day +3"],
            "Projected Tonnes": [13800, 14200, 12900],
            "Key Tasks": ["Strip advance Pit 1", "Blast & load Pit 2", "Maintenance window"]
        })
        st.dataframe(forecast_df, use_container_width=True)
        st.write("**Historical Archive** – all previous days available for comparison")
        st.line_chart(st.session_state.kpi_data, use_container_width=True)

    with mgmt_tab6:
        st.subheader("One-Click Management & Compliance Reporting")
        st.info("Generate a professional export package in seconds.")
        if st.button("Generate full daily report (PDF simulation)"):
            st.success("Report package created – includes annotated imagery, KPIs, handover notes, safety markers and plan. In production this would download as a single PDF ready for senior leadership or regulators.")
            st.download_button(
                label="Download sample report CSV (for demonstration)",
                data=pd.concat([st.session_state.assets, st.session_state.safety_markers]).to_csv(index=False).encode(),
                file_name="MOS_MinePlan_OC_Daily_Report.csv",
                mime="text/csv"
            )
