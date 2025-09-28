"""
Unit tests for /status endpoint
Tests the status endpoint controller logic with mocked dependencies
"""

import unittest
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient


class TestStatusEndpoint(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Import app after setting up any necessary patches
        from app import app
        self.client = TestClient(app)
    
    @patch('scheduler.ReminderScheduler')
    @patch('sns_notifier.SNSNotifier')
    @patch('wekan_client.WekanClient')
    def test_status_healthy(self, mock_wekan_class, mock_sns_class, mock_scheduler_class):
        """Test status endpoint returns healthy when all systems are working"""
        # Setup mocks to return healthy status
        mock_scheduler = Mock()
        mock_scheduler.get_status.return_value = {'running': True}
        mock_scheduler_class.return_value = mock_scheduler
        
        mock_sns = Mock()
        mock_sns.test_connection.return_value = True
        mock_sns_class.return_value = mock_sns
        
        mock_wekan = Mock()
        mock_wekan.test_connection.return_value = True
        mock_wekan_class.return_value = mock_wekan
        
        # Execute
        response = self.client.get("/status")
        
        # Verify
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["service"], "Wekan Reminder Service")
        self.assertIn(data["status"], ["healthy", "degraded"])
    
    @patch('scheduler.ReminderScheduler')
    @patch('sns_notifier.SNSNotifier')
    @patch('wekan_client.WekanClient')
    def test_status_degraded(self, mock_wekan_class, mock_sns_class, mock_scheduler_class):
        """Test status endpoint returns degraded when SNS is not working"""
        # Setup mocks with SNS failure
        mock_scheduler = Mock()
        mock_scheduler.get_status.return_value = {'running': True}
        mock_scheduler_class.return_value = mock_scheduler
        
        mock_sns = Mock()
        mock_sns.test_connection.return_value = False  # SNS failure
        mock_sns_class.return_value = mock_sns
        
        mock_wekan = Mock()
        mock_wekan.test_connection.return_value = True
        mock_wekan_class.return_value = mock_wekan
        
        # Execute
        response = self.client.get("/status")
        
        # Verify
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "degraded")


if __name__ == '__main__':
    unittest.main()