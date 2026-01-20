from datetime import date, timedelta
from src.models import Staff, Shift, ShiftType, Role
from src.engine import assign_staff_to_shift

def run_test_case(name, staff_list, shifts):
    print(f"\n>>> TESTING: {name}")
    results = assign_staff_to_shift(shifts, staff_list)
    
    if results:
        for res in results:
            # We use an f-string with formatting here!
            print(f"✅ SUCCESS: {res['Staff']} assigned to {res['Date']:%d %b}, Staff is PH immune from {res['PH Immunity Period']}")
    else:
        print("❌ RESULT: Infeasible (Constraints Blocked Everyone)")

# --- SETUP DATA ---
# Shift is Jan 25th
target_date1 = date(2026, 2, 17)
target_date2 = date(2026, 2, 18)
ph_shift = [Shift(date=target_date1, type=ShiftType.PUBLIC_HOL_AM), Shift(date=target_date2, type=ShiftType.PUBLIC_HOL_AM)]

# # --- TEST 1: Alice is Immune (Worked 10 days ago) ---
# alice = Staff(name="Immune_Alice", role=Role.STANDARD, last_PH=date(2026, 1, 15))
# bob = Staff(name="Eligible_Bob", role=Role.STANDARD, last_PH=date(2025, 12, 1))

# run_test_case("Normal Immunity (Should pick Bob)", [alice, bob], ph_shift)

# # --- TEST 2: Alice Bids (Overrides her own immunity) ---
# alice.bidding_dates = {target_date}
# run_test_case("Bidding Override (Should pick Alice)", [alice, bob], ph_shift)

# # --- TEST 3: Boundary Test (Immunity just expired) ---
# # 32 days before Jan 25 is Dec 24
# alice.bidding_dates = set() # Clear bid
# alice.last_PH = target_date - timedelta(days=32) 
# # Alice should now be eligible again. 
# # Between Alice (32 days ago) and Bob (55 days ago), 
# # the solver will pick whoever helps 'Fairness' (lowest points).
# run_test_case("Boundary Test (Alice's immunity expired)", [alice, bob], ph_shift)


# --- SCENARIO A: Normal Immunity (Alice is immune, but has LOWER points) ---
# Solver WANTS to pick Alice to be fair, but Immunity should stop it.
# Test if last_PH gets updated and block alice out 
alice = Staff(name="Immune_Alice", role=Role.STANDARD, last_PH=date(2025, 1, 15), ytd_points=0.0, bidding_dates=(date(2026, 2, 17),))
bob = Staff(name="Eligible_Bob", role=Role.STANDARD, last_PH=date(2026, 1, 15), ytd_points=100.0) # bob should be immune to 18 Feb shift, so error should be returned 

run_test_case("Immunity vs Fairness (Should pick Bob despite high points)", [alice, bob], ph_shift)


# --- SCENARIO C: Boundary Test (Alice's immunity expired, she has LOWER points) ---
# Now Alice is eligible AND has lower points. Solver should definitely pick her.
# alice.last_PH = target_date - timedelta(days=101) 

# run_test_case("Boundary Test (Should now pick Alice for fairness)", [alice, bob], ph_shift)