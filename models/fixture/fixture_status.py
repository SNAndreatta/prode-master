import enum

class FixtureStatus(enum.Enum):
    """Enum representing the status of a fixture."""

    TBD = "Time To Be Defined"
    NS = "Not Started"
    H1 = "First Half, Kick Off"
    HT = "Halftime"
    H2 = "Second Half, 2nd Half Started"
    ET = "Extra Time"
    BT = "Break Time"
    P = "Penalty In Progress"
    SUSP = "Match Suspended"
    INT = "Match Interrupted"
    FT = "Match Finished"
    AET = "Match Finished After Extra Time"
    PEN = "Match Finished After Penalty Shootout"
    PST = "Match Postponed"
    CANC = "Match Cancelled"
    ABD = "Match Abandoned"
    AWD = "Technical Loss"
    WO = "WalkOver"
    LIVE = "In Progress"

def string_to_enum(string: str) -> FixtureStatus:
    """Converts a string to a FixtureStatus enum.

    Args:
        string (str): The string to convert.

    Returns:
        FixtureStatus: The corresponding FixtureStatus enum.
    """
    for status in FixtureStatus:
        if status.name == string:
            return status
    return None