"""Galaxy picker dialog for rotation curve analysis."""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTableView, QHeaderView,
    QLineEdit, QLabel,
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem

import pandas as pd


class GalaxyPicker(QDialog):
    """Dialog for selecting a galaxy from the SPARC catalog."""

    galaxy_selected = pyqtSignal(str)

    def __init__(self, table1_df: pd.DataFrame, presence_map: dict | None = None, parent=None):
        super().__init__(parent)
        self.table1_df = table1_df
        self.presence_map = presence_map or {}
        self._setup_ui()
        self._populate_table()

    def _setup_ui(self):
        self.setWindowTitle("Select Galaxy")
        self.resize(900, 580)

        layout = QVBoxLayout(self)

        # Search box
        search_layout = QVBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type galaxy name...")
        self.search_input.textChanged.connect(self._filter_table)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Table
        self.table = QTableView()
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.setSortingEnabled(True)
        self.table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self.table)

        # Info label
        self.info_label = QLabel("Double-click to select a galaxy")
        self.info_label.setObjectName("subtitle")
        layout.addWidget(self.info_label)

    def _populate_table(self):
        """Populate table with galaxy data."""
        self.model = QStandardItemModel()
        headers = [
            "Galaxy", "Distance (Mpc)", "Inc (deg)", "L3.6 (10^9 Lsun)", "Vflat (km/s)",
            "Gas", "Disk", "Bulge", "SBdisk", "SBbul",
        ]
        self.model.setHorizontalHeaderLabels(headers)

        columns = ["Galaxy", "D", "Inc", "L36", "Vflat"]
        status_cols = ["Vgas", "Vdisk", "Vbul", "SBdisk", "SBbul"]

        for _, row in self.table1_df.iterrows():
            items = []
            for col in columns:
                val = row.get(col, "")
                if pd.notna(val):
                    if col in ["D", "Inc", "L36", "Vflat"]:
                        try:
                            val = f"{float(val):.2f}"
                        except (ValueError, TypeError):
                            val = str(val)
                    else:
                        val = str(val)
                else:
                    val = ""
                item = QStandardItem(val)
                item.setEditable(False)
                items.append(item)

            galaxy_key = str(row.get("Galaxy", "")).strip().lower()
            presence = self.presence_map.get(galaxy_key, {})
            for col in status_cols:
                has_component = bool(presence.get(col, False))
                item = QStandardItem("O" if has_component else "X")
                item.setTextAlignment(Qt.AlignCenter)
                item.setEditable(False)
                items.append(item)
            self.model.appendRow(items)

        self.table.setModel(self.model)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Store original data for filtering
        self._all_rows = [
            [self.model.item(r, c).text() for c in range(self.model.columnCount())]
            for r in range(self.model.rowCount())
        ]

    def _filter_table(self, text: str):
        """Filter table based on search text."""
        text = text.lower()

        self.model.removeRows(0, self.model.rowCount())

        for row_data in self._all_rows:
            if text in row_data[0].lower():  # Search in galaxy name
                items = [QStandardItem(val) for val in row_data]
                for item in items:
                    item.setEditable(False)
                self.model.appendRow(items)

        count = self.model.rowCount()
        self.info_label.setText(f"Showing {count} galaxies")

    def _on_double_click(self, index):
        """Handle double-click on table row."""
        if not index.isValid():
            return

        galaxy_name = index.sibling(index.row(), 0).data()
        if galaxy_name:
            self.galaxy_selected.emit(galaxy_name)
            self.accept()

    def get_selected_galaxy(self) -> str:
        """Get currently selected galaxy name."""
        indexes = self.table.selectedIndexes()
        if indexes:
            return indexes[0].sibling(indexes[0].row(), 0).data()
        return ""
