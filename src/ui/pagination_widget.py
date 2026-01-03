from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QIntValidator
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QComboBox, QPushButton, QLineEdit


class PaginationWidget(QWidget):
    """Pagination widget for table view"""

    # Signals
    page_changed = pyqtSignal(int)
    page_size_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.current_page = 1
        self.total_pages = 1
        self.page_size = 50
        self.total_rows = 0
        self.setup_ui()

    def setup_ui(self):
        """Pagination UI initialisation"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        # Page size selector
        layout.addWidget(QLabel('Rows per page:'))

        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["25", "50", "100", "200", "500"])
        self.page_size_combo.setCurrentText("50")
        self.page_size_combo.currentTextChanged.connect(self.on_page_size_changed)
        self.page_size_combo.setMaximumWidth(80)
        layout.addWidget(self.page_size_combo)

        layout.addStretch()

        # Navigation buttons
        self.first_btn = QPushButton("First")
        self.first_btn.clicked.connect(lambda: self.go_to_page(1))
        self.first_btn.setMaximumWidth(80)
        layout.addWidget(self.first_btn)

        self.prev_btn = QPushButton("Prev")
        self.prev_btn.clicked.connect(self.previous_page)
        self.prev_btn.setMaximumWidth(80)
        layout.addWidget(self.prev_btn)

        # Page info
        self.page_label = QLabel("Page 1 of 1")
        self.page_label.setMinimumWidth(100)
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.page_label)

        # Page input
        layout.addWidget(QLabel("Go to:"))
        self.page_input = QLineEdit()
        self.page_input.setMaximumWidth(60)
        self.page_input.setValidator(QIntValidator(1, 999999))
        self.page_input.returnPressed.connect(self.on_page_input)
        layout.addWidget(self.page_input)

        self.next_btn = QPushButton("Next")
        self.next_btn.clicked.connect(self.next_page)
        self.next_btn.setMaximumWidth(80)
        layout.addWidget(self.next_btn)

        self.last_btn = QPushButton("Last")
        self.last_btn.clicked.connect(lambda: self.go_to_page(self.total_pages))
        self.last_btn.setMaximumWidth(80)
        layout.addWidget(self.last_btn)

        layout.addStretch()

        # Total rows info
        self.info_label = QLabel("Total: 0 rows")
        layout.addWidget(self.info_label)

        self.update_buttons()

    def set_total_rows(self, total_rows: int):
        """Set total number of rows and calculate pages"""
        self.total_rows = total_rows
        self.total_pages = max(1, (total_rows + self.page_size - 1) // self.page_size)

        # Reset to first page when data changes
        self.current_page = 1

        self.update_ui()

    def update_ui(self):
        """Update all UI elements"""
        self.page_label.setText(f"Page {self.current_page} of {self.total_pages}")
        self.info_label.setText(f"Total: {self.total_rows:,} rows")
        self.page_input.setPlaceholderText(str(self.current_page))
        self.update_buttons()

    def update_buttons(self):
        """Enable/disable buttons based on current page"""
        self.first_btn.setEnabled(self.current_page > 1)
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < self.total_pages)
        self.last_btn.setEnabled(self.current_page < self.total_pages)

    def go_to_page(self, page: int):
        """Navigate to specific page"""
        if page < 1 or page > self.total_pages:
            return

        if page != self.current_page:
            self.current_page = page
            self.update_ui()
            self.page_changed.emit(page)

    def next_page(self):
        """Go to next page"""
        self.go_to_page(self.current_page + 1)

    def previous_page(self):
        """Go to previous page"""
        self.go_to_page(self.current_page - 1)

    def on_page_input(self):
        """Handle manual page input"""
        try:
            page = int(self.page_input.text())
            self.go_to_page(page)
            self.page_input.clear()
        except ValueError:
            pass

    def on_page_size_changed(self, text: str):
        """Handle page size change"""
        try:
            new_size = int(text)
            if new_size != self.page_size:
                old_size = self.page_size
                old_page = self.current_page
                self.page_size = new_size
                first_row_idx = (old_page - 1) * old_size
                new_page = (first_row_idx // new_size) + 1
                self.total_pages = max(1, (self.total_rows + self.page_size - 1) // self.page_size)
                new_page = min(new_page, self.total_pages)
                self.current_page = new_page
                # Recalculate pages
                # self.total_pages = max(1, (self.total_rows + self.page_size - 1) // self.page_size)
                # self.current_page = min(self.current_page, self.total_pages)
                self.update_ui()
                self.page_size_changed.emit(new_size)
        except ValueError:
            pass

    def reset(self):
        """Reset pagination to initial state"""
        self.current_page = 1
        self.total_pages = 1
        self.total_rows = 0
        self.update_ui()