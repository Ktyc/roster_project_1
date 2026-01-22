from datetime import date
import calendar 
from typing import List
from src.models import Shift, ShiftType, Staff, Role
from src.io_handler import load_staff_from_excel
from ortools.sat.python import cp_model
import streamlit as st
def assign_staff_to_shift(shifts: List[Shift], staff_list:List[Staff]):
    # Creation Of Model
    model = cp_model.CpModel()
    assignments = {}
    for s_idx, shift in enumerate(shifts):
        for staff in staff_list:
            safe_name = "".join(filter(str.isalnum, staff.name))
            var_name = f"s{s_idx}_st{safe_name}"
            assignments[(staff.name, s_idx)] = model.NewBoolVar(var_name) # Creates EVERY possible combinations, each shift can be assigned to ANY of the 40 staff in staff_list
    
    # Hard Constraint: Every shift must have 1 staff assigned
    for s_idx, shift in enumerate(shifts): # For each shift, only one out of the 40 staffs can be assigned to it 
        model.Add(sum(assignments[(staff.name, s_idx)] for staff in staff_list) == 1) 
    
    # Hard Constraint: NO_PM
    for s_idx, shift in enumerate(shifts):
        if shift.type in [ShiftType.WEEKDAY_PM, ShiftType.PUBLIC_HOL_PM]:
            for staff in staff_list:
                if staff.role == Role.NO_PM:
                    model.Add(assignments[(staff.name, s_idx)] == 0)


    # # Hard Constraint: WEEKEND_ONLY
    for s_idx, shift in enumerate(shifts):
        if shift.date.weekday() < 5: 
            for staff in staff_list:
                if staff.role == Role.WEEKEND_ONLY:
                    model.Add(assignments[(staff.name, s_idx)] == 0)


    # Hard Constraint: Blackout Dates
    for s_idx, shift in enumerate(shifts):
        for staff in staff_list:
            if shift.date in staff.blackout_dates:
                # # TEST PRINT: See which dates are blocked 
                # print(f"BLOCKING: {staff.name} is blacked out on {shift.date}")
                model.Add(assignments[(staff.name, s_idx)] == 0)

    # # Hard Constraint: The Rest Rule
    for s_idx, current_shift in enumerate(shifts):
        # Apply rest rule after PM shifts and 24h weekend shifts
        if current_shift.type in [ShiftType.WEEKDAY_PM, ShiftType.WEEKEND_FULL_DAY, ShiftType.PUBLIC_HOL_PM]:

            # Look for any shift that happens "tomorrow"
            for next_s_idx, next_shift in enumerate(shifts):
                # Check if next_shift is exactly 1 day after current_shift
                days_diff = (next_shift.date - current_shift.date).days

                if days_diff == 1:
                    # For every staff member...
                    for staff in staff_list:
                        # Law: Alice_Today_Shift + Alice_Tomorrow_Any <= 1
                        today_shift_var = assignments[(staff.name, s_idx)]
                        tomorrow_var = assignments[(staff.name, next_s_idx)]
                        # # TEST PRINT: See which dates are blocked
                        # print(f"BLOCKING: {staff.name} cannot work shift on {shift.date}")
                        model.Add(today_shift_var + tomorrow_var <= 1)

    # Hard Constraint: Bidding + PH Immunity
    for s_idx, shift in enumerate(shifts):
        if shift.type in [ShiftType.PUBLIC_HOL_AM, ShiftType.PUBLIC_HOL_PM]:
            
            # 1. IDENTIFY BIDDERS (Bypasses Immunity)
            s_bidders = [st for st in staff_list if shift.date in st.bidding_dates]
            
            # Filter bidders by Role (NO_PM / WEEKEND_ONLY)
            eligible_bidders = [
                b for b in s_bidders 
                if not (shift.type == ShiftType.PUBLIC_HOL_PM and b.role == Role.NO_PM)
                and not (shift.date.weekday() < 5 and b.role == Role.WEEKEND_ONLY)
            ]

            if eligible_bidders:
                # If there are bidders, one of them MUST take the shift
                model.Add(sum(assignments[(bidder.name, s_idx)] for bidder in eligible_bidders) == 1)
                # Ensure non-bidders are NOT assigned this shift
                bidder_names = {b.name for b in eligible_bidders}
                for staff in staff_list:
                    if staff.name not in bidder_names:
                        model.Add(assignments[(staff.name, s_idx)] == 0)
            
            else:
                # 2. NO BIDDERS: Check Historical Immunity & Role Constraints
                for staff in staff_list:
                    # If they are historically immune (worked PH in last 300 days)
                    if staff.is_immune_on(shift.date):
                        model.Add(assignments[(staff.name, s_idx)] == 0)
                    
                    # Standard Role Constraints
                    if shift.type == ShiftType.PUBLIC_HOL_PM and staff.role == Role.NO_PM:
                        model.Add(assignments[(staff.name, s_idx)] == 0)
                    if shift.date.weekday() < 5 and staff.role == Role.WEEKEND_ONLY:
                        model.Add(assignments[(staff.name, s_idx)] == 0)

    # Internal Immunity 
    # Prevent anyone from being assigned PH shifts within 300 days of each other
    ph_indices = [i for i, s in enumerate(shifts) if s.type in [ShiftType.PUBLIC_HOL_AM, ShiftType.PUBLIC_HOL_PM]] # Creates ID numbers for each PH shift

    for staff in staff_list:
        for i in range(len(ph_indices)):
            for j in range(i + 1, len(ph_indices)):
                idx1 = ph_indices[i]
                idx2 = ph_indices[j]
                
                date1 = shifts[idx1].date
                date2 = shifts[idx2].date
                
                if abs((date1 - date2).days) < 300:
                    # Rule: Assignment to PH1 + Assignment to PH2 <= 1 (Cannot do both)
                    model.Add(assignments[(staff.name, idx1)] + assignments[(staff.name, idx2)] <= 1)

    # Soft Constraint: Fairness
    # Create a dictionary to hold the TOTAL points for each staff
    total_staff_points = {}

    for staff in staff_list:
        # Start with their existing points (scaled to int)
        initial_p = int(staff.ytd_points * 10)
        
        # Calculate points from NEW shifts assigned in this run
        new_points = sum(
            assignments[(staff.name, s_idx)] * int(shift.type.points * 10)
            for s_idx, shift in enumerate(shifts)
        )
        
        # Define the dynamic total
        total_points_var = model.NewIntVar(0, 1000000, f"total_{staff.name}")
        model.Add(total_points_var == initial_p + new_points)
        total_staff_points[staff.name] = total_points_var

    # Now link highest/lowest to these dynamic totals
    highest = model.NewIntVar(0, 1000000, "highest_p")
    lowest = model.NewIntVar(0, 1000000, "lowest_p")

    for p_var in total_staff_points.values():
        model.Add(highest >= p_var)
        model.Add(lowest <= p_var)

    model.Minimize(highest - lowest)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30.0
    status = solver.Solve(model)

    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        results = [] 
        for s_idx, s_obj in enumerate(shifts):
            for staff in staff_list:
                if solver.Value(assignments[(staff.name, s_idx)]) == 1: # If particular staff is assigned to this particular shift
                    # Update Staff Score
                    staff.ytd_points += s_obj.type.points
                    # Update Shift's Occupant
                    s_obj.assigned_staff = staff
                    # PH Immunity
                    if s_obj.type in [ShiftType.PUBLIC_HOL_AM, ShiftType.PUBLIC_HOL_PM]:
                        staff.last_PH = s_obj.date 
                        # print(f"TESING IMMUNITY: {staff.name} immunity status - {staff.PH_Immunity(s_obj.date)}")
                        # print(f"{staff.name} immunity starts on {s_obj.date} and ends on {staff.immunity_expiry_date}")
                    results.append({"Date": s_obj.date, "Shift": s_obj.type.name, "Staff": staff.name, "PH Immunity Period": f"{staff.last_PH} - {staff.immunity_expiry_date}"})
        return results 
    return None

            
