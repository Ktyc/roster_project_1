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
        if shift.type in [ShiftType.WEEKDAY_PM, ShiftType.WEEKEND_PM, ShiftType.PUBLIC_HOL_PM]:
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
        if current_shift.type in [ShiftType.WEEKDAY_PM, ShiftType.WEEKEND_PM, ShiftType.PUBLIC_HOL_PM]:

            # Now, look for any shift that happens "tomorrow"
            for next_s_idx, next_shift in enumerate(shifts):
                # Check if next_shift is exactly 1 day after current_shift
                days_diff = (next_shift.date - current_shift.date).days

                if days_diff == 1:
                    # for every staff member...
                    for staff in staff_list:
                        # Law: Alice_Today_PM + Alice_Tomorrow_Any <= 1
                        today_pm_var = assignments[(staff.name, s_idx)]
                        tomorrow_var = assignments[(staff.name, next_s_idx)]
                        # # TEST PRINT: See which dates are blocked 
                        # print(f"BLOCKING: {staff.name} cannot work AM shift on {shift.date}")
                        model.Add(today_pm_var + tomorrow_var <= 1)

    # # Hard Constraint: Public Holiday Bidding
    for s_idx, shift in enumerate(shifts):
        s_bidders = []
        for staff in staff_list:
            if shift.date in staff.bidding_dates: # Bidding dates only contains Public Holidays
                #if not staff.PH_Immunity:
                s_bidders.append(staff)
        if len(s_bidders) != 0: # Have Bidders, IF NO BIDDERS CODE SHOULD SITLL FOLLOW HARD CONSTRAINT 1
            model.Add(sum(assignments[(bidder.name, s_idx)] for bidder in s_bidders) == 1) # Only one

    # # Hard Constraint: PH Immunity (CANT TEST YET)
    for s_idx, shift in enumerate(shifts):
        if shift.type in [ShiftType.PUBLIC_HOL_AM, ShiftType.PUBLIC_HOL_PM]:
            for staff in staff_list:
                if staff.PH_Immunity(shift.date): 
                    model.Add(assignments[(staff.name, s_idx)] == 0)


    # Soft Constraint: Fairness
    highest = model.NewIntVar(0, 100000, "Highest Points")
    lowest = model.NewIntVar(0, 100000, "Lowest Points")
    for staff in staff_list:
        model.Add(highest >= int(staff.ytd_points * 10))
        model.Add(lowest <= int(staff.ytd_points * 10))

    highest_lowest_diff = highest - lowest

    # Finalize and Solve
    model.Minimize(highest_lowest_diff)

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
    solver.parameters.max_time_in_seconds = 600.0 
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
                        # print(f"{staff.name} immunity ends on {staff.immunity_expiry_date}")
                    results.append({"Date": s_obj.date, "Shift": s_obj.type.name, "Staff": staff.name})
        return results 
    return None

            
