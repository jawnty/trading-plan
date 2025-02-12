import unittest
from unittest.mock import patch, MagicMock
from basic.trading_plan import TradingPlan

class TestTradingPlan(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.trading_plan = TradingPlan()

    def test_google_sheets_connection(self):
        """Test that we can connect to Google Sheets."""
        with patch('googleapiclient.discovery.build') as mock_build:
            mock_service = MagicMock()
            mock_build.return_value = mock_service
            # Test connection logic
            self.assertIsNotNone(self.trading_plan.service)

    def test_risk_calculation(self):
        """Test risk calculation functionality."""
        test_data = {
            'entry_price': 100.0,
            'stop_loss': 90.0,
            'position_size': 1000.0
        }
        expected_risk = 100.0  # (100 - 90) * 1000 * 0.01
        result = self.trading_plan.calculate_risk(test_data)
        self.assertEqual(result, expected_risk)

    def test_invalid_input_handling(self):
        """Test how the system handles invalid input."""
        with self.assertRaises(ValueError):
            self.trading_plan.validate_trading_data({})

    def test_api_error_handling(self):
        """Test handling of API errors."""
        with patch('googleapiclient.discovery.build') as mock_build:
            mock_build.side_effect = Exception("API Error")
            with self.assertRaises(Exception):
                self.trading_plan.connect_to_sheets()

if __name__ == '__main__':
    unittest.main() 