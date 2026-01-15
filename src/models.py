from dataclasses import dataclass, field
from enum import Enum, auto 
from typing import Set, Optional
from datetime import date

class Role(Enum): # Fixed, The variables are just fixed labels which doesnt change 
    """"Types of staff memebrs based on their shift constraints"""
    STANDARD = auto() # auto assigns a unique value to the attributes starting from 1 
    NO_PM = auto()
    WEEKEND_ONLY = auto()

class ShiftType(Enum): # Fixed 
    # Format: (Value, Points)
    WEEKDAY_PM = (1, 1.0)
    WEEKEND_AM = (2, 1.5)
    WEEKEND_PM = (3, 1.5)
    PUBLIC_HOL_AM = (4, 1.5)
    PUBLIC_HOL_PM = (5, 1.5)

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
    PH_Immunity: bool = False

@dataclass # Because of this line, a __init__() method is not needed 
class Shift: # Fluid
    """Keeps track of who is doing what shift on which date"""
    date: date
    type: ShiftType
    assigned_staff: Optional[Staff] = None # Optional[Staff] = None just enable for this attribute to be None to cater for cases where no staff are assigned yet