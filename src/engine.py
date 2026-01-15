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
    
    # Hard Constraint: Every shift msut have 1 staff assigned
    for s_idx, shift in enumerate(shifts): # For each shift, only one out of the 40 staffs can be assigned to it 
        model.Add(sum(assignments[(staff.name, s_idx)] for staff in staff_list) == 1) 
    
    # Hard Constraint: NO_PM
    for s_idx, shift in enumerate(shifts):
        for staff in staff_list:
            if staff.role.NO_PM and shift.type in [ShiftType.WEEKDAY_PM, ShiftType.WEEKEND_PM, ShiftType.PUBLIC_HOL_PM]: # PUBLIC HOLIDAY NO COUNT
                model.Add(assignments[(staff.name, s_idx)] == 0)

    # Hard Constraint: WEEKEND_ONLY
    for s_idx, shift in enumerate(shifts):
        for staff in staff_list:
            if staff.role.WEEKEND_ONLY and shift.date.weekday() < 5:
                model.Add(assignments[(staff.name, s_idx)] == 0)

    # Hard Constraint: Blackout Dates
    for s_idx, shift in enumerate(shifts):
        for staff in staff_list:
            if shift.date in staff.blackout_dates:
                model.Add(assignments[(staff.name, s_idx)] == 0)

    # Hard Constraint: The Rest Rule
    for s_idx, shift in enumerate(shifts):
        for staff in staff_list:
            if shift.type in [ShiftType.PUBLIC_HOL_PM, ShiftType.WEEKEND_PM]:
                model.Add(assignments[(staff.name, s_idx+1)] == 0)
    
    # Hard Constraint: Public Holiday Bidding
    for s_idx, shift in enumerate(shifts):
        s_bidders = []
        for staff in staff_list:
            if shift.date in staff.bidding_dates: # Bidding dates only contains Public Holidays
                s_bidders.append(staff)
        if len(s_bidders) != 0: # Have Bidders, IF NO BIDDERS CODE SHOULD SITLL FOLLOW HARD CONSTRAINT 1
            model.Add(sum(assignments([bidder.name, s_idx] for bidder in s_bidders) == 1)) # Only one

    # Soft Constraint: Fairness
    highest = 0
    lowest = 100000
    for staff in staff_list:
        if staff.ytd_points > highest:
            highest = staff.ytd_points
        if staff.ytd_points < lowest:
            lowest = staff.ytd_points
    highest_lowest_diff = highest - lowest

    # Finalize and Solve
    model.Minimize(sum(highest_lowest_diff))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 100.0 
    status = solver.Solve(model)

    # if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    #     results = [] 
    #     for s_idx, s_obj in enumerate(shifts):
    #         for staff in staff_list:
    #             if solver.Value(assignments[(staff.name, s_idx)]) == 1:
    #                 # Update Staff Score
    #                 staff.ytd_points += s_obj.type.points
    #                 # Update Shift's Occupant
    #                 s_obj.assigned_staff = staff
    #                 # PH Immunity
    #                 if s_obj.type in [ShiftType.PUBLIC_HOL_AM, ShiftType.PUBLIC_HOL_PM]:
    #                     staff.PH_Immunity = True 

    #                 results.append({"Date": s_obj.date, "Shift": s_obj.type.name, "Staff": staff.name})
    #     return results 
    # return None

            


'''
    1. Account for Shift Types and Roles (DONE)
    2. Account for YTD scores (DONE)
    3. Account for PM Shifts where Staff do not need to work the next day (DONE)
    4. Account for voluntary basis
    5. Account for PHs
    6. Account for blackout dates (DONE)
'''
'''Hard Constraint: Every shift must have 1 person assigned'''


