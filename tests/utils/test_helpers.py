from unittest.mock import patch
from src.utils import helpers
import unittest
import datetime


class TestHelperUtils(unittest.TestCase):
    def test_trim_string(self):
        long = "teststring" * 11
        short = "teststring"

        long_res = helpers.trim_string(long)
        self.assertEqual(long[:50] + "...", long_res, 'String should be trimmed to 50 characters')
        short_res = helpers.trim_string(short)
        self.assertEqual(short, short_res, 'Shorter string has been trimmed')

    def test_parse_timestamp(self):
        timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        parsed = helpers.parse_timestamp(timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f"))
        self.assertEqual(timestamp.strftime("%Y-%m-%d %H:%M:%S"), parsed, 'Timestamp should be parsed correctly')

    def test_try_convert_float(self):
        with patch('src.utils.helpers.float') as mock_float:
            mock_float.side_effect = [1.0, ValueError]

            self.assertTrue(helpers.try_convert_float('1.0'), '1.0 should be float')
            self.assertFalse(helpers.try_convert_float('1.a'), '1.a should not be float')

            self.assertEqual(2, mock_float.call_count, 'Expected 2 calls; one for success and one for exception')

    def test_try_convert_int(self):
        with patch('src.utils.helpers.int') as mock_int:
            mock_int.side_effect = [10, 5, ValueError]

            self.assertTrue(helpers.try_convert_int('10'), '10 should be an int')
            self.assertTrue(helpers.try_convert_int('5.5'), '5.5 should be floored to 5 and recognised as int')
            self.assertFalse(helpers.try_convert_int('10b'), '10b should not be float')

            self.assertEqual(3, mock_int.call_count, 'Expected 3 calls; two for success and one for exception')

    def test_get_dummy_data(self):
        self.assertEqual(0, helpers.get_dummy_data('INTEGER', 'id'))
        self.assertEqual(0.0, helpers.get_dummy_data('REAL', 'amount'))
        self.assertEqual("'column'", helpers.get_dummy_data('STRING', 'column'))

    @patch('src.utils.helpers.QApplication.clipboard')
    def test_copy_to_clipboard(
            self,
            mock_clipboard
    ):
        clipboard = mock_clipboard.return_value
        helpers.copy_to_clipboard("Test Clipboard Text")
        clipboard.setText.assert_called_once_with("Test Clipboard Text")