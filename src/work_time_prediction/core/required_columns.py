# Configuration globale des colonnes
from __future__ import annotations
from copy import copy

class RequiredColumnsMapping:
    def __init__(
            self, id="Employee ID", date = "Date", start = "First Punch", end = "Last Punch"
    ) -> None:
        self.id = id
        self.date = date
        self.start = start
        self.end = end

    def clean(self) -> RequiredColumnsMapping:
        column_clean = copy(self)
        column_clean.id = self.id.replace(" ", "_")
        column_clean.date = self.date.replace(" ", "_")
        column_clean.start = self.start.replace(" ", "_")
        column_clean.end = self.end.replace(" ", "_")
        return column_clean

required_columns = RequiredColumnsMapping()
