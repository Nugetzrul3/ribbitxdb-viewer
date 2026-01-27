from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from typing import Dict, Any, List
from PySide6.QtGui import QColor


class HistoryTableModel(QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self._columns = []
        self._rows = []

    def headerData(self, section, orientation, role = Qt.ItemDataRole.DisplayRole):
        """Return header data to display"""
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                if section < len(self._columns):
                    return self._columns[section]
            else:
                return str(section + 1)

        return None

    def data(self, index, role = Qt.ItemDataRole.DisplayRole):
        """Return data for a given cell"""
        if not index.isValid():
            return None

        row = index.row()
        column = index.column()
        value = self._rows[row][column]

        if role == Qt.ItemDataRole.DisplayRole:
            if isinstance(value, float):
                return f"{value:.4f}"
            return str(value) if value is not None else 'NULL'
        elif role == Qt.ItemDataRole.ForegroundRole:
            if value is None:
                return QColor("#6B7280")
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if isinstance(value, (int, float)):
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter

        return None

    def columnCount(self, parent = QModelIndex()):
        return len(self._columns)

    def rowCount(self, parent = QModelIndex()):
        return len(self._rows)

    def set_data(self, rows: List[Any]):
        """Set row and column data"""
        self.beginResetModel()
        self._columns = ['Database', 'Execution Timestamp', 'Execution Time (s)', 'Rows Affected', 'Query']
        self._rows = rows
        self.endResetModel()

    def flags(self, index: QModelIndex):
        """Item flags for table data item"""
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable