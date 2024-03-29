from datetime import datetime
from typing import List, Optional

import git
import xlsxwriter


class ExcelWorksheetWrapper(xlsxwriter.workbook.Worksheet):
    current_column: int
    current_row: int
    max_column: int
    max_row: int
    hidden_columns: List[int]
    headers_row: int

    AVAILABLE_COLOURS = [
        "blue",
        "red",
        "green",
        "orange",
        "purple",
        "magenta",
        "cyan",
        "gray",
        "brown",
        "black",
    ]

    def initialise(
        self,
        name,
        dut_name: Optional[str] = None,
        test_notes: Optional[str] = None,
    ):
        self.current_column = 0
        self.current_row = 0
        self.max_column = 0
        self.max_row = 0
        self.hidden_columns = []
        self.hidden_rows = []
        self.name = name
        self.headers_row = 0
        self.headers_column = 0
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
        self.write(5, 0, dut_name)
        self.write(5, 0, "Notes")
        self.write(5, 1, test_notes)

        self.headers_row = 8
        self.current_row = self.headers_row
        self.current_column = 0

    def hide_current_column(self) -> None:
        column_letter = chr(self.current_column + ord("A"))
        self.set_column(
            f"{column_letter}:{column_letter}", None, None, {"hidden": True}
        )
        self.hidden_columns.append(self.current_column)

    def hide_current_row(self) -> None:
        self.set_row(self.current_row, None, None, {"hidden": True})
        self.hidden_rows.append(self.current_column)

    def new_row(self):
        self.current_column = self.headers_column
        self.max_row = max(self.max_row, self.current_row)
        self.current_row += 1

    def new_column(self):
        self.current_row = self.headers_row
        self.max_column = max(self.max_column, self.current_column)
        self.current_column += 1

    def write_and_move_right(self, x):
        self.write(self.current_row, self.current_column, x)
        self.max_column = max(self.max_column, self.current_column)
        self.current_column += 1

    def write_and_move_down(self, x):
        self.write(self.current_row, self.current_column, x)
        self.max_row = max(self.max_row, self.current_row)
        self.current_row += 1

    def save_headers_row(self):
        self.headers_row = self.current_row

    def plot_current_column(self, extra_commands: dict = None):
        """
        Plots current column with self.headers_column as x axis
        Set second_y_axis to True to plot on secondary y axis
        """

        # Plot upper tone
        column = chr(self.current_column + ord("A"))
        headers_column = chr(self.headers_column + ord("A"))
        # +1 for data being one row lower, +1 for stupid 0/1 indexing
        start_row = self.headers_row + 2
        commands = {
            "name": f"='{self.name}'!${column}${self.headers_row + 1}",
            "categories": f"='{self.name}'!${headers_column}${start_row}:"  # noqa E501
            f"${headers_column}{self.max_row + 1}",
            "values": f"='{self.name}'!${column}${start_row}:"
            f"${column}{self.max_row + 1}",
        }
        if extra_commands:
            commands.update(extra_commands)
        self.chart.add_series(commands)
