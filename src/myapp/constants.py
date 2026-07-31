
from typing import Final

class _MissingType:
    """
    Sentinel type for distinguishing 'missing' from None.
    Use the singleton MISSING instead of instantiating this class.
    """
    def __repr__(self) -> str:
        return "MISSING"

    def __bool__(self) -> bool:
        return False

MISSING: Final[_MissingType] = _MissingType()

STATUS_OPTIONS = [
    "Not Applied",
    "Applied",
    "Interview Scheduled",
    "Interviewed",
    "Offer",
    "Rejected",
    "Withdrawn",
    ]

JOB_TYPE_OPTIONS = [
    "Full time",
    "Part time",
    "Contract",
    ]

WORK_ARRANGEMENT_OPTIONS = [
    "On-site", 
    "Hybrid", 
    "Remote"
    ]

STATUS_COLOURS = {
    "Not Applied": "#256D6D",           # Desaturated Teal - informative
    "Applied": "#3B82F6",               # Blue - informative
    "Interview Scheduled": "#F59E0B",   # Amber - attention/upcoming
    "Interviewed": "#8B5CF6",           # Purple - in progress/waiting
    "Offer": "#2b7a2b",                 # Green - success/positive
    "Rejected": "#EF4444",              # Red - negative/closed
    "Withdrawn": "#6B7280",             # Gray - neutral/inactive
    }