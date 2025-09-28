"""
AWS SNS Notification Module
Handles sending notifications via AWS Simple Notification Service
"""

import os
import boto3
import logging
from datetime import datetime
from typing import List, Dict, Optional
from botocore.exceptions import ClientError, BotoCoreError

# Set up logging
logger = logging.getLogger(__name__)

class SNSNotifier:
    """
    AWS SNS notification service for sending card reminders
    """
    
    def __init__(self):
        """Initialize SNS client with AWS credentials"""
        try:
            # Get AWS configuration from environment variables
            self.aws_region = os.getenv('AWS_REGION', 'eu-west-1')  # Default to eu-west-1
            self.sns_topic_arn = os.getenv('SNS_TOPIC_ARN','arn:aws:sns:eu-west-1:228281126655:wekan-card-reminders')
            
            # Validate required environment variables
            if not self.sns_topic_arn:
                raise ValueError("Missing required AWS environment variable: SNS_TOPIC_ARN")
            
            # Initialize SNS client using default credential chain
            # This will automatically use IAM roles, AWS CLI profile, or instance profile
            self.sns_client = boto3.client('sns', region_name=self.aws_region)
            
            logger.info(f"SNS client initialized for region: {self.aws_region}")
            logger.info("Using default AWS credential chain (IAM role/profile)")
            
        except Exception as e:
            logger.error(f"Failed to initialize SNS client: {str(e)}")
            raise
    
    def format_card_message(self, due_cards: List[Dict]) -> tuple[str, str]:
        """
        Format due cards into SNS message
        Args:
            due_cards: List of due card dictionaries
        Returns: Tuple of (subject, message)
        """
        try:
            if not due_cards:
                return "No Due Cards", "No cards are currently due."
            
            # Create subject
            card_count = len(due_cards)
            subject = f"🔔 Wekan Alert: {card_count} Card{'s' if card_count > 1 else ''} Due Soon"
            
            # Create message body
            message_lines = [
                f"Wekan Card Reminders - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"Total cards due within 1 hour: {card_count}",
                "",
                "📋 Due Cards Details:",
                "=" * 50
            ]
            
            for i, card in enumerate(due_cards, 1):
                # Calculate hours until due
                try:
                    due_date = card.get('dueAtParsed', datetime.now())
                    current_time = datetime.now()
                    hours_until_due = (due_date - current_time).total_seconds() / 3600
                except:
                    hours_until_due = 0
                
                # Determine urgency
                if hours_until_due < 0:
                    urgency = "⚠️ OVERDUE"
                elif hours_until_due < 0.5:
                    urgency = "🚨 URGENT (< 30 min)"
                elif hours_until_due < 1:
                    urgency = "⏰ SOON (< 1 hour)"
                else:
                    urgency = "📅 UPCOMING"
                
                card_info = [
                    f"{i}. {card.get('title', 'Untitled Card')} {urgency}",
                    f"   Board: {card.get('boardTitle', 'Unknown Board')}",
                    f"   List: {card.get('listTitle', 'Unknown List')}",
                    f"   Due: {due_date.strftime('%Y-%m-%d %H:%M:%S') if isinstance(due_date, datetime) else 'Unknown Date'}",
                    f"   Time until due: {hours_until_due:.1f} hours",
                ]
                
                # Add description if available
                description = card.get('description', '').strip()
                if description:
                    # Truncate long descriptions
                    if len(description) > 100:
                        description = description[:100] + "..."
                    card_info.append(f"   Description: {description}")
                
                message_lines.extend(card_info)
                message_lines.append("")  # Empty line between cards
            
            # Add footer
            message_lines.extend([
                "=" * 50,
                f"Please check your Wekan board: {os.getenv('WEKAN_URL', 'http://localhost:80')}",
                "",
                "This is an automated reminder from your Wekan Reminder Service."
            ])
            
            message = "\n".join(message_lines)
            return subject, message
            
        except Exception as e:
            logger.error(f"Error formatting card message: {str(e)}")
            return "Wekan Alert - Formatting Error", f"Error formatting reminder message: {str(e)}"
    
    def send_notification(self, due_cards: List[Dict]) -> bool:
        """
        Send SNS notification for due cards
        Args:
            due_cards: List of due card dictionaries
        Returns: True if successful, False otherwise
        """
        try:
            if not due_cards:
                logger.info("No due cards to notify about")
                return True
            
            logger.info(f"Preparing to send SNS notification for {len(due_cards)} due cards")
            
            # Format message
            subject, message = self.format_card_message(due_cards)
            
            # Send SNS message
            response = self.sns_client.publish(
                TopicArn=self.sns_topic_arn,
                Subject=subject,
                Message=message
            )
            
            # Check response
            if response.get('MessageId'):
                logger.info(f"✅ SNS notification sent successfully! MessageId: {response['MessageId']}")
                return True
            else:
                logger.error("❌ SNS notification failed - no MessageId in response")
                return False
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"❌ AWS SNS ClientError ({error_code}): {error_message}")
            
            # Provide specific guidance for common errors
            if error_code == 'NotFound':
                logger.error("SNS Topic not found. Please verify SNS_TOPIC_ARN in your .env file")
            elif error_code in ['InvalidParameter', 'AuthorizationError']:
                logger.error("Authentication failed. Please ensure AWS credentials are configured:")
                logger.error("- Set up AWS CLI: aws configure")
                logger.error("- Use IAM role (for EC2/ECS)")
                logger.error("- Set environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
            elif error_code == 'AccessDenied':
                logger.error("Access denied. Please ensure your AWS credentials have SNS publish permissions")
            
            return False
            
        except BotoCoreError as e:
            logger.error(f"❌ AWS BotoCoreError: {str(e)}")
            logger.error("This might be a network connectivity issue or AWS service problem")
            return False
            
        except Exception as e:
            logger.error(f"❌ Unexpected error sending SNS notification: {str(e)}")
            return False
    
    def test_connection(self) -> bool:
        """
        Test SNS connection and topic access
        Returns: True if connection successful, False otherwise
        """
        try:
            logger.info("Testing SNS connection...")
            
            # Try to get topic attributes
            response = self.sns_client.get_topic_attributes(
                TopicArn=self.sns_topic_arn
            )
            
            if response.get('Attributes'):
                topic_name = response['Attributes'].get('DisplayName', 'Unknown')
                logger.info(f"✅ SNS connection successful! Topic: {topic_name}")
                return True
            else:
                logger.error("❌ SNS topic found but no attributes returned")
                return False
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"❌ SNS connection test failed ({error_code}): {error_message}")
            return False
            
        except Exception as e:
            logger.error(f"❌ SNS connection test error: {str(e)}")
            return False
    
    def send_test_notification(self) -> bool:
        """
        Send a test notification to verify SNS setup
        Returns: True if successful, False otherwise
        """
        try:
            logger.info("Sending test SNS notification...")
            
            test_subject = "🧪 Wekan Reminder Service - Test Notification"
            test_message = f"""
Wekan Reminder Service Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

✅ SNS integration is working correctly!

This is a test notification to verify that your AWS SNS setup is configured properly.

Configuration Details:
- AWS Region: {self.aws_region}
- Topic ARN: {self.sns_topic_arn}
- Wekan URL: {os.getenv('WEKAN_URL', 'Not configured')}

If you received this message, your reminder service is ready to send real notifications when Wekan cards are due.

This is an automated test from your Wekan Reminder Service.
"""
            
            response = self.sns_client.publish(
                TopicArn=self.sns_topic_arn,
                Subject=test_subject,
                Message=test_message
            )
            
            if response.get('MessageId'):
                logger.info(f"✅ Test notification sent! MessageId: {response['MessageId']}")
                return True
            else:
                logger.error("❌ Test notification failed - no MessageId")
                return False
                
        except Exception as e:
            logger.error(f"❌ Test notification error: {str(e)}")
            return False