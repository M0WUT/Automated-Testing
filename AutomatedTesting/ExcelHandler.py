import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

import git
import xlsxwriter


class ExcelWorksheetWrapper(xlsxwriter.workbook.Worksheet):
    currentColumn: int
    currentRow: int
    maxColumn: int
    maxRow: int
    hiddenColumns: List[int]
    headersRow: int

    def initialise(
        self,
        name,
        dutName: Optional[str] = None,
        testNotes: Optional[str] = None,
    ):
        self.currentColumn = 0
        self.currentRow = 0
        self.maxColumn = 0
        self.maxRow = 0
        self.hiddenColumns = []
        self.name = name
        self.headersRow = 0
        self.headersColumn = "A"
        self.chart = None

        now = datetime.now()

        self.write(0, 0, "Date")
        self.write(0, 1, now.strftime("%d/%m/%Y"))
        self.write(1, 0, "Time")
        self.write(1, 1, now.strftime("%H:%M"))
        self.write(2, 0, "Test code version")
        repo = git.Repo(search_parent_directories=True)
        self.write(2, 1, repo.head.object.hexsha)
        self.write(3, 0, "Repo status")
        self.write(3, 1, "Dirty" if repo.is_dirty() else "Clean")
        self.write(4, 0, "DUT Name")
        self.write(5, 0, dutName)
        self.write(5, 0, "Notes")
        self.write(5, 1, testNotes)

        self.headersRow = 7
        self.currentRow = self.headersRow

    def hide_current_column(self) -> None:
        columnLetter = chr(self.currentColumn + ord("A"))
        self.set_column(
            f"{columnLetter}:{columnLetter}", None, None, {"hidden": True}
        )
        self.hiddenColumns.append(self.currentColumn)

    def hide_current_row(self) -> None:
        self.set_row(self.currentRow, None, None, {"hidden": True})
        self.hiddenColumns.append(self.currentColumn)

    def new_row(self):
        self.currentColumn = self.headersColumn
        self.maxRow = max(self.maxRow, self.currentRow)
        self.currentRow += 1

    def new_column(self):
        self.currentRow = self.headersRow
        self.maxColumn = max(self.maxColumn, self.currentColumn)
        self.currentColumn += 1

    def write_and_move_right(self, x):
        self.write(self.currentRow, self.currentColumn, x)
        self.maxColumn = max(self.maxColumn, self.currentColumn)
        self.currentColumn += 1

    def write_and_move_down(self, x):
        self.write(self.currentRow, self.currentColumn, x)
        self.maxRow = max(self.maxRow, self.currentRow)
        self.currentRow += 1

    def save_headers_row(self):
        self.headersRow = self.currentRow

    def plot_current_column(self):
        # Plot upper tone
        column = chr(self.currentColumn + ord("A"))
        # +1 for data being one row lower, +1 for stupid 0/1 indexing
        startRow = self.headersRow + 2
        self.chart.add_series(
            {
                "name": f"='{self.name}'!${column}${self.headersRow + 1}",
                "categories": f"='{self.name}'!${self.headersColumn}${startRow}:"
                f"${self.headersColumn}{self.maxRow + 1}",
                "values": f"='{self.name}'!${column}${startRow}:"
                f"${column}{self.maxRow + 1}",
            }
        )
