# Simplified utils - only export what the new pipeline needs
from .csv_loader import parse_csv

__all__ = [
    "parse_csv",
]
