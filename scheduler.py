"""
Scheduler Module
Manages automatic reminder checks using APScheduler
"""

import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from wekan_client import WekanClient
from sns_notifier import SNSNotifier

logger = logging.getLogger(__name__)

class ReminderScheduler:
    """Manages scheduled reminder checks"""
    
    def __init__(self):
        """Initialize the scheduler with configuration"""
        self.scheduler = BackgroundScheduler()
        self.wekan_client = WekanClient()
        self.sns_notifier = SNSNotifier()
        self.interval_minutes = int(os.getenv('SCHEDULER_INTERVAL_MINUTES', 60))
        self.is_running = False
        
        logger.info(f"Scheduler initialized with {self.interval_minutes} minute interval")
    
    def check_and_send_reminders(self):
        """
        Main job function: Check for due cards and send reminders
        This function is called by the scheduler
        """
        try:
            logger.info("Starting scheduled reminder check")
            start_time = datetime.now()
            
            # Get due cards from Wekan
            due_cards = self.wekan_client.get_due_cards(hours_ahead=1)
            
            if due_cards:
                logger.info(f"Found {len(due_cards)} due cards, sending SNS notification")
                
                # Send SNS notification with due cards
                success = self.sns_notifier.send_notification(due_cards)
                
                if success:
                    logger.info("SNS notification sent successfully")
                else:
                    logger.error("Failed to send SNS notification")
            else:
                logger.info("No due cards found, no notification needed")
            
            # Log execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Reminder check completed in {execution_time:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Error during scheduled reminder check: {str(e)}")
    
    def start(self):
        """Start the scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        try:
            # Add the job to the scheduler
            self.scheduler.add_job(
                func=self.check_and_send_reminders,
                trigger=IntervalTrigger(minutes=self.interval_minutes),
                id='reminder_check',
                name='Check for due cards and send reminders',
                replace_existing=True
            )
            
            # Start the scheduler
            self.scheduler.start()
            self.is_running = True
            
            logger.info(f"Scheduler started successfully - checking every {self.interval_minutes} minutes")
            
            # Run initial check immediately
            logger.info("Running initial reminder check")
            self.check_and_send_reminders()
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {str(e)}")
            raise
    
    def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return
        
        try:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Scheduler stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping scheduler: {str(e)}")
    
    def get_status(self) -> dict:
        """
        Get scheduler status information
        Returns: Dictionary with scheduler status
        """
        try:
            jobs = self.scheduler.get_jobs() if self.is_running else []
            next_run = None
            
            if jobs:
                next_run = jobs[0].next_run_time
            
            return {
                "running": self.is_running,
                "interval_minutes": self.interval_minutes,
                "next_run": next_run.isoformat() if next_run else None,
                "jobs_count": len(jobs)
            }
            
        except Exception as e:
            logger.error(f"Error getting scheduler status: {str(e)}")
            return {
                "running": False,
                "error": str(e)
            }
    
    def run_manual_check(self) -> dict:
        """
        Manually trigger a reminder check (for testing/debugging)
        Returns: Dictionary with check results
        """
        try:
            logger.info("Manual reminder check triggered")
            start_time = datetime.now()
            
            # Get due cards
            due_cards = self.wekan_client.get_due_cards(hours_ahead=1)
            
            result = {
                "timestamp": start_time.isoformat(),
                "due_cards_count": len(due_cards),
                "due_cards": [],
                "notification_sent": False,
                "success": True
            }
            
            # Add card summaries to result
            for card in due_cards:
                result["due_cards"].append({
                    "title": card.get('title'),
                    "board": card.get('boardTitle'),
                    "list": card.get('listTitle'),
                    "due_at": card.get('dueAtParsed').isoformat() if card.get('dueAtParsed') else None,
                    "hours_until_due": card.get('hoursUntilDue')
                })
            
            # Send SNS notification if there are due cards
            if due_cards:
                notification_success = self.sns_notifier.send_notification(due_cards)
                result["notification_sent"] = notification_success
                
                if not notification_success:
                    result["success"] = False
                    result["error"] = "Failed to send SNS notification"
            
            execution_time = (datetime.now() - start_time).total_seconds()
            result["execution_time_seconds"] = execution_time
            
            logger.info(f"Manual check completed: {len(due_cards)} due cards, notification sent: {result['notification_sent']}")
            return result
            
        except Exception as e:
            logger.error(f"Error during manual reminder check: {str(e)}")
            return {
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e)
            }