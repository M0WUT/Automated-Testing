from dataclasses import dataclass
import xlsxwriter
import logging
from typing import List


class ExcelWorksheetWrapper(xlsxwriter.workbook.Worksheet):
    currentColumn: int
    currentRow: int
    maxColumn: int
    maxRow: int
    hiddenColumns: List[int]
    headersRow: int

    def add_wrapper_attributes(self, name):
        self.currentColumn = 0
        self.currentRow = 0
        self.maxColumn = 0
        self.maxRow = 0
        self.hiddenColumns = []
        self.name = name
        self.headersRow = 0

    def hide_current_column(self) -> None:
        columnLetter = chr(self.currentColumn + ord('A'))
        self.set_column(
            f"{columnLetter}:{columnLetter}",
            None, None, {'hidden': True}
        )
        self.hiddenColumns.append(self.currentColumn)

    def hide_current_row(self) -> None:
        self.set_row(
            self.currentRow,
            None, None, {'hidden': True}
        )
        self.hiddenColumns.append(self.currentColumn)

    def new_row(self):
        self.currentColumn = 0
        self.maxRow = max(self.maxRow, self.currentRow)
        self.currentRow += 1

    def write_and_move_right(self, x):
        self.write(self.currentRow, self.currentColumn, x)
        self.maxColumn = max(self.maxColumn, self.currentColumn)
        self.currentColumn += 1

    def save_headers_row(self):
        self.headersRow = self.currentRow
