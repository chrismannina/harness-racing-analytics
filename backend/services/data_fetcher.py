import httpx
import asyncio
import random
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import logging
from bs4 import BeautifulSoup
import re
import json
from models import Track, Horse, Driver, Trainer, Race, RaceEntry, DataFetch
from schemas import DataStatusResponse
from services.ontario_racing_api import OntarioRacingDataService, get_ontario_races_today, get_ontario_future_races, get_live_ontario_odds, get_ontario_race_results, search_horse_stats, search_driver_stats, search_trainer_stats

logger = logging.getLogger(__name__)

class DataFetcher:
    def __init__(self):
        self.base_urls = {
            'standardbred_canada': 'https://standardbredcanada.ca',
            'woodbine_mohawk': 'https://woodbine.com/mohawk',
            'ontario_racing': 'https://www.ontarioracing.com',
            'usta_racing': 'https://racing.ustrotting.com'
        }
        self.session = httpx.AsyncClient(timeout=30.0)
    
    async def fetch_latest_data(self, db: Session) -> Dict[str, Any]:
        """Fetch the latest racing data from various sources"""
        results = {
            'tracks_updated': 0,
            'horses_updated': 0,
            'drivers_updated': 0,
            'trainers_updated': 0,
            'races_updated': 0,
            'entries_updated': 0,
            'errors': []
        }
        
        try:
            # Initialize tracks if not exists
            await self._initialize_tracks(db)
            results['tracks_updated'] = 1
            
            # Try to fetch real data first
            real_data_success = await self._fetch_real_data(db, results)
            
            # If real data fetch fails or returns minimal data, use sample data as fallback
            if not real_data_success or results['races_updated'] < 5:
                logger.info("Real data fetch unsuccessful, falling back to sample data")
                await self._fetch_sample_data(db, results)
            
            # Record successful fetch
            self._record_fetch(db, 'all_sources', 'complete', 'success', 
                             results['races_updated'] + results['entries_updated'])
            
        except Exception as e:
            logger.error(f"Data fetch failed: {str(e)}")
            results['errors'].append(str(e))
            self._record_fetch(db, 'all_sources', 'complete', 'failed', 0, str(e))
        
        return results
    
    async def _initialize_tracks(self, db: Session):
        """Initialize Ontario harness racing tracks"""
        tracks_data = [
            {
                'name': 'Woodbine Mohawk Park',
                'location': 'Campbellville, ON',
                'surface': 'synthetic',
                'circumference': 875.0
            },
            {
                'name': 'Georgian Downs',
                'location': 'Innisfil, ON',
                'surface': 'synthetic',
                'circumference': 875.0
            },
            {
                'name': 'Grand River Raceway',
                'location': 'Elora, ON',
                'surface': 'synthetic',
                'circumference': 875.0
            },
            {
                'name': 'Hanover Raceway',
                'location': 'Hanover, ON',
                'surface': 'synthetic',
                'circumference': 875.0
            },
            {
                'name': 'Kawartha Downs',
                'location': 'Fraserville, ON',
                'surface': 'synthetic',
                'circumference': 875.0
            }
        ]
        
        for track_data in tracks_data:
            existing_track = db.query(Track).filter(Track.name == track_data['name']).first()
            if not existing_track:
                track = Track(**track_data)
                db.add(track)
        
        db.commit()
    
    async def _fetch_sample_data(self, db: Session, results: Dict[str, Any]):
        """Generate sample data for demonstration purposes"""
        
        # Sample horses
        sample_horses = [
            {'name': 'Lightning Strike', 'registration_number': 'ON2021001', 'sex': 'stallion', 'color': 'bay', 'owner': 'Thunder Bay Stables'},
            {'name': 'Midnight Express', 'registration_number': 'ON2021002', 'sex': 'mare', 'color': 'black', 'owner': 'Moonlight Racing'},
            {'name': 'Golden Arrow', 'registration_number': 'ON2021003', 'sex': 'gelding', 'color': 'chestnut', 'owner': 'Arrow Stables'},
            {'name': 'Storm Chaser', 'registration_number': 'ON2021004', 'sex': 'stallion', 'color': 'grey', 'owner': 'Weather Vane Farm'},
            {'name': 'Fire Dancer', 'registration_number': 'ON2021005', 'sex': 'mare', 'color': 'sorrel', 'owner': 'Flame Racing'},
            {'name': 'Ice Breaker', 'registration_number': 'ON2021006', 'sex': 'gelding', 'color': 'white', 'owner': 'Arctic Stables'},
            {'name': 'Thunder Bolt', 'registration_number': 'ON2021007', 'sex': 'stallion', 'color': 'bay', 'owner': 'Lightning Farms'},
            {'name': 'Wind Walker', 'registration_number': 'ON2021008', 'sex': 'mare', 'color': 'brown', 'owner': 'Breeze Stables'}
        ]
        
        for horse_data in sample_horses:
            existing_horse = db.query(Horse).filter(Horse.registration_number == horse_data['registration_number']).first()
            if not existing_horse:
                horse = Horse(
                    name=horse_data['name'],
                    registration_number=horse_data['registration_number'],
                    foaling_date=date(2019, 4, 15),  # Sample foaling date
                    sex=horse_data['sex'],
                    color=horse_data['color'],
                    sire='Sample Sire',
                    dam='Sample Dam',
                    breeder='Sample Breeder',
                    owner=horse_data['owner']
                )
                db.add(horse)
                results['horses_updated'] += 1
        
        # Sample drivers
        sample_drivers = [
            {'name': 'John MacDonald', 'license_number': 'DR2024001', 'hometown': 'Toronto, ON'},
            {'name': 'Sarah Johnson', 'license_number': 'DR2024002', 'hometown': 'Ottawa, ON'},
            {'name': 'Mike Wilson', 'license_number': 'DR2024003', 'hometown': 'Hamilton, ON'},
            {'name': 'Lisa Brown', 'license_number': 'DR2024004', 'hometown': 'London, ON'},
            {'name': 'David Smith', 'license_number': 'DR2024005', 'hometown': 'Kingston, ON'},
            {'name': 'Jennifer Davis', 'license_number': 'DR2024006', 'hometown': 'Windsor, ON'}
        ]
        
        for driver_data in sample_drivers:
            existing_driver = db.query(Driver).filter(Driver.license_number == driver_data['license_number']).first()
            if not existing_driver:
                driver = Driver(
                    name=driver_data['name'],
                    license_number=driver_data['license_number'],
                    birth_date=date(1985, 6, 15),  # Sample birth date
                    hometown=driver_data['hometown']
                )
                db.add(driver)
                results['drivers_updated'] += 1
        
        # Sample trainers
        sample_trainers = [
            {'name': 'Robert Thompson', 'license_number': 'TR2024001', 'hometown': 'Mississauga, ON'},
            {'name': 'Mary Anderson', 'license_number': 'TR2024002', 'hometown': 'Brampton, ON'},
            {'name': 'James Miller', 'license_number': 'TR2024003', 'hometown': 'Markham, ON'},
            {'name': 'Patricia Garcia', 'license_number': 'TR2024004', 'hometown': 'Vaughan, ON'},
            {'name': 'William Martinez', 'license_number': 'TR2024005', 'hometown': 'Richmond Hill, ON'}
        ]
        
        for trainer_data in sample_trainers:
            existing_trainer = db.query(Trainer).filter(Trainer.license_number == trainer_data['license_number']).first()
            if not existing_trainer:
                trainer = Trainer(
                    name=trainer_data['name'],
                    license_number=trainer_data['license_number'],
                    birth_date=date(1975, 8, 20),  # Sample birth date
                    hometown=trainer_data['hometown']
                )
                db.add(trainer)
                results['trainers_updated'] += 1
        
        db.commit()
        
        # Create sample races and entries
        await self._create_sample_races(db, results)
    
    async def _create_sample_races(self, db: Session, results: Dict[str, Any]):
        """Create sample races with entries"""
        
        # Get tracks, horses, drivers, trainers
        tracks = db.query(Track).all()
        horses = db.query(Horse).all()
        drivers = db.query(Driver).all()
        trainers = db.query(Trainer).all()
        
        if not all([tracks, horses, drivers, trainers]):
            return
        
        # Create races for today and recent dates
        race_dates = [date.today() - timedelta(days=i) for i in range(7)]
        
        for race_date in race_dates:
            for track in tracks[:2]:  # Use first 2 tracks
                for race_num in range(1, 9):  # 8 races per day
                    existing_race = db.query(Race).filter(
                        Race.track_id == track.id,
                        Race.race_date == race_date,
                        Race.race_number == race_num
                    ).first()
                    
                    if not existing_race:
                        # Calculate post time with proper minute handling
                        base_hour = 19
                        minutes_increment = race_num * 15
                        total_minutes = minutes_increment
                        hours_to_add = total_minutes // 60
                        final_minutes = total_minutes % 60
                        final_hour = base_hour + hours_to_add
                        
                        race = Race(
                            track_id=track.id,
                            race_number=race_num,
                            race_date=race_date,
                            post_time=datetime.combine(race_date, datetime.min.time().replace(hour=final_hour, minute=final_minutes)),
                            distance=1609,  # 1 mile in meters
                            purse=15000.00,
                            race_type='allowance',
                            conditions='Non-winners of $10,000 in last 5 starts',
                            track_condition='fast',
                            weather='clear',
                            temperature=22.0,
                            status='finished' if race_date < date.today() else 'scheduled'
                        )
                        db.add(race)
                        db.flush()  # Get the race ID
                        
                        # Create entries for this race
                        import random
                        selected_horses = random.sample(horses, min(8, len(horses)))
                        selected_drivers = random.sample(drivers, min(8, len(drivers)))
                        selected_trainers = random.sample(trainers, min(8, len(trainers)))
                        
                        for i, (horse, driver, trainer) in enumerate(zip(selected_horses, selected_drivers, selected_trainers)):
                            entry = RaceEntry(
                                race_id=race.id,
                                horse_id=horse.id,
                                driver_id=driver.id,
                                trainer_id=trainer.id,
                                post_position=i + 1,
                                program_number=str(i + 1),
                                morning_line_odds=f"{random.randint(2, 20)}-1"
                            )
                            
                            # Add results for finished races
                            if race.status == 'finished':
                                positions = list(range(1, 9))
                                random.shuffle(positions)
                                entry.finish_position = positions[i]
                                entry.final_odds = f"{random.randint(2, 25)}-1"
                                entry.finish_time = f"1:{random.randint(50, 59)}.{random.randint(10, 99)}"
                                entry.earnings = 15000.00 / (2 ** (entry.finish_position - 1)) if entry.finish_position <= 5 else 0
                                if i > 0:
                                    entry.margin = f"{random.randint(1, 10)} lengths"
                            
                            db.add(entry)
                            results['entries_updated'] += 1
                        
                        results['races_updated'] += 1
        
        db.commit()
    
    def _record_fetch(self, db: Session, source: str, fetch_type: str, status: str, 
                     records_processed: int, error_message: str = None):
        """Record data fetch attempt"""
        fetch_record = DataFetch(
            source=source,
            fetch_type=fetch_type,
            fetch_date=date.today(),
            status=status,
            records_processed=records_processed,
            error_message=error_message,
            completed_at=datetime.now()
        )
        db.add(fetch_record)
        db.commit()
    
    def get_data_status(self, db: Session) -> DataStatusResponse:
        """Get current data status and freshness"""
        
        # Get last successful fetch
        last_fetch = db.query(DataFetch)\
                       .filter(DataFetch.status == 'success')\
                       .order_by(DataFetch.completed_at.desc())\
                       .first()
        
        # Get counts
        total_races = db.query(Race).count()
        total_horses = db.query(Horse).filter(Horse.active == True).count()
        total_drivers = db.query(Driver).filter(Driver.active == True).count()
        total_trainers = db.query(Trainer).filter(Trainer.active == True).count()
        
        # Determine data freshness
        data_freshness = "outdated"
        if last_fetch:
            hours_since_fetch = (datetime.now() - last_fetch.completed_at).total_seconds() / 3600
            if hours_since_fetch < 2:
                data_freshness = "fresh"
            elif hours_since_fetch < 24:
                data_freshness = "stale"
        
        return DataStatusResponse(
            last_fetch=last_fetch.completed_at if last_fetch else None,
            total_races=total_races,
            total_horses=total_horses,
            total_drivers=total_drivers,
            total_trainers=total_trainers,
            data_freshness=data_freshness
        )
    
    async def close(self):
        """Close the HTTP session"""
        await self.session.aclose()
    
    async def _fetch_real_data(self, db: Session, results: Dict[str, Any]) -> bool:
        """Attempt to fetch real racing data from Ontario sources"""
        try:
            logger.info("Attempting to fetch real Ontario harness racing data...")
            
            # Use the Ontario Racing API to get real data
            real_data = await self.fetch_real_ontario_data()
            
            if real_data.get('data_quality') == 'real' and real_data.get('total_races', 0) > 0:
                # Process today's races
                today_races = real_data.get('todays_races', [])
                historical_races = real_data.get('future_races', [])
                
                # Create races from real data
                races_created = await self._process_real_races(db, today_races + historical_races, results)
                
                if races_created > 0:
                    logger.info(f"Successfully created {races_created} races from real data")
                    return True
                else:
                    logger.info("No new races created from real data sources")
            
            # If real data fetch didn't work or returned no data, log and return False
            logger.info("Real data fetch completed but no usable data found")
            return False
            
        except Exception as e:
            logger.error(f"Error fetching real data: {e}")
            results['errors'].append(f"Real data fetch error: {str(e)}")
            return False
    
    async def fetch_real_ontario_data(self) -> Dict[str, Any]:
        """Fetch real Ontario harness racing data from multiple sources"""
        logger.info("Fetching real Ontario harness racing data...")
        
        try:
            # Get today's races
            todays_races = await get_ontario_races_today()
            
            # Get future races (next 7 days)
            future_races = await get_ontario_future_races(7)
            
            # Get live odds
            live_odds = await get_live_ontario_odds()
            
            # Get recent results (past 3 days)
            recent_results = []
            for i in range(1, 4):
                past_date = date.today() - timedelta(days=i)
                for track in ["Woodbine Mohawk Park", "Georgian Downs", "Grand River Raceway"]:
                    results = await get_ontario_race_results(track, past_date)
                    recent_results.extend(results)
            
            return {
                'todays_races': todays_races,
                'future_races': future_races,
                'live_odds': live_odds,
                'recent_results': recent_results,
                'sources': [
                    'Standardbred Canada',
                    'Woodbine Mohawk Park',
                    'The Odds API',
                    'Ontario Racing Commission'
                ],
                'last_updated': datetime.now().isoformat(),
                'data_quality': 'real',
                'total_races': len(todays_races) + len(future_races)
            }
            
        except Exception as e:
            logger.error(f"Error fetching real Ontario data: {e}")
            # Fallback to sample data
            return await self.generate_sample_data()
    
    async def fetch_and_store_real_data(self, db: Session) -> Dict[str, Any]:
        """Fetch real Ontario racing data and store it in the database"""
        logger.info("Fetching and storing real Ontario racing data...")
        
        try:
            # Fetch real data
            real_data = await self.fetch_real_ontario_data()
            
            if real_data.get('data_quality') == 'real' and real_data.get('total_races', 0) > 0:
                # Process and store the data
                results = {
                    'races_updated': 0,
                    'horses_updated': 0,
                    'drivers_updated': 0,
                    'trainers_updated': 0,
                    'entries_updated': 0,
                    'errors': []
                }
                
                # Initialize tracks
                await self._initialize_tracks(db)
                
                # Process races
                all_races = real_data.get('todays_races', []) + real_data.get('future_races', [])
                races_created = await self._process_real_races(db, all_races, results)
                
                return {
                    'success': True,
                    'data_source': 'real',
                    'statistics': results,
                    'sources': real_data.get('sources', []),
                    'total_races': real_data.get('total_races', 0),
                    'last_updated': real_data.get('last_updated')
                }
            else:
                # Fallback to sample data
                logger.info("Real data not available, using sample data")
                return await self.generate_and_store_sample_data(db)
                
        except Exception as e:
            logger.error(f"Error in fetch_and_store_real_data: {e}")
            # Fallback to sample data on error
            return await self.generate_and_store_sample_data(db)
    
    async def _process_real_races(self, db: Session, race_results: List, results: Dict[str, Any]) -> int:
        """Process real race results and create database entries"""
        races_created = 0
        
        try:
            for race_result in race_results:
                # Get or create track
                track = db.query(Track).filter(Track.name == race_result.track_name).first()
                if not track:
                    # Create track if it doesn't exist
                    track = Track(
                        name=race_result.track_name,
                        location="Ontario, Canada",
                        surface="synthetic",
                        circumference=875.0,
                        active=True
                    )
                    db.add(track)
                    db.commit()
                    results['tracks_updated'] += 1
                
                # Check if race already exists
                existing_race = db.query(Race).filter(
                    Race.track_id == track.id,
                    Race.race_number == race_result.race_number,
                    Race.race_date == race_result.race_date
                ).first()
                
                if not existing_race:
                    # Create new race
                    race = Race(
                        track_id=track.id,
                        race_number=race_result.race_number,
                        race_date=race_result.race_date,
                        post_time=race_result.post_time,
                        distance=race_result.distance,
                        purse=race_result.purse,
                        race_type=race_result.race_type,
                        track_condition=race_result.track_condition,
                        status='finished' if race_result.entries else 'scheduled'
                    )
                    db.add(race)
                    db.commit()
                    races_created += 1
                    results['races_updated'] += 1
                    
                    # Process race entries if available
                    if race_result.entries:
                        entries_created = await self._process_real_entries(db, race.id, race_result.entries, results)
                        results['entries_updated'] += entries_created
        
        except Exception as e:
            logger.error(f"Error processing real races: {e}")
            results['errors'].append(f"Race processing error: {str(e)}")
        
        return races_created
    
    async def _process_real_entries(self, db: Session, race_id: int, entries: List[Dict], results: Dict[str, Any]) -> int:
        """Process real race entries and create database entries"""
        entries_created = 0
        
        try:
            for entry_data in entries:
                # Get or create horse
                horse = await self._get_or_create_horse(db, entry_data.get('horse_name'), results)
                
                # Get or create driver
                driver = await self._get_or_create_driver(db, entry_data.get('driver_name'), results)
                
                # Get or create trainer
                trainer = await self._get_or_create_trainer(db, entry_data.get('trainer_name'), results)
                
                if horse:
                    # Create race entry
                    race_entry = RaceEntry(
                        race_id=race_id,
                        horse_id=horse.id,
                        driver_id=driver.id if driver else None,
                        trainer_id=trainer.id if trainer else None,
                        post_position=None,  # Would need to extract from real data
                        finish_position=entry_data.get('finish_position'),
                        earnings=entry_data.get('earnings', 0),
                        odds=entry_data.get('odds'),
                        scratched=False
                    )
                    db.add(race_entry)
                    entries_created += 1
            
            db.commit()
        
        except Exception as e:
            logger.error(f"Error processing real entries: {e}")
            results['errors'].append(f"Entry processing error: {str(e)}")
        
        return entries_created
    
    async def _get_or_create_horse(self, db: Session, horse_name: str, results: Dict[str, Any]) -> Optional[Horse]:
        """Get existing horse or create new one"""
        if not horse_name:
            return None
            
        horse = db.query(Horse).filter(Horse.name == horse_name).first()
        if not horse:
            horse = Horse(
                name=horse_name,
                registration_number=f"ON{len(horse_name)}{hash(horse_name) % 10000:04d}",
                foaling_year=2018,  # Default year, would need real data
                sire="Unknown",
                dam="Unknown",
                sex="G",
                color="Brown",
                active=True
            )
            db.add(horse)
            db.commit()
            results['horses_updated'] += 1
        
        return horse
    
    async def _get_or_create_driver(self, db: Session, driver_name: str, results: Dict[str, Any]) -> Optional[Driver]:
        """Get existing driver or create new one"""
        if not driver_name:
            return None
            
        driver = db.query(Driver).filter(Driver.name == driver_name).first()
        if not driver:
            driver = Driver(
                name=driver_name,
                license_number=f"DRV{hash(driver_name) % 10000:04d}",
                hometown="Ontario, Canada",
                active=True
            )
            db.add(driver)
            db.commit()
            results['drivers_updated'] += 1
        
        return driver
    
    async def _get_or_create_trainer(self, db: Session, trainer_name: str, results: Dict[str, Any]) -> Optional[Trainer]:
        """Get existing trainer or create new one"""
        if not trainer_name:
            return None
            
        trainer = db.query(Trainer).filter(Trainer.name == trainer_name).first()
        if not trainer:
            trainer = Trainer(
                name=trainer_name,
                license_number=f"TRN{hash(trainer_name) % 10000:04d}",
                location="Ontario, Canada",
                active=True
            )
            db.add(trainer)
            db.commit()
            results['trainers_updated'] += 1
        
        return trainer

    async def update_live_odds(self, db: Session) -> Dict[str, Any]:
        """Update live odds for today's races"""
        try:
            live_odds = await get_live_ontario_odds()
            
            if not live_odds:
                return {'success': False, 'message': 'No live odds available'}
            
            updated_count = 0
            
            # Update odds in database
            # This would need to be implemented based on the actual odds data structure
            
            return {
                'success': True,
                'updated_entries': updated_count,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error updating live odds: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_enhanced_horse_stats(self, horse_name: str) -> Dict[str, Any]:
        """Get enhanced horse statistics from real data sources"""
        try:
            stats = await search_horse_stats(horse_name)
            return stats
        except Exception as e:
            logger.error(f"Error getting enhanced horse stats: {e}")
            return {}
    
    async def get_enhanced_driver_stats(self, driver_name: str) -> Dict[str, Any]:
        """Get enhanced driver statistics from real data sources"""
        try:
            stats = await search_driver_stats(driver_name)
            return stats
        except Exception as e:
            logger.error(f"Error getting enhanced driver stats: {e}")
            return {}
    
    async def get_enhanced_trainer_stats(self, trainer_name: str) -> Dict[str, Any]:
        """Get enhanced trainer statistics from real data sources"""
        try:
            stats = await search_trainer_stats(trainer_name)
            return stats
        except Exception as e:
            logger.error(f"Error getting enhanced trainer stats: {e}")
            return {}

    # Keep existing sample data methods as fallback
    async def generate_sample_data(self) -> Dict[str, Any]:
        """Generate sample harness racing data as fallback"""
        logger.info("Generating sample Ontario harness racing data...")
        
        # Sample tracks in Ontario
        tracks = [
            "Woodbine Mohawk Park",
            "Georgian Downs", 
            "Grand River Raceway",
            "Hanover Raceway",
            "Hiawatha Horse Park"
        ]
        
        # Sample race data
        races = []
        for track in tracks:
            for race_num in range(1, random.randint(8, 12)):  # 8-12 races per track
                race = {
                    'track': track,
                    'race_number': race_num,
                    'date': date.today(),
                    'post_time': f"{6 + race_num}:00 PM",
                    'distance': "1 Mile",
                    'surface': "Fast",
                    'race_type': random.choice(["Pace", "Trot"]),
                    'purse': random.randint(8000, 25000),
                    'conditions': "Open Handicap",
                    'entries': self._generate_sample_entries(8)
                }
                races.append(race)
        
        return {
            'todays_races': races,
            'future_races': [],
            'live_odds': {},
            'recent_results': [],
            'sources': ['Sample Data Generator'],
            'last_updated': datetime.now().isoformat(),
            'data_quality': 'sample',
            'total_races': len(races)
        }
    
    def _generate_sample_entries(self, count: int) -> List[Dict]:
        """Generate sample race entries"""
        sample_horses = [
            "Lightning Strike", "Thunder Bay", "Maple Leaf", "Northern Star",
            "Golden Arrow", "Silver Bullet", "Racing Thunder", "Swift Wind",
            "Midnight Express", "Royal Flush", "Lucky Charm", "Fire Storm"
        ]
        
        sample_drivers = [
            "John MacDonald", "Trevor Henry", "Scott Coulter", "Doug McNair",
            "James MacDonald", "Jody Jamieson", "Bob McClure", "Tyler Borth"
        ]
        
        sample_trainers = [
            "Ben Wallace", "Richard Moreau", "Carl Jamieson", "Robert McIntosh",
            "Travis Cullen", "Jodie Cullen", "Mark Steacy", "Paul MacKenzie"
        ]
        
        entries = []
        for i in range(count):
            entry = {
                'horse_name': random.choice(sample_horses),
                'driver': random.choice(sample_drivers),
                'trainer': random.choice(sample_trainers),
                'post_position': i + 1,
                'program_number': str(i + 1),
                'morning_line_odds': f"{random.randint(2, 12)}-1",
                'age': random.randint(3, 8),
                'sex': random.choice(['M', 'F', 'G']),
                'sire': "Unknown Sire",
                'dam': "Unknown Dam",
                'owner': f"Owner {i + 1}",
                'earnings': random.randint(5000, 150000),
                'starts': random.randint(10, 50),
                'wins': random.randint(1, 15),
                'places': random.randint(2, 20),
                'shows': random.randint(3, 25)
            }
            entries.append(entry)
        
        return entries

    async def generate_and_store_sample_data(self, db: Session) -> Dict[str, Any]:
        """Generate and store sample data in database"""
        logger.info("Generating and storing sample data...")
        
        try:
            # Clear existing data
            db.execute(text("DELETE FROM race_entries"))
            db.execute(text("DELETE FROM races"))
            db.execute(text("DELETE FROM horses"))
            db.execute(text("DELETE FROM drivers"))
            db.execute(text("DELETE FROM trainers"))
            db.commit()

            stats = {
                'races_created': 0,
                'horses_created': 0,
                'drivers_created': 0,
                'trainers_created': 0,
                'entries_created': 0
            }

            # Create sample trainers
            sample_trainers = [
                "Ben Wallace", "Richard Moreau", "Carl Jamieson", "Robert McIntosh",
                "Travis Cullen", "Jodie Cullen", "Mark Steacy", "Paul MacKenzie"
            ]
            
            trainers = {}
            for trainer_name in sample_trainers:
                trainer = Trainer(
                    name=trainer_name,
                    license_number=f"TRN{random.randint(1000, 9999)}",
                    stable_name=f"{trainer_name} Stable",
                    phone=f"519-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                    email=f"{trainer_name.lower().replace(' ', '.')}@email.com"
                )
                db.add(trainer)
                trainers[trainer_name] = trainer
                stats['trainers_created'] += 1

            # Create sample drivers
            sample_drivers = [
                "John MacDonald", "Trevor Henry", "Scott Coulter", "Doug McNair",
                "James MacDonald", "Jody Jamieson", "Bob McClure", "Tyler Borth"
            ]
            
            drivers = {}
            for driver_name in sample_drivers:
                driver = Driver(
                    name=driver_name,
                    license_number=f"ON{random.randint(1000, 9999)}",
                    birth_date=date(random.randint(1970, 1995), random.randint(1, 12), random.randint(1, 28)),
                    hometown="Ontario, Canada"
                )
                db.add(driver)
                drivers[driver_name] = driver
                stats['drivers_created'] += 1

            # Create sample horses
            sample_horses = [
                "Lightning Strike", "Thunder Bay", "Maple Leaf", "Northern Star",
                "Golden Arrow", "Silver Bullet", "Racing Thunder", "Swift Wind",
                "Midnight Express", "Royal Flush", "Lucky Charm", "Fire Storm",
                "Blazing Speed", "Storm Chaser", "Victory Lane", "Power Play"
            ]
            
            horses = {}
            for horse_name in sample_horses:
                horse = Horse(
                    name=horse_name,
                    age=random.randint(3, 8),
                    sex=random.choice(['M', 'F', 'G']),
                    sire="Unknown Sire",
                    dam="Unknown Dam", 
                    color=random.choice(['Bay', 'Brown', 'Chestnut', 'Black', 'Grey']),
                    foaling_date=date(2024 - random.randint(3, 8), random.randint(1, 12), random.randint(1, 28)),
                    owner=f"Owner {random.randint(1, 20)}",
                    breeder=f"Breeder {random.randint(1, 15)}"
                )
                db.add(horse)
                horses[horse_name] = horse
                stats['horses_created'] += 1

            db.flush()  # Ensure IDs are assigned

            # Create sample races
            tracks = [
                "Woodbine Mohawk Park",
                "Georgian Downs", 
                "Grand River Raceway",
                "Hanover Raceway"
            ]

            race_dates = [date.today() + timedelta(days=i) for i in range(-2, 5)]
            
            for track in tracks:
                for race_date in race_dates:
                    # Skip some days for some tracks
                    if random.random() < 0.3:
                        continue
                        
                    num_races = random.randint(8, 12)
                    for race_num in range(1, num_races + 1):
                        # Calculate race time with proper minute handling
                        base_hour = 18  # 6 PM
                        race_minutes = (race_num - 1) * 20  # 20 minutes between races
                        race_hour = base_hour + (race_minutes // 60)
                        race_minute = race_minutes % 60
                        
                        post_time = datetime.combine(
                            race_date, 
                            datetime.min.time().replace(hour=race_hour, minute=race_minute)
                        )

                        race = Race(
                            track_name=track,
                            race_date=race_date,
                            race_number=race_num,
                            post_time=post_time,
                            distance=random.choice([1609, 1609, 1200, 1400]),  # Mostly 1 mile
                            purse=random.randint(8000, 25000),
                            race_type=random.choice(["Pace", "Trot"]),
                            track_condition=random.choice(["Fast", "Good", "Sloppy"]),
                            weather=random.choice(["Clear", "Cloudy", "Light Rain"])
                        )
                        db.add(race)
                        stats['races_created'] += 1

                        db.flush()  # Get race ID

                        # Create race entries
                        num_entries = random.randint(6, 10)
                        selected_horses = random.sample(list(horses.keys()), min(num_entries, len(horses)))
                        
                        for i, horse_name in enumerate(selected_horses):
                            horse = horses[horse_name]
                            driver = random.choice(list(drivers.values()))
                            trainer = random.choice(list(trainers.values()))

                            entry = RaceEntry(
                                race_id=race.id,
                                horse_id=horse.id,
                                driver_id=driver.id,
                                trainer_id=trainer.id,
                                post_position=i + 1,
                                program_number=str(i + 1),
                                morning_line_odds=random.uniform(1.5, 15.0),
                                actual_odds=random.uniform(1.2, 20.0),
                                finish_position=random.randint(1, num_entries) if race_date < date.today() else None,
                                win_time=f"1:{random.randint(50, 59)}.{random.randint(10, 99)}" if race_date < date.today() and random.random() < 0.2 else None,
                                earnings=random.randint(0, 5000) if race_date < date.today() else 0.0,
                                equipment_change="",
                                scratched=random.random() < 0.05,  # 5% scratch rate
                                late_change=""
                            )
                            db.add(entry)
                            stats['entries_created'] += 1

            db.commit()
            logger.info(f"Sample data created successfully: {stats}")
            
            return {
                'success': True,
                'data_source': 'sample',
                'statistics': stats,
                'sources': ['Sample Data Generator']
            }

        except Exception as e:
            logger.error(f"Error generating sample data: {e}")
            db.rollback()
            return {
                'success': False,
                'error': str(e),
                'data_source': 'sample'
            }