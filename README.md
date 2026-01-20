# AI Staff Roster Engine
This is an automated rostering engine built using Google OR-Tools to assign staff to shifts based on constraints that were given.

## Key Features
1. Ensures fairness in shift assignment using a point based system
2. Constraint Based:
  - Assigns staffs to shifts based on their roles.
  - Staff will not be able to work the next shift following a PM shift for safety reasons.
  - Staff will be entitled to take blackout dates where they would not be assigned a shift.
  - Staff will be able to bid for specific Public Holiday shifts which they would want to work on.
  - Staff will be taken out of pool for Public Holiday shifts if the shift is within 300 days of their last worked Public Holiday, unless they bidded for it.

## Tech Stack
- **Language:** Python 3.14+
- **Optimisation:** Google OR-Tools (CP-SAT Solver)
- **Interface:** Streamlit
- **Data Handling:** Pandas, Openpyxl

## Installation & Setup
### To get this project running on your local machine, follow these steps:
```bash
# Clone the repo
git clone [https://github.com/Ktyc/roster_project_2.git](https://github.com/Ktyc/roster_project_2.git)

# Create a virtual environment
python -m venv venv

# Activate the environment
# On Windows:
.\venv\Scripts\activate  
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt```


### To generate test file:
```bash
python generate_data.py


### To launch dashboard interface:
```bash
streamlit run app.py


## File Structure
```text
roster_project_main/
├── data/
│   └── staff_list.xlsx       # Input data template
├── src/
│   ├── engine.py             # Core OR-Tools solver logic
│   ├── models.py             # Staff and Shift classes
│   └── io_handler.py         # Excel loading/saving
├── tests/
│   ├── test_immunity.py      # PH logic test cases
│   └── test_constraints.py   # Role constraint tests
├── .gitignore                # Files to skip (venv, pycache)
├── app.py                    # Streamlit UI entry point
├── README.md                 # Project documentation
└── requirements.txt          # Python dependencies
