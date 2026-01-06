from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QFileDialog, QMessageBox
)
from pathlib import Path


class OpenDatabaseDialog(QDialog):
    """Dialog for opening a database file"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.filepath = None
        self.setup_ui()

    def setup_ui(self):
        """Initialize dialog UI"""
        self.setWindowTitle("Open Database")
        self.setModal(True)
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        label = QLabel("Select a RibbitXDB database file to open:")
        label.setWordWrap(True)
        layout.addWidget(label)

        file_layout = QHBoxLayout()

        self.filepath_input = QLineEdit()
        self.filepath_input.setPlaceholderText("Path to database file...")
        self.filepath_input.textChanged.connect(self.validate_input)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_file)

        file_layout.addWidget(self.filepath_input)
        file_layout.addWidget(browse_btn)

        layout.addLayout(file_layout)

        layout.addStretch()

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.open_btn = QPushButton("Open")
        self.open_btn.setEnabled(False)
        self.open_btn.clicked.connect(self.accept)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(self.open_btn)

        layout.addLayout(button_layout)

    def browse_file(self):
        """Open file browser dialog"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Open Database File",
            "",
            "Database Files (*.rbx);;All Files (*.*)",
        )

        if filepath:
            self.filepath_input.setText(filepath)

    def validate_input(self):
        """Validate the file path input"""
        filepath = self.filepath_input.text().strip()

        if not filepath:
            self.open_btn.setEnabled(False)
            return

        path = Path(filepath)

        if path.exists() and path.is_file():
            self.open_btn.setEnabled(True)
        else:
            self.open_btn.setEnabled(False)

    def accept(self):
        """Handle OK button"""
        filepath = self.filepath_input.text().strip()
        path = Path(filepath)

        if not path.exists():
            QMessageBox.warning(
                self,
                "File Not Found",
                f"The file '{filepath}' does not exist."
            )
            return

        if not path.is_file():
            QMessageBox.warning(
                self,
                "Invalid File",
                f"'{filepath}' is not a valid file."
            )
            return

        self.filepath = filepath
        super().accept()

    def get_filepath(self) -> str:
        """Get the selected file path"""
        return self.filepath