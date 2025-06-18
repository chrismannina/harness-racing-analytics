from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from typing import List, Optional
from models import Driver, RaceEntry, Race, Track, Horse, Trainer
from schemas import DriverResponse, DriverDetailResponse, DriverStatsResponse
from decimal import Decimal

class DriverService:
    def get_drivers(self, db: Session, name: Optional[str] = None, limit: int = 50) -> List[DriverResponse]:
        query = db.query(Driver).filter(Driver.active == True)
        
        if name:
            query = query.filter(Driver.name.ilike(f"%{name}%"))
            
        drivers = query.order_by(Driver.name).limit(limit).all()
        return [DriverResponse.model_validate(driver) for driver in drivers]
    
    def get_driver_by_id(self, db: Session, driver_id: int) -> Optional[DriverDetailResponse]:
        driver = db.query(Driver).filter(Driver.id == driver_id).first()
        if driver:
            return DriverDetailResponse.model_validate(driver)
        return None
    
    def get_driver_stats(self, db: Session, driver_id: int) -> DriverStatsResponse:
        # Get basic stats
        stats = db.query(
            func.count(RaceEntry.id).label('total_starts'),
            func.sum(func.case((RaceEntry.finish_position == 1, 1), else_=0)).label('wins'),
            func.sum(func.case((RaceEntry.finish_position == 2, 1), else_=0)).label('places'),
            func.sum(func.case((RaceEntry.finish_position == 3, 1), else_=0)).label('shows'),
            func.sum(RaceEntry.earnings).label('total_earnings')
        ).filter(RaceEntry.driver_id == driver_id)\
         .filter(RaceEntry.scratched == False)\
         .first()
        
        total_starts = stats.total_starts or 0
        wins = stats.wins or 0
        places = stats.places or 0
        shows = stats.shows or 0
        total_earnings = stats.total_earnings or Decimal('0.00')
        
        # Calculate percentages
        win_percentage = (wins / total_starts * 100) if total_starts > 0 else 0
        place_percentage = ((wins + places) / total_starts * 100) if total_starts > 0 else 0
        show_percentage = ((wins + places + shows) / total_starts * 100) if total_starts > 0 else 0
        average_earnings = (total_earnings / total_starts) if total_starts > 0 else Decimal('0.00')
        
        return DriverStatsResponse(
            driver_id=driver_id,
            total_starts=total_starts,
            wins=wins,
            places=places,
            shows=shows,
            win_percentage=round(win_percentage, 2),
            place_percentage=round(place_percentage, 2),
            show_percentage=round(show_percentage, 2),
            total_earnings=total_earnings,
            average_earnings=average_earnings
        )
    
    def get_total_drivers(self, db: Session) -> int:
        return db.query(Driver).filter(Driver.active == True).count()
    
    def get_top_drivers_by_wins(self, db: Session, limit: int = 10) -> List[dict]:
        results = db.query(
            Driver.id,
            Driver.name,
            func.count(RaceEntry.id).label('total_starts'),
            func.sum(func.case((RaceEntry.finish_position == 1, 1), else_=0)).label('wins'),
            func.sum(RaceEntry.earnings).label('total_earnings')
        ).join(RaceEntry)\
         .filter(Driver.active == True)\
         .filter(RaceEntry.scratched == False)\
         .group_by(Driver.id, Driver.name)\
         .order_by(desc('wins'))\
         .limit(limit).all()
        
        return [
            {
                'id': result.id,
                'name': result.name,
                'total_starts': result.total_starts,
                'wins': result.wins,
                'win_percentage': round((result.wins / result.total_starts * 100) if result.total_starts > 0 else 0, 2),
                'total_earnings': float(result.total_earnings or 0)
            }
            for result in results
        ]
    
    def get_top_drivers_by_earnings(self, db: Session, limit: int = 10) -> List[dict]:
        results = db.query(
            Driver.id,
            Driver.name,
            func.count(RaceEntry.id).label('total_starts'),
            func.sum(func.case((RaceEntry.finish_position == 1, 1), else_=0)).label('wins'),
            func.sum(RaceEntry.earnings).label('total_earnings')
        ).join(RaceEntry)\
         .filter(Driver.active == True)\
         .filter(RaceEntry.scratched == False)\
         .group_by(Driver.id, Driver.name)\
         .order_by(desc('total_earnings'))\
         .limit(limit).all()
        
        return [
            {
                'id': result.id,
                'name': result.name,
                'total_starts': result.total_starts,
                'wins': result.wins,
                'win_percentage': round((result.wins / result.total_starts * 100) if result.total_starts > 0 else 0, 2),
                'total_earnings': float(result.total_earnings or 0)
            }
            for result in results
        ]