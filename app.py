"""Main Entry Point for Duty Roster Application"""
import plotly.express as px
import streamlit as st
import pandas as pd
import io
from src.io_handler import load_staff_from_excel 
from src.engine import assign_staff_to_shift
from src.models import Shift, ShiftType
from datetime import date, timedelta

# 1. Setup the page
st.set_page_config(page_title="AI Staff Scheduler", layout="wide")

# 2. Header
st.title("AI Duty Roster Planner")

# 3. Sidebar for settings
with st.sidebar:
    st.header("1. Define Date Range")
    # This defaults to "Today", so it works in 2026, 2027, etc.
    start_date = st.date_input("Start Date", value=date.today())
    
    # Suggest an end date 6 months from the chosen start date
    suggested_end = start_date + timedelta(days=182) 
    end_date = st.date_input("End Date", value=suggested_end)
    


    # st.divider()
    # st.header("2. Public Holidays")
    # ph_dates = st.multiselect(
    #     "Select Public Holidays", 
    #     options=all_dates, 
    #     format_func=lambda x: x.strftime("%d %b (%a)")
    # )

    st.divider()
    st.header("3. Data Upload")
    uploaded_file = st.file_uploader("Upload Staff Excel", type=["xlsx"])
    
    if uploaded_file is not None:
        if "staff_list" not in st.session_state:
            # We load the data once and keep it in session state
            st.session_state.staff_list = load_staff_from_excel(uploaded_file)
            st.session_state.raw_staff_df = pd.read_excel(uploaded_file)
            # Snapshot of points before the engine runs
            st.session_state.initial_points = {s.name: s.ytd_points for s in st.session_state.staff_list}

    st.divider()
    st.header("4. Refresh")
    if uploaded_file is not None:
        # Use the button or a change in the file to trigger a reload
        if st.sidebar.button("Reload Staff Data"):
            # This clears the old data and forces a fresh load
            st.session_state.staff_list = load_staff_from_excel(uploaded_file)
            st.session_state.raw_staff_df = pd.read_excel(uploaded_file)
            st.session_state.initial_points = {s.name: s.ytd_points for s in st.session_state.staff_list}
            st.sidebar.success("Data Refreshed!")

        # Fallback for the very first load
        if "staff_list" not in st.session_state:
            st.session_state.staff_list = load_staff_from_excel(uploaded_file)
            st.session_state.raw_staff_df = pd.read_excel(uploaded_file)
            st.session_state.initial_points = {s.name: s.ytd_points for s in st.session_state.staff_list}

if uploaded_file is not None and start_date <= end_date:
    # 4. Main logic
    ph_dates = [
        date(2026, 2, 17),
        date(2026, 2, 18),
        date(2026, 4, 3),
        date(2026, 5, 1),
        date(2026, 5, 21),
        date(2026, 6, 3),
        date(2026, 8, 9),
        date(2026, 12, 25)
    ] # HARD CODED FOR TESTING PURPOSES

    # GENERATING ALL THE SHIFTS 
    delta = end_date - start_date
    all_dates = [start_date + timedelta(days=i) for i in range(delta.days + 1)]
    curr_shifts = []
    for d in all_dates: # DISTINGUISHES PHs from WEEKENDS AND WEEKDAYS
        if d in ph_dates: # PH 
            curr_shifts.append(Shift(date=d, type=ShiftType.PUBLIC_HOL_AM))
            curr_shifts.append(Shift(date=d, type=ShiftType.PUBLIC_HOL_PM))
        elif d.weekday() >= 5: # Weekend
            curr_shifts.append(Shift(date=d, type=ShiftType.WEEKEND_AM))
            curr_shifts.append(Shift(date=d, type=ShiftType.WEEKEND_PM))
        else: # Weekday
            curr_shifts.append(Shift(date=d, type=ShiftType.WEEKDAY_PM))
    

