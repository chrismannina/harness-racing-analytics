import httpx
import asyncio
import time
from typing import List, Dict, Optional, Any
from bs4 import BeautifulSoup
from datetime import datetime, date
import logging
import re
from urllib.parse import urljoin, urlparse
import json

logger = logging.getLogger(__name__)

class RacingWebScraper:
    """Specialized web scraper for Ontario harness racing data"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        )
        self.rate_limit_delay = 2.0  # 2 seconds between requests
        self.last_request_time = 0
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def _rate_limit(self):
        """Implement rate limiting to be respectful to servers"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last)
        
        self.last_request_time = time.time()
    
    async def scrape_standardbred_canada_entries(self, track: str, race_date: date) -> List[Dict]:
        """Scrape race entries from Standardbred Canada"""
        await self._rate_limit()
        
        try:
            # Build URL for Standardbred Canada entries
            base_url = "https://standardbredcanada.ca/racing/entries"
            
            # Try different URL patterns
            date_str = race_date.strftime("%Y-%m-%d")
            
            # Method 1: Direct entries page
            response = await self.client.get(base_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for track and date selection forms
            track_options = soup.find_all('option')
            date_options = soup.find_all('option')
            
            # Extract available tracks and dates
            available_tracks = []
            available_dates = []
            
            for option in track_options:
                if option.get('value') and 'track' in option.get('value', '').lower():
                    available_tracks.append(option.text.strip())
            
            for option in date_options:
                if option.get('value') and re.match(r'\d{4}-\d{2}-\d{2}', option.get('value', '')):
                    available_dates.append(option.text.strip())
            
            logger.info(f"Found {len(available_tracks)} tracks and {len(available_dates)} dates")
            
            # Try to find race entries
            entries = []
            
            # Look for race cards or entry tables
            race_cards = soup.find_all(['div', 'table'], class_=re.compile(r'race|entry|card', re.I))
            
            for card in race_cards:
                entry_data = self._parse_standardbred_entry_card(card)
                if entry_data:
                    entries.extend(entry_data)
            
            return entries
            
        except Exception as e:
            logger.error(f"Error scraping Standardbred Canada entries: {e}")
            return []
    
    def _parse_standardbred_entry_card(self, card_element) -> List[Dict]:
        """Parse a race card element from Standardbred Canada"""
        entries = []
        
        try:
            # Look for race information
            race_info = {}
            
            # Try to find race number
            race_num_elem = card_element.find(text=re.compile(r'Race\s+\d+', re.I))
            if race_num_elem:
                race_match = re.search(r'Race\s+(\d+)', race_num_elem, re.I)
                if race_match:
                    race_info['race_number'] = int(race_match.group(1))
            
            # Try to find post time
            time_elem = card_element.find(text=re.compile(r'\d{1,2}:\d{2}\s*(AM|PM)?', re.I))
            if time_elem:
                race_info['post_time'] = time_elem.strip()
            
            # Look for entry rows in tables
            entry_rows = card_element.find_all('tr')
            
            for row in entry_rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 3:  # Minimum cells for meaningful data
                    entry = self._parse_entry_row(cells)
                    if entry:
                        entry.update(race_info)
                        entries.append(entry)
            
            # Alternative: Look for div-based entries
            if not entries:
                entry_divs = card_element.find_all('div', class_=re.compile(r'entry|horse', re.I))
                for div in entry_divs:
                    entry = self._parse_entry_div(div)
                    if entry:
                        entry.update(race_info)
                        entries.append(entry)
            
        except Exception as e:
            logger.error(f"Error parsing entry card: {e}")
        
        return entries
    
    def _parse_entry_row(self, cells) -> Optional[Dict]:
        """Parse a table row containing entry information"""
        try:
            entry = {}
            
            # Common patterns for entry data
            for i, cell in enumerate(cells):
                text = cell.get_text(strip=True)
                
                # Skip empty cells
                if not text or text in ['-', 'N/A', '']:
                    continue
                
                # Try to identify data types
                if re.match(r'^\d+$', text) and len(text) <= 2:
                    # Likely post position or program number
                    if 'post_position' not in entry:
                        entry['post_position'] = int(text)
                    elif 'program_number' not in entry:
                        entry['program_number'] = text
                
                elif re.match(r'^\d+-\d+$', text):
                    # Likely odds format
                    entry['morning_line_odds'] = text
                
                elif re.match(r'^[A-Za-z\s]+$', text) and len(text) > 2:
                    # Likely name
                    if 'horse_name' not in entry:
                        entry['horse_name'] = text
                    elif 'driver' not in entry:
                        entry['driver'] = text
                    elif 'trainer' not in entry:
                        entry['trainer'] = text
                
                elif re.match(r'^\d+[MFG]?$', text):
                    # Age and possibly sex
                    age_match = re.match(r'^(\d+)([MFG]?)$', text)
                    if age_match:
                        entry['age'] = int(age_match.group(1))
                        if age_match.group(2):
                            entry['sex'] = age_match.group(2)
            
            # Only return if we have minimum required data
            if 'horse_name' in entry and 'post_position' in entry:
                return entry
            
        except Exception as e:
            logger.error(f"Error parsing entry row: {e}")
        
        return None
    
    def _parse_entry_div(self, div_element) -> Optional[Dict]:
        """Parse a div element containing entry information"""
        try:
            entry = {}
            text = div_element.get_text(strip=True)
            
            # Try to extract structured data from text
            # This would need to be customized based on actual HTML structure
            
            # Look for horse name (often in strong/bold tags)
            horse_elem = div_element.find(['strong', 'b'])
            if horse_elem:
                entry['horse_name'] = horse_elem.get_text(strip=True)
            
            # Look for numbers that might be post positions
            numbers = re.findall(r'\b\d+\b', text)
            if numbers:
                entry['post_position'] = int(numbers[0])
            
            # Look for odds patterns
            odds_match = re.search(r'\b\d+-\d+\b', text)
            if odds_match:
                entry['morning_line_odds'] = odds_match.group()
            
            return entry if 'horse_name' in entry else None
            
        except Exception as e:
            logger.error(f"Error parsing entry div: {e}")
            return None
    
    async def scrape_woodbine_races(self, race_date: date) -> List[Dict]:
        """Scrape race data from Woodbine Mohawk Park"""
        await self._rate_limit()
        
        try:
            # Try different Woodbine URLs
            urls_to_try = [
                "https://woodbine.com/mohawk/racing/",
                "https://woodbine.com/mohawk/entries/",
                f"https://woodbine.com/mohawk/racing/{race_date.strftime('%Y-%m-%d')}"
            ]
            
            races = []
            
            for url in urls_to_try:
                try:
                    response = await self.client.get(url)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Look for race data
                    race_data = self._parse_woodbine_page(soup, race_date)
                    if race_data:
                        races.extend(race_data)
                        break  # Found data, no need to try other URLs
                        
                except Exception as e:
                    logger.warning(f"Failed to scrape {url}: {e}")
                    continue
            
            return races
            
        except Exception as e:
            logger.error(f"Error scraping Woodbine races: {e}")
            return []
    
    def _parse_woodbine_page(self, soup: BeautifulSoup, race_date: date) -> List[Dict]:
        """Parse Woodbine page for race data"""
        races = []
        
        try:
            # Look for JSON data in script tags
            script_tags = soup.find_all('script')
            for script in script_tags:
                if script.string and ('race' in script.string.lower() or 'entry' in script.string.lower()):
                    try:
                        # Try to extract JSON data
                        json_match = re.search(r'(\{.*\})', script.string)
                        if json_match:
                            data = json.loads(json_match.group(1))
                            if isinstance(data, dict) and 'races' in data:
                                races.extend(data['races'])
                    except:
                        continue
            
            # If no JSON found, try HTML parsing
            if not races:
                race_elements = soup.find_all(['div', 'section'], class_=re.compile(r'race', re.I))
                for elem in race_elements:
                    race_data = self._parse_woodbine_race_element(elem)
                    if race_data:
                        races.append(race_data)
            
        except Exception as e:
            logger.error(f"Error parsing Woodbine page: {e}")
        
        return races
    
    def _parse_woodbine_race_element(self, element) -> Optional[Dict]:
        """Parse a race element from Woodbine"""
        try:
            race = {}
            
            # Extract race number
            race_num_elem = element.find(text=re.compile(r'Race\s+\d+', re.I))
            if race_num_elem:
                race_match = re.search(r'Race\s+(\d+)', race_num_elem, re.I)
                if race_match:
                    race['race_number'] = int(race_match.group(1))
            
            # Extract post time
            time_elem = element.find(text=re.compile(r'\d{1,2}:\d{2}\s*(AM|PM)', re.I))
            if time_elem:
                race['post_time'] = time_elem.strip()
            
            # Extract entries
            entries = []
            entry_elements = element.find_all(['tr', 'div'], class_=re.compile(r'entry|horse', re.I))
            
            for entry_elem in entry_elements:
                entry_data = self._parse_woodbine_entry(entry_elem)
                if entry_data:
                    entries.append(entry_data)
            
            if entries:
                race['entries'] = entries
            
            return race if 'race_number' in race else None
            
        except Exception as e:
            logger.error(f"Error parsing Woodbine race element: {e}")
            return None
    
    def _parse_woodbine_entry(self, element) -> Optional[Dict]:
        """Parse an entry element from Woodbine"""
        try:
            entry = {}
            text = element.get_text(strip=True)
            
            # Similar parsing logic as Standardbred Canada
            # This would need to be customized based on Woodbine's actual HTML structure
            
            return entry if entry else None
            
        except Exception as e:
            logger.error(f"Error parsing Woodbine entry: {e}")
            return None
    
    async def scrape_live_odds(self, track_url: str) -> Dict[str, Any]:
        """Scrape live odds from track websites"""
        await self._rate_limit()
        
        try:
            response = await self.client.get(track_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            odds_data = {}
            
            # Look for odds tables or elements
            odds_elements = soup.find_all(['table', 'div'], class_=re.compile(r'odd|bet|wager', re.I))
            
            for elem in odds_elements:
                parsed_odds = self._parse_odds_element(elem)
                if parsed_odds:
                    odds_data.update(parsed_odds)
            
            return odds_data
            
        except Exception as e:
            logger.error(f"Error scraping live odds: {e}")
            return {}
    
    def _parse_odds_element(self, element) -> Dict[str, Any]:
        """Parse odds from an HTML element"""
        odds = {}
        
        try:
            # Look for odds patterns in text
            text = element.get_text()
            
            # Find odds patterns like "3-1", "5/2", "2.50"
            odds_patterns = re.findall(r'\b\d+[-/]\d+\b|\b\d+\.\d+\b', text)
            
            # Find horse names (this would need refinement)
            horse_names = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
            
            # Pair odds with horses if possible
            if len(odds_patterns) == len(horse_names):
                for horse, odd in zip(horse_names, odds_patterns):
                    odds[horse] = odd
            
        except Exception as e:
            logger.error(f"Error parsing odds element: {e}")
        
        return odds
    
    async def test_scraping_capabilities(self) -> Dict[str, Any]:
        """Test scraping capabilities against various Ontario racing sites"""
        results = {
            'standardbred_canada': {'status': 'untested', 'data': []},
            'woodbine_mohawk': {'status': 'untested', 'data': []},
            'live_odds': {'status': 'untested', 'data': {}}
        }
        
        # Test Standardbred Canada
        try:
            sc_data = await self.scrape_standardbred_canada_entries("Woodbine Mohawk Park", date.today())
            results['standardbred_canada'] = {
                'status': 'success' if sc_data else 'no_data',
                'data': sc_data,
                'count': len(sc_data)
            }
        except Exception as e:
            results['standardbred_canada'] = {'status': 'error', 'error': str(e)}
        
        # Test Woodbine
        try:
            wb_data = await self.scrape_woodbine_races(date.today())
            results['woodbine_mohawk'] = {
                'status': 'success' if wb_data else 'no_data',
                'data': wb_data,
                'count': len(wb_data)
            }
        except Exception as e:
            results['woodbine_mohawk'] = {'status': 'error', 'error': str(e)}
        
        # Test live odds
        try:
            odds_data = await self.scrape_live_odds("https://woodbine.com/mohawk")
            results['live_odds'] = {
                'status': 'success' if odds_data else 'no_data',
                'data': odds_data,
                'count': len(odds_data)
            }
        except Exception as e:
            results['live_odds'] = {'status': 'error', 'error': str(e)}
        
        return results

# Convenience functions
async def test_ontario_scraping():
    """Test scraping capabilities for Ontario racing data"""
    async with RacingWebScraper() as scraper:
        return await scraper.test_scraping_capabilities()

async def get_standardbred_entries(track: str, race_date: date):
    """Get entries from Standardbred Canada"""
    async with RacingWebScraper() as scraper:
        return await scraper.scrape_standardbred_canada_entries(track, race_date)

async def get_woodbine_races(race_date: date):
    """Get races from Woodbine"""
    async with RacingWebScraper() as scraper:
        return await scraper.scrape_woodbine_races(race_date) 