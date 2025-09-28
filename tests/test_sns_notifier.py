"""
Unit tests for SNS Notifier
Tests the core SNS notification functionality with proper mocking
"""

import unittest
import sys
import os
from unittest.mock import patch, Mock
from datetime import datetime

# Add project root to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sns_notifier import SNSNotifier


class TestSNSNotifier(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Sample test data
        self.test_cards = [{
            'title': 'Test Card',
            'boardTitle': 'Test Board',
            'listTitle': 'Test List',
            'dueAtParsed': datetime.now()
        }]
    
    @patch('boto3.client')
    def test_sns_initialization(self, mock_boto_client):
        """Test SNS client is properly initialized with correct region"""
        mock_sns = Mock()
        mock_boto_client.return_value = mock_sns
        
        notifier = SNSNotifier()
        
        # Verify boto3.client was called with correct parameters
        mock_boto_client.assert_called_once_with('sns', region_name='eu-west-1')
        self.assertEqual(notifier.sns_client, mock_sns)
    
    @patch('boto3.client')
    def test_send_notification_success(self, mock_boto_client):
        """Test successful notification sending"""
        # Setup mock
        mock_sns = Mock()
        mock_sns.publish.return_value = {'MessageId': 'test-message-123'}
        mock_boto_client.return_value = mock_sns
        
        # Execute
        notifier = SNSNotifier()
        result = notifier.send_notification(self.test_cards)
        
        # Verify
        self.assertTrue(result)
        mock_sns.publish.assert_called_once()
        
        # Check correct topic ARN was used
        call_args = mock_sns.publish.call_args
        self.assertIn('arn:aws:sns:eu-west-1:228281126655:wekan-card-reminders', 
                     call_args[1]['TopicArn'])
    
    @patch('boto3.client')
    def test_send_notification_empty_cards(self, mock_boto_client):
        """Test behavior with no cards to notify about"""
        mock_sns = Mock()
        mock_boto_client.return_value = mock_sns
        
        notifier = SNSNotifier()
        result = notifier.send_notification([])
        
        # Should return True but not call publish
        self.assertTrue(result)
        mock_sns.publish.assert_not_called()


if __name__ == '__main__':
    unittest.main()