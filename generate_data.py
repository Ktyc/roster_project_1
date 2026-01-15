import pandas as pd
import random
from datetime import date, timedelta

def generate_full_year_staff_data(filename="full_year_2026_staff.xlsx"):
    names = [
        "Aaron Tan", "Beatrice Lim", "Charlie Ng", "David Seah", "Elena Gomez", 
        "Farhan Idris", "Grace Wong", "Hanafi Ali", "Isaac Low", "Jasmine Kaur",
        "Kevin Chen", "Lily Ortega", "Marcus Teo", "Nadia Rosli", "Owen Yap", 
        "Priya Mani", "Quentin Lee", "Rachel Sim", "Suresh Raj", "Tessa Quinn",
        "Umar Khalid", "Vicky Zhao", "William Goh", "Xavier Ong", "Yvonne Lim", 
        "Zackary Ho", "Adam Smith", "Bella Swan", "Chris Pratt", "Diana Prince",
        "Ethan Hunt", "Fiona Shrek", "George King", "Holly Wood", "Ian Wright",
        "Jenny Han", "Karl Marx", "Luna Love", "Micky Mouse", "Nina Dobrev"
    ]
    
    # Sample 2026 Public Holidays for bidding simulation
    holidays_2026 = ["2026-01-01", "2026-02-17", "2026-02-18", "2026-04-03", "2026-05-01", "2026-05-21", "2026-08-09", "2026-12-25"]
    
    roles = ["STANDARD", "NO_PM", "WEEKEND_ONLY"]
    year_start = date(2026, 1, 1)
    
    data = []
    for name in names:
        role = random.choice(roles)
        #ytd_points = float(random.randint(0, 50))
        ytd_points = 0.0
        
        # Blackout Dates
        blackout_list = []
        for _ in range(random.randint(15, 25)):
            # First, pick the random number
            random_day_idx = random.randint(0, 364)
            # Then, add it to the start date
            random_day = year_start + timedelta(days=random_day_idx)
            ######blackout_list.append(random_day.strftime("%Y-%m-%d"))
        blackout_str = ", ".join(sorted(list(set(blackout_list))))
        
        # --- NEW COLUMNS ---
        # Bid for 1-3 random holidays if available
        PH_Avail = random.choice["Yes", "No"]
        bidding = ", ".join(random.sample(holidays_2026, k=random.randint(1, 3))) if PH_Avail == "Yes" else "N/A"
        
        PH_Immunity = random.choice["Immune", "Not Immune"]

        data.append({
            "Name": name,
            "Role": role,
            "Ytd_Points": ytd_points,
            "Blackout_Dates": blackout_str,
            "PH_Bidding": bidding,
            "PH_Immunity": PH_Immunity
        })

    df = pd.DataFrame(data)
    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='2026_Master_List')
        workbook, worksheet = writer.book, writer.sheets['2026_Master_List']
        header_fmt = workbook.add_format({'bold': True, 'bg_color': '#4F81BD', 'font_color': 'white', 'border': 1})
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_fmt)
            worksheet.set_column(col_num, col_num, 20)

    print(f"✅ Created '{filename}' with PH Bidding columns.")

if __name__ == "__main__":
    generate_full_year_staff_data()