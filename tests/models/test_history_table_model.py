from src.models.history_table_model import HistoryTableModel, Qt, QColor
from unittest.mock import patch
from datetime import datetime
import unittest
import time


class TestHistoryTableModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = [
            [
                f'db{x}.rbx',
                datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),
                0.123456789 * x,
                x,
                None
            ]
            for x in range(1, 6)
        ]
        cls.model = HistoryTableModel()

    def test_set_data(self):
        with patch.object(HistoryTableModel, 'beginResetModel') as begin_mock, \
            patch.object(HistoryTableModel, 'endResetModel') as end_mock:
            self.model.set_data(self.rows)

            # assertions
            self.assertEqual(5, self.model.columnCount(), 'Data model columns not populated')
            self.assertEqual(5, self.model.rowCount(), 'Data model rows not populated')

            begin_mock.assert_called_once()
            end_mock.assert_called_once()

    def test_data_override(self):
        self.model.set_data(self.rows)

        # Test invalid calls
        result = self.model.data(self.model.index(-1, -1))
        self.assertIsNone(result, 'Invalid index should return None')

        result = self.model.data(self.model.index(5, 2))
        self.assertIsNone(result, 'Out of bound index should return None')

        result = self.model.data(self.model.index(0, 0), Qt.ItemDataRole.RangeModelDataRole)
        self.assertIsNone(result, 'Invalid role should return None')

        # Test different roles to enforce their expected return val
        # str
        result = self.model.data(self.model.index(0, 0))
        self.assertIsNotNone(result, 'Valid index should return a value')
        self.assertEqual(self.rows[0][0], result, 'Data should match expected value')

        result = self.model.data(self.model.index(1, 1), Qt.ItemDataRole.TextAlignmentRole)
        self.assertIsNone(result, 'No text alignment for str')

        result = self.model.data(self.model.index(2, 1),Qt. ItemDataRole.ForegroundRole)
        self.assertIsNone(result, 'ForegroundRole for str should return None')

        # int
        result = self.model.data(self.model.index(0, 3))
        self.assertIsInstance(result, str, 'Display Role should return a string')
        self.assertEqual(str(self.rows[0][3]), result, 'Data should match expected value')

        result = self.model.data(self.model.index(2, 3), Qt.ItemDataRole.TextAlignmentRole)
        self.assertEqual(result, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                         'Flag type of AlignRight or AlignVCenter should be returned')

        result = self.model.data(self.model.index(3, 3), Qt.ItemDataRole.ForegroundRole)
        self.assertIsNone(result, 'ForegroundRole for int should return None')

        # float
        result = self.model.data(self.model.index(3, 2))
        self.assertEqual(f"{self.rows[3][2]:.4f}", result, 'Float number should be formatted to 4 decimals')

        result = self.model.data(self.model.index(2, 2), Qt.ItemDataRole.TextAlignmentRole)
        self.assertEqual(result, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                         'Flag type of AlignRight or AlignVCenter should be returned')

        result = self.model.data(self.model.index(0, 2), Qt.ItemDataRole.ForegroundRole)
        self.assertIsNone(result, 'ForegroundRole for float should return None')

        # none
        result = self.model.data(self.model.index(1, 4))
        self.assertEqual('NULL', result, "None type should be rendered as 'NULL'")

        result = self.model.data(self.model.index(0, 4), Qt.ItemDataRole.ForegroundRole)
        self.assertIsInstance(result, QColor, 'Role should return a QColor')
        self.assertEqual('#6b7280', result.name(), 'Colour should be correct')

        result = self.model.data(self.model.index(2, 4), Qt.ItemDataRole.TextAlignmentRole)
        self.assertIsNone(result, 'No text alignment for none type')


    def test_headerData_override(self):
        self.model.set_data(self.rows)

        # invalid role
        result = self.model.headerData(1, Qt.Orientation.Horizontal, Qt.ItemDataRole.TextAlignmentRole)
        self.assertIsNone(result, 'Invalid role type should return None')

        # vertical header
        result = self.model.headerData(10, Qt.Orientation.Vertical)
        self.assertEqual('11', result, 'Vertical header should be incremented')

        # section data
        result = self.model.headerData(2, Qt.Orientation.Horizontal)
        self.assertEqual('Execution Time (s)', result, 'Incorrect horizontal header returned')

        result = self.model.headerData(5, Qt.Orientation.Horizontal)
        self.assertIsNone(result, 'Column index out of bound should return None')