# --- UI: Staff Preview --- 
    with st.expander("View Staff Directory & Constraints", expanded=False):
        st.dataframe(st.session_state.raw_staff_df, width='stretch', hide_index=True)

    # Roster Generation
    if st.button("Generate Optimized Roster", type="primary", width='stretch'):
        with st.spinner("AI is generating the best shift distribution..."):
            assignments = assign_staff_to_shift(curr_shifts, st.session_state.staff_list)
            
            if assignments:
                st.session_state.last_assignments = assignments
                st.success("Roster generated successfully!")
            else:
                st.error("No valid solution found! Please check the constraints given.")

    # 5. Display Results
    if "last_assignments" in st.session_state and st.session_state.last_assignments:
        # Roster Table
        st.subheader("Finalised Roster")
        df_roster = pd.DataFrame(st.session_state.last_assignments)


        # Pivot the data so Dates are rows and Shift Types are columns
        pivot_df = df_roster.pivot(index="Date", columns="Shift", values="Staff")
        
        # FIXED: Corrected column names to match ShiftType Enum names exactly
        cols_priority = ["WEEKDAY_PM", "WEEKEND_AM", "WEEKEND_PM", "PUBLIC_HOL_AM", "PUBLIC_HOL_PM"]
        existing_cols = [c for c in cols_priority if c in pivot_df.columns]
        pivot_df = pivot_df.reindex(columns=existing_cols).fillna("-")
        
        # Format dates for display
        display_roster = pivot_df.copy()
        display_roster.index = [d.strftime("%a, %d %b") for d in display_roster.index]
        
        st.dataframe(display_roster, width='stretch')

        # --- POINTS RECONCILIATION ---
        st.divider()
        st.subheader("📈 Points Reconciliation")
        
        recon_data = []
        for s in st.session_state.staff_list:
            start_pts = st.session_state.initial_points.get(s.name, 0.0)
            recon_data.append({
                "Staff Name": s.name,
                "Role": s.role.name,
                "Starting YTD": start_pts,
                "Points Earned": round(s.ytd_points - start_pts, 1),
                "Final Total": round(s.ytd_points, 1)
            })
        
        df_recon = pd.DataFrame(recon_data)
        # Format the numeric columns to 1 decimal place for display
        formatted_df = df_recon.style.format({
            "Starting YTD": "{:.1f}",
            "Points Earned": "{:.1f}",
            "Final Total": "{:.1f}"
        })

        st.table(formatted_df)



        # --- VISUALIZATION SECTION ---
        st.subheader("Workload Distribution Analysis")
        
        # Create a bar chart showing the final totals
        # This helps you visually identify if someone is getting too many/few points
        fig = px.bar(
            df_recon, 
            x="Staff Name", 
            y="Final Total", 
            color="Role",
            title="Total Points by Staff (Fairness Check)",
            text="Final Total",
            color_discrete_map={
                "STANDARD": "#1f77b4", 
                "NO_PM": "#ff7f0e", 
                "WEEKEND_ONLY": "#2ca02c"
            }
        )
        
        # Improve the layout
        fig.update_traces(textposition='outside')
        fig.update_layout(xaxis_tickangle=-45, height=500)
        
        st.plotly_chart(fig, width='stretch')
        
        # Metric
        # Assuming df_recon is your Points Reconciliation DataFrame
        std_dev = df_recon["Final Total"].std()
        mean_pts = df_recon["Final Total"].mean()

        # Display as metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Average Points", f"{round(mean_pts, 2)}")
        with col2:
            st.metric("Standard Deviation", f"{round(std_dev, 2)}")
        with col3:
            # A gap of 0 is perfect fairness
            point_gap = df_recon["Final Total"].max() - df_recon["Final Total"].min()
            st.metric("Fairness Gap (Max-Min)", f"{round(point_gap, 1)} pts")

        # Interpretation Help
        if std_dev < 2.0:
            st.success("✅ Excellent Fairness: Points are tightly clustered.")
        elif std_dev < 5.0:
            st.info("ℹ️ Good Fairness: Minor variations based on roles.")
        else:
            st.warning("⚠️ High Variation: Some staff are working significantly more than others.")
        
        # Box and Whisker's Plot
        fig_box = px.box(
        df_recon, 
        y="Final Total", 
        points="all", 
        title="Statistical Spread of Points"
    )
        st.plotly_chart(fig_box, width='stretch')


        # --- DOWNLOAD ---
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            pivot_df.to_excel(writer, sheet_name='Roster')
            pd.DataFrame(recon_data).to_excel(writer, sheet_name='Points', index=False)
        
        st.download_button(
            "Download Roster (Excel)",
            data=output.getvalue(),
            file_name=f"Roster_{start_date}.xlsx",
            mime="application/vnd.ms-excel",
            width='stretch'
        )

else:
    st.info("👈 Upload the Staff Excel file and set the dates in the sidebar to begin.")