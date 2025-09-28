"""
Unit tests for /reminders/run endpoint
Tests the manual reminder trigger endpoint with mocked scheduler
"""

import unittest
import sys
import os
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

# Add project root to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app


class TestRemindersRunEndpoint(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.client = TestClient(app)
    
    @patch('app.scheduler')  # Mock the global scheduler variable
    def test_reminders_run_success(self, mock_scheduler):
        """Test /reminders/run endpoint when manual check succeeds"""
        # Setup mock scheduler response
        mock_scheduler.run_manual_check.return_value = {
            'success': True,
            'timestamp': '2025-09-27T10:00:00',
            'due_cards_count': 2,
            'due_cards': [
                {'title': 'Card 1', 'board': 'Test Board'},
                {'title': 'Card 2', 'board': 'Test Board'}
            ],
            'notification_sent': True,
            'execution_time_seconds': 1.5
        }
        
        # Execute
        response = self.client.post("/reminders/run")
        
        # Verify
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["due_cards_count"], 2)
        self.assertTrue(data["notification_sent"])
        self.assertEqual(data["execution_time_seconds"], 1.5)
        
        # Verify scheduler was called
        mock_scheduler.run_manual_check.assert_called_once()
    
    @patch('app.scheduler')
    def test_reminders_run_no_cards(self, mock_scheduler):
        """Test /reminders/run endpoint when no cards are due"""
        # Setup mock scheduler response for no due cards
        mock_scheduler.run_manual_check.return_value = {
            'success': True,
            'timestamp': '2025-09-27T10:00:00',
            'due_cards_count': 0,
            'due_cards': [],
            'notification_sent': False,
            'execution_time_seconds': 0.8
        }
        
        # Execute
        response = self.client.post("/reminders/run")
        
        # Verify
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["due_cards_count"], 0)
        self.assertFalse(data["notification_sent"])


if __name__ == '__main__':
    unittest.main()