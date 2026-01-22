from dataclasses import dataclass, field
from enum import Enum, auto 
from typing import Set, Optional
from datetime import date, timedelta

class Role(Enum): # Fixed, The variables are just fixed labels which doesnt change 
    """"Types of staff memebrs based on their shift constraints"""
    STANDARD = auto() # auto assigns a unique value to the attributes starting from 1 
    NO_PM = auto()
    WEEKEND_ONLY = auto()

class ShiftType(Enum): # Fixed
    # Format: (Value, Points)
    WEEKDAY_PM = (1, 1.0)
    WEEKEND_FULL_DAY = (2, 3.0)  # 24h shift = AM(1.5) + PM(1.5)
    PUBLIC_HOL_AM = (3, 1.5)
    PUBLIC_HOL_PM = (4, 1.5)

    def __init__(self, id, points):
        self.id = id
        self.points = points

@dataclass # Because of this line, a __init__() method is not needed
class Staff: # Fluid
    """Represents a staff member and their scheduling constraints"""
    name: str
    role: Role
    ytd_points: float = 0.0
    blackout_dates: Set[date] = field(default_factory=set) # Ensures every Staff object created has their own unique dates
    bidding_dates: Set[date] = field(default_factory=set)
    last_PH: Optional[date] = None
    

    @property
    def immunity_expiry_date(self):
        if self.last_PH is None:
            return None
        else:
            return self.last_PH + timedelta(days=300)
    
    def is_immune_on(self, shift_date: date): 
        if self.last_PH is None:
            return False
        else:
            return self.last_PH < shift_date <= self.immunity_expiry_date  



@dataclass # Because of this line, a __init__() method is not needed 
class Shift: # Fluid
    """Keeps track of who is doing what shift on which date"""
    date: date
    type: ShiftType
    assigned_staff: Optional[Staff] = None # Optional[Staff] = None just enable for this attribute to be None to cater for cases where no staff are assigned yet


