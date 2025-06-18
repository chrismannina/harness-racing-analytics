import httpx
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import logging
import json
import re
from dataclasses import dataclass
import time
from urllib.parse import urljoin, parse_qs, urlparse

logger = logging.getLogger(__name__)

@dataclass
class RaceEntry:
    """Data structure for a race entry"""
    horse_name: str
    driver: str
    trainer: str
    post_position: int
    morning_line_odds: str
    program_number: str
    age: int
    sex: str
    sire: str = ""
    dam: str = ""
    owner: str = ""
    earnings: float = 0.0
    starts: int = 0
    wins: int = 0
    places: int = 0
    shows: int = 0
    last_race_date: Optional[date] = None
    last_race_finish: Optional[int] = None

@dataclass
class Race:
    """Data structure for a race"""
    race_number: int
    track: str
    date: date
    post_time: str
    distance: str
    surface: str
    race_type: str
    purse: float
    conditions: str
    entries: List[RaceEntry]
    weather: str = ""
    track_condition: str = ""

@dataclass
class RaceResult:
    """Data structure for race results"""
    race_number: int
    track: str
    date: date
    winner: str
    winning_time: str
    payouts: Dict[str, float]
    finishing_order: List[str]
    scratches: List[str] = None

@dataclass
class HorseInfo:
    name: str
    registration_number: str
    foaling_year: int
    sire: str
    dam: str
    sex: str
    color: str

