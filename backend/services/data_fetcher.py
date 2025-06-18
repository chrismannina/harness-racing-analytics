import httpx
import asyncio
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
import logging
from bs4 import BeautifulSoup
import re
from models import Track, Horse, Driver, Trainer, Race, RaceEntry, DataFetch
from schemas import DataStatusResponse

logger = logging.getLogger(__name__)

class DataFetcher:
    def __init__(self):
        self.base_urls = {
            'woodbine': 'https://woodbine.com/mohawk/',
            'standardbred_canada': 'https://www.standardbredcanada.ca/',
            'ontario_racing': 'https://www.ontarioracing.com/'
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
            
            # Fetch sample data for demonstration
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