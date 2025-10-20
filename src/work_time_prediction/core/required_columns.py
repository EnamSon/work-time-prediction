# Configuration globale des colonnes
from __future__ import annotations
from copy import copy
class RequiredColumnsMapping:
    def __init__(
            self, id_column: str, date_column: str, start_time_column: str, end_time_column: str
    ) -> None:
        self.id = id_column
        self.date = date_column
        self.start = start_time_column
        self.end = end_time_column

    def clean(self) -> RequiredColumnsMapping:
        column_clean = copy(self)
        column_clean.id = self.id.replace(" ", "_")
        column_clean.date = self.date.replace(" ", "_")
        column_clean.start = self.start.replace(" ", "_")
        column_clean.end = self.end.replace(" ", "_")
        return column_clean