class OntarioRacingDataService:
    """Comprehensive Ontario harness racing data service"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        )
        self.base_urls = {
            'standardbred_canada': 'https://standardbredcanada.ca',
            'woodbine_mohawk': 'https://woodbine.com/mohawk',
            'odds_api': 'https://api.the-odds-api.com/v4',
            'racing_api': 'https://theracingapi.com/v1'
        }
        
        # Cache for avoiding repeated requests
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self._cache:
            return False
        return time.time() - self._cache[key]['timestamp'] < self._cache_ttl

    def _get_from_cache(self, key: str) -> Any:
        """Get data from cache"""
        if self._is_cache_valid(key):
            return self._cache[key]['data']
        return None

    def _set_cache(self, key: str, data: Any):
        """Set data in cache"""
        self._cache[key] = {
            'data': data,
            'timestamp': time.time()
        }

    async def get_todays_races(self) -> List[Race]:
        """Get today's races from all Ontario tracks"""
        cache_key = f"todays_races_{date.today()}"
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached

        races = []
        
        # Get races from multiple sources
        try:
            # Primary source: Standardbred Canada
            sc_races = await self._get_standardbred_canada_races(date.today())
            races.extend(sc_races)
            
            # Secondary source: Woodbine Mohawk
            woodbine_races = await self._get_woodbine_races(date.today())
            races.extend(woodbine_races)
            
            # Remove duplicates based on track and race number
            unique_races = self._deduplicate_races(races)
            
            self._set_cache(cache_key, unique_races)
            return unique_races
            
        except Exception as e:
            logger.error(f"Error getting today's races: {e}")
            return []

    async def get_future_races(self, days_ahead: int = 7) -> List[Race]:
        """Get future races for the next N days"""
        all_races = []
        
        for i in range(1, days_ahead + 1):
            future_date = date.today() + timedelta(days=i)
            races = await self._get_races_for_date(future_date)
            all_races.extend(races)
        
        return all_races

    async def get_live_odds(self, track: str = "woodbine") -> Dict[str, Any]:
        """Get live odds data"""
        try:
            # Try The Odds API first (if API key available)
            odds_data = await self._get_odds_api_data()
            if odds_data:
                return odds_data
            
            # Fallback to scraping
            return await self._scrape_live_odds(track)
            
        except Exception as e:
            logger.error(f"Error getting live odds: {e}")
            return {}

    async def get_race_results(self, track: str, race_date: date) -> List[RaceResult]:
        """Get race results for a specific track and date"""
        cache_key = f"results_{track}_{race_date}"
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached

        try:
            results = await self._get_standardbred_canada_results(track, race_date)
            self._set_cache(cache_key, results)
            return results
        except Exception as e:
            logger.error(f"Error getting race results: {e}")
            return []

    async def get_horse_statistics(self, horse_name: str) -> Dict[str, Any]:
        """Get comprehensive horse statistics"""
        try:
            return await self._get_standardbred_canada_horse_stats(horse_name)
        except Exception as e:
            logger.error(f"Error getting horse statistics: {e}")
            return {}

    async def get_driver_statistics(self, driver_name: str) -> Dict[str, Any]:
        """Get driver performance statistics"""
        try:
            return await self._get_standardbred_canada_driver_stats(driver_name)
        except Exception as e:
            logger.error(f"Error getting driver statistics: {e}")
            return {}

    async def get_trainer_statistics(self, trainer_name: str) -> Dict[str, Any]:
        """Get trainer performance statistics"""
        try:
            return await self._get_standardbred_canada_trainer_stats(trainer_name)
        except Exception as e:
            logger.error(f"Error getting trainer statistics: {e}")
            return {}

    async def get_available_tracks(self) -> List[Dict[str, str]]:
        """Get list of available tracks from Standardbred Canada"""
        try:
            url = f"{self.base_urls['standardbred_canada']}/racing"
            response = await self.client.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            tracks = []
            
            # Find track selection dropdown
            track_select = soup.find('select', {'name': 'entries_track'})
            if track_select:
                options = track_select.find_all('option')
                for option in options:
                    value = option.get('value', '')
                    text = option.get_text(strip=True)
                    
                    # Filter for Ontario tracks
                    ontario_tracks = ['GEODF', 'GRVRF', 'WBSBS', 'HNVR', 'SAR F', 'KD F', 'CLNTN', 'DRES']
                    if value in ontario_tracks:
                        tracks.append({
                            'code': value,
                            'name': text,
                            'province': 'Ontario'
                        })
            
            return tracks
            
        except Exception as e:
            logger.error(f"Error getting available tracks: {e}")
            return []

    async def get_track_racing_dates(self, track_code: str) -> List[str]:
        """Get racing dates for a specific track"""
        try:
            url = f"{self.base_urls['standardbred_canada']}/racing/racedates"
            response = await self.client.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for date information
            dates = []
            date_elements = soup.find_all(text=re.compile(r'\d{4}-\d{2}-\d{2}'))
            
            for date_text in date_elements:
                date_match = re.search(r'\d{4}-\d{2}-\d{2}', date_text)
                if date_match:
                    dates.append(date_match.group())
            
            return list(set(dates))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error getting racing dates: {e}")
            return []

    # Private methods for data sources

    async def _get_standardbred_canada_races(self, race_date: date) -> List[Race]:
        """Scrape races from Standardbred Canada"""
        races = []
        
        try:
            # Get entries for Ontario tracks
            ontario_tracks = [
                'Woodbine Mohawk Park',
                'Georgian Downs', 
                'Grand River Raceway',
                'Hanover Raceway',
                'Hiawatha Horse Park'
            ]
            
            for track in ontario_tracks:
                track_races = await self._scrape_sc_track_entries(track, race_date)
                races.extend(track_races)
            
            return races
            
        except Exception as e:
            logger.error(f"Error scraping Standardbred Canada: {e}")
            return []

    async def _scrape_sc_track_entries(self, track: str, race_date: date) -> List[Race]:
        """Scrape entries for a specific track from Standardbred Canada"""
        races = []
        
        try:
            # Format date for URL
            date_str = race_date.strftime("%Y-%m-%d")
            
            # Build URL - using the correct Standardbred Canada URL structure
            url = f"{self.base_urls['standardbred_canada']}/racing"
            
            response = await self.client.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Parse the HTML to extract race data
            # Look for race cards or entry tables
            race_elements = soup.find_all(['div', 'table'], class_=re.compile(r'race|entry|card', re.I))
            
            for race_elem in race_elements:
                race = self._parse_sc_race_element(race_elem, track, race_date)
                if race:
                    races.append(race)
            
            return races
            
        except Exception as e:
            logger.error(f"Error scraping {track} entries: {e}")
            return []

    async def _get_woodbine_races(self, race_date: date) -> List[Race]:
        """Get races from Woodbine Mohawk Park"""
        races = []
        
        try:
            # Woodbine API endpoint (if available) or scraping
            url = f"{self.base_urls['woodbine_mohawk']}/race/"
            
            response = await self.client.get(url)
            
            # Try to parse JSON first (if API available)
            try:
                data = response.json()
                races = self._parse_woodbine_json(data, race_date)
            except:
                # Fallback to HTML parsing
                soup = BeautifulSoup(response.text, 'html.parser')
                races = self._parse_woodbine_html(soup, race_date)
            
            return races
            
        except Exception as e:
            logger.error(f"Error getting Woodbine races: {e}")
            return []

    async def _get_odds_api_data(self) -> Dict[str, Any]:
        """Get odds from The Odds API"""
        try:
            # This would require an API key
            api_key = "YOUR_ODDS_API_KEY"  # Would be in environment variables
            if not api_key or api_key == "YOUR_ODDS_API_KEY":
                return {}
            
            url = f"{self.base_urls['odds_api']}/sports/horseracing/odds"
            params = {
                'apiKey': api_key,
                'regions': 'us,uk,au',  # Adjust based on available regions
                'markets': 'h2h,spreads',
                'oddsFormat': 'decimal'
            }
            
            response = await self.client.get(url, params=params)
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting odds API data: {e}")
            return {}

    async def _scrape_live_odds(self, track: str) -> Dict[str, Any]:
        """Scrape live odds from track websites"""
        try:
            if track.lower() == "woodbine":
                url = f"{self.base_urls['woodbine_mohawk']}/race/"
                response = await self.client.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Parse odds from HTML
                odds_data = {}
                odds_elements = soup.find_all('div', class_='odds')
                
                for elem in odds_elements:
                    # Parse odds data - placeholder implementation
                    pass
                
                return odds_data
            
            return {}
            
        except Exception as e:
            logger.error(f"Error scraping live odds: {e}")
            return {}

    async def _get_standardbred_canada_results(self, track: str, race_date: date) -> List[RaceResult]:
        """Get race results from Standardbred Canada"""
        results = []
        
        try:
            # Use the correct results URL structure
            url = f"{self.base_urls['standardbred_canada']}/racing"
            
            # Add query parameters for results tab
            params = {
                'active_tab': 'results'
            }
            
            response = await self.client.get(url, params=params)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Parse results - look for results tables or cards
            result_elements = soup.find_all(['div', 'table'], class_=re.compile(r'result|race', re.I))
            
            for result_elem in result_elements:
                result = self._parse_sc_result_element(result_elem, track, race_date)
                if result:
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting SC results: {e}")
            return []

    async def _get_standardbred_canada_horse_stats(self, horse_name: str) -> Dict[str, Any]:
        """Get horse statistics from Standardbred Canada"""
        try:
            # Search for horse
            search_url = f"{self.base_urls['standardbred_canada']}/search"
            params = {'q': horse_name, 'type': 'horse'}
            
            response = await self.client.get(search_url, params=params)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Parse horse statistics
            stats = {
                'name': horse_name,
                'starts': 0,
                'wins': 0,
                'places': 0,
                'shows': 0,
                'earnings': 0.0,
                'best_time': '',
                'recent_races': []
            }
            
            # Extract stats from HTML - placeholder implementation
            stats_elem = soup.find('div', class_='horse-stats')
            if stats_elem:
                # Parse stats
                pass
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting horse stats: {e}")
            return {}

    async def _get_standardbred_canada_driver_stats(self, driver_name: str) -> Dict[str, Any]:
        """Get driver statistics from Standardbred Canada"""
        try:
            search_url = f"{self.base_urls['standardbred_canada']}/search"
            params = {'q': driver_name, 'type': 'driver'}
            
            response = await self.client.get(search_url, params=params)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            stats = {
                'name': driver_name,
                'starts': 0,
                'wins': 0,
                'win_percentage': 0.0,
                'earnings': 0.0,
                'recent_drives': []
            }
            
            # Parse driver stats from HTML
            return stats
            
        except Exception as e:
            logger.error(f"Error getting driver stats: {e}")
            return {}

    async def _get_standardbred_canada_trainer_stats(self, trainer_name: str) -> Dict[str, Any]:
        """Get trainer statistics from Standardbred Canada"""
        try:
            search_url = f"{self.base_urls['standardbred_canada']}/search"
            params = {'q': trainer_name, 'type': 'trainer'}
            
            response = await self.client.get(search_url, params=params)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            stats = {
                'name': trainer_name,
                'starts': 0,
                'wins': 0,
                'win_percentage': 0.0,
                'earnings': 0.0,
                'horses_trained': []
            }
            
            # Parse trainer stats from HTML
            return stats
            
        except Exception as e:
            logger.error(f"Error getting trainer stats: {e}")
            return {}

    async def _get_races_for_date(self, race_date: date) -> List[Race]:
        """Get races for a specific date"""
        races = []
        
        try:
            # Get from Standardbred Canada
            sc_races = await self._get_standardbred_canada_races(race_date)
            races.extend(sc_races)
            
            # Get from Woodbine if it's a racing day
            if race_date.weekday() in [0, 3, 4, 5]:  # Mon, Thu, Fri, Sat
                woodbine_races = await self._get_woodbine_races(race_date)
                races.extend(woodbine_races)
            
            return self._deduplicate_races(races)
            
        except Exception as e:
            logger.error(f"Error getting races for {race_date}: {e}")
            return []

    def _deduplicate_races(self, races: List[Race]) -> List[Race]:
        """Remove duplicate races based on track, date, and race number"""
        seen = set()
        unique_races = []
        
        for race in races:
            key = (race.track, race.date, race.race_number)
            if key not in seen:
                seen.add(key)
                unique_races.append(race)
        
        return unique_races

    def _parse_sc_race_element(self, elem, track: str, race_date: date) -> Optional[Race]:
        """Parse a race element from Standardbred Canada HTML"""
        try:
            # This is a placeholder - actual implementation would depend on HTML structure
            race_number = 1
            post_time = "7:00 PM"
            distance = "1 Mile"
            surface = "Fast"
            race_type = "Pace"
            purse = 15000.0
            conditions = "Open Pace"
            entries = []
            
            return Race(
                race_number=race_number,
                track=track,
                date=race_date,
                post_time=post_time,
                distance=distance,
                surface=surface,
                race_type=race_type,
                purse=purse,
                conditions=conditions,
                entries=entries
            )
        except Exception as e:
            logger.error(f"Error parsing SC race element: {e}")
            return None

    def _parse_woodbine_json(self, data: Dict, race_date: date) -> List[Race]:
        """Parse Woodbine JSON data"""
        races = []
        
        try:
            # Parse JSON structure - placeholder implementation
            if 'races' in data:
                for race_data in data['races']:
                    race = Race(
                        race_number=race_data.get('raceNumber', 1),
                        track="Woodbine Mohawk Park",
                        date=race_date,
                        post_time=race_data.get('postTime', ''),
                        distance=race_data.get('distance', ''),
                        surface=race_data.get('surface', ''),
                        race_type=race_data.get('raceType', ''),
                        purse=race_data.get('purse', 0.0),
                        conditions=race_data.get('conditions', ''),
                        entries=[]
                    )
                    races.append(race)
            
            return races
            
        except Exception as e:
            logger.error(f"Error parsing Woodbine JSON: {e}")
            return []

    def _parse_woodbine_html(self, soup: BeautifulSoup, race_date: date) -> List[Race]:
        """Parse Woodbine HTML data"""
        races = []
        
        try:
            # Parse HTML structure - placeholder implementation
            race_elements = soup.find_all('div', class_='race')
            
            for elem in race_elements:
                # Extract race data from HTML
                race = Race(
                    race_number=1,
                    track="Woodbine Mohawk Park",
                    date=race_date,
                    post_time="",
                    distance="",
                    surface="",
                    race_type="",
                    purse=0.0,
                    conditions="",
                    entries=[]
                )
                races.append(race)
            
            return races
            
        except Exception as e:
            logger.error(f"Error parsing Woodbine HTML: {e}")
            return []

    def _parse_sc_result_element(self, elem, track: str, race_date: date) -> Optional[RaceResult]:
        """Parse a result element from Standardbred Canada HTML"""
        try:
            # Placeholder implementation
            result = RaceResult(
                race_number=1,
                track=track,
                date=race_date,
                winner="",
                winning_time="",
                payouts={},
                finishing_order=[],
                scratches=[]
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing SC result element: {e}")
            return None

# Convenience functions for easy integration

async def get_ontario_races_today() -> List[Race]:
    """Get today's Ontario harness races"""
    async with OntarioRacingDataService() as service:
        return await service.get_todays_races()

async def get_ontario_future_races(days: int = 7) -> List[Race]:
    """Get future Ontario harness races"""
    async with OntarioRacingDataService() as service:
        return await service.get_future_races(days)

async def get_live_ontario_odds() -> Dict[str, Any]:
    """Get live odds for Ontario tracks"""
    async with OntarioRacingDataService() as service:
        return await service.get_live_odds()

async def get_ontario_race_results(track: str, date: date) -> List[RaceResult]:
    """Get race results for Ontario track"""
    async with OntarioRacingDataService() as service:
        return await service.get_race_results(track, date)

async def search_horse_stats(horse_name: str) -> Dict[str, Any]:
    """Search for horse statistics"""
    async with OntarioRacingDataService() as service:
        return await service.get_horse_statistics(horse_name)

async def search_driver_stats(driver_name: str) -> Dict[str, Any]:
    """Search for driver statistics"""
    async with OntarioRacingDataService() as service:
        return await service.get_driver_statistics(driver_name)

async def search_trainer_stats(trainer_name: str) -> Dict[str, Any]:
    """Search for trainer statistics"""
    async with OntarioRacingDataService() as service:
        return await service.get_trainer_statistics(trainer_name) 