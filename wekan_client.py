"""
Wekan API Client Module
Handles authentication and communication with Wekan API
"""

import os
import requests
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
import pytz

logger = logging.getLogger(__name__)

class WekanClient:
    """Client for interacting with Wekan API"""
    
    def __init__(self):
        """Initialize Wekan client with configuration from environment variables"""
        self.base_url = os.getenv('WEKAN_URL', 'http://localhost:80')
        self.username = os.getenv('WEKAN_USER',"rabeeaFaraj")
        self.password = os.getenv('WEKAN_PASSWORD',"123456789")
        self.token = None
        self.user_id = None
        
        if not all([self.username, self.password]):
            raise ValueError("WEKAN_USER and WEKAN_PASSWORD must be set in environment variables")
    
    def login(self) -> bool:
        """
        Authenticate with Wekan API and store token
        Returns: True if login successful, False otherwise
        """
        try:
            login_url = f"{self.base_url}/users/login"
            login_data = {
                "username": self.username,
                "password": self.password
            }
            
            logger.info(f"Attempting to login to Wekan at {login_url}")
            response = requests.post(login_url, json=login_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('token')
                self.user_id = data.get('id')
                logger.info("Successfully logged in to Wekan")
                return True
            else:
                logger.error(f"Login failed with status code: {response.status_code}")
                try:
                    error_data = response.json()
                    logger.error(f"Error details: {error_data}")
                except:
                    logger.error(f"Response text: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Login request failed: {str(e)}")
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """Get authorization headers for API requests"""
        if not self.token:
            raise ValueError("Not authenticated. Call login() first.")
        
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def get_boards(self) -> List[Dict]:
        """
        Fetch all boards accessible to the user
        Returns: List of board dictionaries
        """
        try:
            if not self.token and not self.login():
                return []
            
            boards_url = f"{self.base_url}/api/users/{self.user_id}/boards"
            response = requests.get(boards_url, headers=self.get_headers(), timeout=10)
            
            if response.status_code == 200:
                boards = response.json()
                logger.info(f"Retrieved {len(boards)} boards")
                return boards
            else:
                logger.error(f"Failed to fetch boards: {response.status_code}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching boards: {str(e)}")
            return []
    
    def get_cards_from_board(self, board_id: str) -> List[Dict]:
        """
        Fetch all cards from a specific board
        Args:
            board_id: The ID of the board
        Returns: List of card dictionaries
        """
        try:
            # First get all lists in the board
            lists_url = f"{self.base_url}/api/boards/{board_id}/lists"
            response = requests.get(lists_url, headers=self.get_headers(), timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch lists for board {board_id}: {response.status_code}")
                return []
            
            lists = response.json()
            all_cards = []
            
            # Get cards from each list
            for list_item in lists:
                list_id = list_item.get('_id')
                cards_url = f"{self.base_url}/api/boards/{board_id}/lists/{list_id}/cards"
                
                cards_response = requests.get(cards_url, headers=self.get_headers(), timeout=10)
                if cards_response.status_code == 200:
                    cards = cards_response.json()
                    # Add board and list context to each card
                    for card in cards:
                        card['boardId'] = board_id
                        card['listId'] = list_id
                        card['listTitle'] = list_item.get('title', 'Unknown List')
                    all_cards.extend(cards)
                else:
                    logger.warning(f"Failed to fetch cards for list {list_id}: {cards_response.status_code}")
            
            logger.info(f"Retrieved {len(all_cards)} cards from board {board_id}")
            return all_cards
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching cards from board {board_id}: {str(e)}")
            return []
    
    def get_due_cards(self, hours_ahead: int = 1) -> List[Dict]:
        """
        Get cards that are due within the specified number of hours
        Args:
            hours_ahead: Number of hours to look ahead for due cards
        Returns: List of due cards
        """
        try:
            # Get current time in local timezone (IDT)
            local_tz = pytz.timezone('Asia/Jerusalem')  # IDT timezone
            now_utc = datetime.now(timezone.utc)
            now_local = now_utc.astimezone(local_tz)
            threshold_local = now_local + timedelta(hours=hours_ahead)
            
            # Convert to naive datetime for comparison (but keep timezone info for logging)
            now = now_local.replace(tzinfo=None)
            threshold = threshold_local.replace(tzinfo=None)
            
            logger.info(f"Looking for cards due between now and {threshold} (local time)")
            
            due_cards = []
            boards = self.get_boards()
            
            if not boards:
                logger.warning("No boards found")
                return []
            
            logger.info(f"Retrieved {len(boards)} boards")
            
            for board in boards:
                board_id = board.get('_id')
                board_title = board.get('title', 'Unknown Board')
                
                logger.info(f"Checking board: {board_title} (ID: {board_id})")
                
                # Get cards from this board
                cards = self.get_cards_from_board(board_id)
                
                logger.info(f"Found {len(cards)} total cards in board {board_title}")
                
                for card in cards:
                    card_title = card.get('title', 'Untitled')
                    due_at = card.get('dueAt')
                    
                    logger.info(f"Checking card: '{card_title}' - dueAt: {due_at}")
                    
                    if due_at:
                        try:
                            # Parse the due date (Wekan stores dates in ISO format, usually UTC)
                            logger.info(f"Parsing due date: '{due_at}' for card '{card_title}'")
                            
                            # Parse as UTC and convert to local timezone
                            due_date_utc = datetime.fromisoformat(due_at.replace('Z', '+00:00'))
                            due_date_local = due_date_utc.astimezone(local_tz)
                            due_date = due_date_local.replace(tzinfo=None)  # Remove timezone for comparison
                            
                            logger.info(f"Parsed due date: {due_date} (local), Current time: {now} (local), Threshold: {threshold} (local)")
                            
                            # Check if card is due within the specified timeframe
                            if now <= due_date <= threshold:
                                card['boardTitle'] = board_title
                                card['dueAtParsed'] = due_date  # Add parsed due date for email formatting
                                due_cards.append(card)
                                logger.info(f"✅ Card '{card_title}' is due within {hours_ahead} hour(s)!")
                            else:
                                logger.info(f"❌ Card '{card_title}' not in time range. Due: {due_date} (local)")
                        except Exception as e:
                            logger.error(f"Error parsing due date for card '{card_title}': {str(e)}")
                    else:
                        logger.info(f"Card '{card_title}' has no due date")
            
            logger.info(f"Found {len(due_cards)} cards due within {hours_ahead} hour(s)")
            return due_cards
            
        except Exception as e:
            logger.error(f"Error getting due cards: {str(e)}")
            return []
    
    def test_connection(self) -> bool:
        """
        Test the connection to Wekan API
        Returns: True if connection successful, False otherwise
        """
        try:
            # Try to access the root API endpoint
            test_url = f"{self.base_url}/api/version"
            response = requests.get(test_url, timeout=10)
            
            if response.status_code == 200:
                logger.info("Wekan API connection test successful")
                return True
            else:
                logger.error(f"Wekan API connection test failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Wekan API connection test failed: {str(e)}")
            return False