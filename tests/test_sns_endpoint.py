"""
Unit tests for /test/sns endpoint
Tests the SNS test endpoint controller logic with mocked SNS
"""

import unittest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient


class TestSNSEndpoint(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        from app import app
        self.client = TestClient(app)
    
    @patch('app.SNSNotifier')  # Patch where it's used in app.py
    def test_sns_test_success(self, mock_sns_class):
        """Test /test/sns endpoint when SNS test notification succeeds"""
        # Setup SNS mock to return success
        mock_sns = Mock()
        mock_sns.send_test_notification.return_value = True
        mock_sns_class.return_value = mock_sns
        
        # Execute
        response = self.client.post("/test/sns")
        
        # Verify
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("SNS notification sent successfully", data["message"])
        
        # Verify SNS test notification was called
        mock_sns.send_test_notification.assert_called_once()
    
    @patch('app.SNSNotifier')  # Patch where it's used in app.py
    def test_sns_test_failure(self, mock_sns_class):
        """Test /test/sns endpoint when SNS test notification fails"""
        # Setup SNS mock to return failure
        mock_sns = Mock()
        mock_sns.send_test_notification.return_value = False
        mock_sns_class.return_value = mock_sns
        
        # Execute
        response = self.client.post("/test/sns")
        
        # Verify
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("Failed to send test SNS notification", data["message"])


if __name__ == '__main__':
    unittest.main()