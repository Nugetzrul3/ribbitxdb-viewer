from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout


class AcceptActionDialog(QDialog):
    """Display general accept or decline dialog"""
    def __init__(self, parent=None, title: str = "Confirm", message: str = ""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.message = message
        self.setup_ui()

    def setup_ui(self):
        self.setModal(True)
        self.setFixedWidth(300)
        self.setFixedHeight(self.height())
        layout = QVBoxLayout(self)

        label = QLabel(self.message)
        label.setWordWrap(True)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        accept_button = QPushButton("Accept")
        accept_button.clicked.connect(self.accept)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(cancel_button)
        button_layout.addWidget(accept_button)

        layout.addWidget(label)
        layout.addLayout(button_layout)


