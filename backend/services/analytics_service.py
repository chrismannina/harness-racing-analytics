from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func, extract, case
from typing import List, Dict, Any
from datetime import datetime, date, timedelta
from models import Race, RaceEntry, Horse, Driver, Trainer, Track
from schemas import DashboardResponse, TopPerformersResponse, TrendsResponse
from services.race_service import RaceService
from services.horse_service import HorseService
from services.driver_service import DriverService
from services.trainer_service import TrainerService

class AnalyticsService:
    def __init__(self):
        self.race_service = RaceService()
        self.horse_service = HorseService()
        self.driver_service = DriverService()
        self.trainer_service = TrainerService()
    
    def get_dashboard_data(self, db: Session) -> DashboardResponse:
        # Get counts
        total_races_today = self.race_service.get_today_race_count(db)
        total_horses = self.horse_service.get_total_horses(db)
        total_drivers = self.driver_service.get_total_drivers(db)
        total_trainers = self.trainer_service.get_total_trainers(db)
        
        # Get recent races
        recent_races = self.race_service.get_recent_races(db, limit=5)
        
        # Get top performers
        top_horses = self.get_top_horses_by_wins(db, limit=5)
        top_drivers = self.driver_service.get_top_drivers_by_wins(db, limit=5)
        top_trainers = self.trainer_service.get_top_trainers_by_wins(db, limit=5)
        
        return DashboardResponse(
            total_races_today=total_races_today,
            total_horses=total_horses,
            total_drivers=total_drivers,
            total_trainers=total_trainers,
            recent_races=recent_races,
            top_horses=top_horses,
            top_drivers=top_drivers,
            top_trainers=top_trainers
        )
    
    def get_top_performers(self, db: Session, category: str, metric: str, limit: int = 10) -> TopPerformersResponse:
        performers = []
        
        if category == "horses":
            if metric == "wins":
                performers = self.get_top_horses_by_wins(db, limit)
            elif metric == "earnings":
                performers = self.get_top_horses_by_earnings(db, limit)
            elif metric == "win_rate":
                performers = self.get_top_horses_by_win_rate(db, limit)
        elif category == "drivers":
            if metric == "wins":
                performers = self.driver_service.get_top_drivers_by_wins(db, limit)
            elif metric == "earnings":
                performers = self.driver_service.get_top_drivers_by_earnings(db, limit)
        elif category == "trainers":
            if metric == "wins":
                performers = self.trainer_service.get_top_trainers_by_wins(db, limit)
            elif metric == "earnings":
                performers = self.trainer_service.get_top_trainers_by_earnings(db, limit)
        
        return TopPerformersResponse(
            category=category,
            metric=metric,
            performers=performers
        )
    
    def get_trends(self, db: Session, period: str) -> TrendsResponse:
        # Calculate date range based on period
        end_date = date.today()
        if period == "week":
            start_date = end_date - timedelta(days=7)
            date_trunc = 'day'
        elif period == "month":
            start_date = end_date - timedelta(days=30)
            date_trunc = 'day'
        elif period == "quarter":
            start_date = end_date - timedelta(days=90)
            date_trunc = 'week'
        else:  # year
            start_date = end_date - timedelta(days=365)
            date_trunc = 'month'
        
        # Get race trends
        race_trends = db.query(
            Race.race_date,
            func.count(Race.id).label('race_count'),
            func.sum(Race.purse).label('total_purse')
        ).filter(Race.race_date.between(start_date, end_date))\
         .group_by(Race.race_date)\
         .order_by(Race.race_date).all()
        
        data = [
            {
                'date': trend.race_date.isoformat(),
                'race_count': trend.race_count,
                'total_purse': float(trend.total_purse or 0)
            }
            for trend in race_trends
        ]
        
        return TrendsResponse(period=period, data=data)
    
    def get_top_horses_by_wins(self, db: Session, limit: int = 10) -> List[Dict[str, Any]]:
        results = db.query(
            Horse.id,
            Horse.name,
            func.count(RaceEntry.id).label('total_starts'),
            func.sum(case((RaceEntry.finish_position == 1, 1), else_=0)).label('wins'),
            func.sum(RaceEntry.earnings).label('total_earnings')
        ).join(RaceEntry)\
         .filter(Horse.active == True)\
         .filter(RaceEntry.scratched == False)\
         .group_by(Horse.id, Horse.name)\
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
    
    def get_top_horses_by_earnings(self, db: Session, limit: int = 10) -> List[Dict[str, Any]]:
        results = db.query(
            Horse.id,
            Horse.name,
            func.count(RaceEntry.id).label('total_starts'),
            func.sum(case((RaceEntry.finish_position == 1, 1), else_=0)).label('wins'),
            func.sum(RaceEntry.earnings).label('total_earnings')
        ).join(RaceEntry)\
         .filter(Horse.active == True)\
         .filter(RaceEntry.scratched == False)\
         .group_by(Horse.id, Horse.name)\
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
    
    def get_top_horses_by_win_rate(self, db: Session, limit: int = 10, min_starts: int = 5) -> List[Dict[str, Any]]:
        results = db.query(
            Horse.id,
            Horse.name,
            func.count(RaceEntry.id).label('total_starts'),
            func.sum(case((RaceEntry.finish_position == 1, 1), else_=0)).label('wins'),
            func.sum(RaceEntry.earnings).label('total_earnings')
        ).join(RaceEntry)\
         .filter(Horse.active == True)\
         .filter(RaceEntry.scratched == False)\
         .group_by(Horse.id, Horse.name)\
         .having(func.count(RaceEntry.id) >= min_starts)\
         .order_by(desc(func.sum(case((RaceEntry.finish_position == 1, 1), else_=0)) / func.count(RaceEntry.id)))\
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