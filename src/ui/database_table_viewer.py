from PySide6.QtWidgets import (
    QTableView, QHeaderView, QMessageBox,
    QVBoxLayout, QWidget, QLabel, QStackedWidget,
    QHBoxLayout, QLineEdit, QPushButton, QListWidgetItem, QToolBar
)
from .custom.multiselect_combo_box import MultiSelectComboBox
from ..models.database_table_model import DatabaseTableModel
from ..utils import try_convert_int, try_convert_float
from ..core.database_manager import DatabaseManager
from .pagination_widget import PaginationWidget
from typing import Dict, Any, Optional
from PySide6.QtCore import Qt



class DatabaseTableViewer(QWidget):
    """Widget to display table data"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Table Viewer")
        self.current_table: Optional[str] = None
        self.current_db_manager: Optional[DatabaseManager] = None
        self.table_view = QTableView()
        self.data_model = DatabaseTableModel()
        self.table_view.setModel(self.data_model)
        self.filters = {}
        self.setup_ui()

    def setup_ui(self):
        """Create UI with table and pagination"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        toolbar = QToolBar()
        self.main_layout.addWidget(toolbar)
        self.multi_combo_box = MultiSelectComboBox()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search Data")
        
        self.search_input.setMaximumWidth(300)
        self.search_input.setEnabled(False)
        self.search_input.returnPressed.connect(self.search)

        self.search_button = QPushButton("Search🔍")
        self.search_button.clicked.connect(self.search)

        toolbar.addWidget(QLabel("Columns to search: "))
        toolbar.addWidget(self.multi_combo_box)
        toolbar.addWidget(self.search_input)
        toolbar.addWidget(self.search_button)

        self.setup_table_view()
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(self.table_view)

        self.empty_view_label = QLabel("No Data")
        self.empty_view_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stacked_widget.addWidget(self.empty_view_label)

        self.stacked_widget.setCurrentIndex(0)
        self.main_layout.addWidget(self.stacked_widget)

        self.pagination = PaginationWidget()
        self.pagination.page_changed.connect(self.on_page_changed)
        self.pagination.page_size_changed.connect(self.on_page_size_changed)
        self.main_layout.addWidget(self.pagination)

    def setup_table_view(self):
        """Initialise table settings"""
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.table_view.setVerticalScrollMode(QTableView.ScrollMode.ScrollPerPixel)
        self.table_view.setHorizontalScrollMode(QTableView.ScrollMode.ScrollPerPixel)
        self.table_view.horizontalHeader().sortIndicatorChanged.connect(self.on_sorting_changed)

        v_header = self.table_view.verticalHeader()
        v_header.setVisible(True)

    def on_sorting_changed(self, idx: int, sorting: Qt.SortOrder):
        if idx == -1:
            return

        data = self.data_model.headerData(idx, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
        # need to flip
        sorting = 'DESC' if sorting == Qt.SortOrder.AscendingOrder else 'ASC'
        self.filters['sorting'] = {
            'column': data,
            'order': sorting
        }

        # call this function again for the sake of not duplicating
        current_page = self.pagination.current_page
        self.on_page_changed(current_page)


    def display_data(self, data: Dict[str, Any], db_manager: Optional[DatabaseManager] = None,
                     table_name: Optional[str] = None):
        """Display query results"""
        self.multi_combo_box.clear_items()
        self.search_input.setText("")
        if data.get('total_rows') == 0:
            self.clear_data()
            self.search_input.setEnabled(False)
            self.search_button.setEnabled(False)
            self.stacked_widget.setCurrentIndex(1)
            return

        self.stacked_widget.setCurrentIndex(0)

        self.current_db_manager = db_manager
        self.current_table = table_name

        h_header = self.table_view.horizontalHeader()
        h_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.table_view.setSortingEnabled(False)
        self.data_model.set_data(data)
        self.table_view.setSortingEnabled(True)
        h_header.setSortIndicator(-1, Qt.SortOrder.AscendingOrder)

        h_header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        h_header.setStretchLastSection(True)

        # column types
        schema = self.current_db_manager.get_table_schema(table_name)
        columns = [(x['column_name'], x['column_type']) for x in schema]

        self.multi_combo_box.add_items(columns)
        total_rows = data.get('total_rows', len(data.get('rows', [])))
        self.pagination.set_total_rows(total_rows)
        self.search_input.setEnabled(True)
        self.search_button.setEnabled(True)

    def on_page_changed(self, page: int):
        if not self.current_table or not self.current_db_manager:
            return

        try:
            page_size = self.pagination.page_size
            data = self.current_db_manager.get_table_data_paginated(
                self.current_table, page, page_size, self.filters
            )

            self.data_model.set_data(data)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load page: {str(e)}")
            raise e


    # We already have db manager, we can just query the paginated search
    def search(self):
        if len(self.search_input.text()) == 0:
            self.filters["columns"] = []
            page_size = self.pagination.page_size
            data = self.current_db_manager.get_table_data_paginated(
                self.current_table, 1, page_size, self.filters
            )

            h_header = self.table_view.horizontalHeader()
            h_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

            self.data_model.set_data(data)

            h_header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            h_header.setStretchLastSection(True)

            self.pagination.set_total_rows(data.get('total_rows', len(data.get('rows', []))))
            self.pagination.go_to_page(1)
            return

        filter_columns = []
        filter_items_selected = self.multi_combo_box.get_selected_items()
        search_text = self.search_input.text().strip()

        # when we search, we check the column types. for text types, convert
        # just pass the search query into the column filter. for int or real,
        # try to convert the search query into an int first, then try to
        # convert into a float. if any pass, then just add them to the filter
        for item in filter_items_selected:
            list_item: QListWidgetItem = item[1]
            data = list_item.data(Qt.ItemDataRole.UserRole)
            if data == "TEXT":
                filter_columns.append({
                    "condition": (item[0], f"LIKE '%{search_text}%'"),
                    "type": "LIKE"
                })
                continue
            # item is int or real
            if data == "INTEGER":
                if try_convert_int(search_text):
                    filter_columns.append({
                        "condition": (item[0], int(search_text)),
                        "type": "EQUALS"
                    })

            if data == "REAL":
                if try_convert_float(search_text):
                    filter_columns.append({
                        "condition": (item[0], float(search_text)),
                        "type": "EQUALS"
                    })


        self.filters['columns'] = filter_columns
        page_size = self.pagination.page_size
        data = self.current_db_manager.get_table_data_paginated(
            self.current_table, 1, page_size, self.filters
        )

        h_header = self.table_view.horizontalHeader()
        h_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.data_model.set_data(data)

        h_header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        h_header.setStretchLastSection(True)

        self.pagination.set_total_rows(data.get('total_rows', len(data.get('rows', []))))
        self.pagination.go_to_page(1)

    def on_page_size_changed(self, page_size: int):
        current_page = self.pagination.current_page
        self.on_page_changed(current_page)

    def clear_data(self):
        """Clear all data from the table"""
        empty_data = {
            'columns': [],
            'rows': [],
            'total_rows': 0
        }
        self.data_model.set_data(empty_data)
        self.pagination.reset()
        self.current_table = None
        self.current_db_manager = None