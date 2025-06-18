from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func, case
from typing import List, Optional
from models import Horse, RaceEntry, Race, Track, Driver, Trainer
from schemas import HorseResponse, HorseDetailResponse, HorseStatsResponse, RaceResultResponse
from decimal import Decimal

class HorseService:
    def get_horses(self, db: Session, name: Optional[str] = None, limit: int = 50) -> List[HorseResponse]:
        query = db.query(Horse).filter(Horse.active == True)
        
        if name:
            query = query.filter(Horse.name.ilike(f"%{name}%"))
            
        horses = query.order_by(Horse.name).limit(limit).all()
        return [HorseResponse.model_validate(horse) for horse in horses]
    
    def get_horse_by_id(self, db: Session, horse_id: int) -> Optional[HorseDetailResponse]:
        horse = db.query(Horse).filter(Horse.id == horse_id).first()
        if horse:
            return HorseDetailResponse.model_validate(horse)
        return None
    
    def get_horse_stats(self, db: Session, horse_id: int) -> HorseStatsResponse:
        # Get basic stats
        stats = db.query(
            func.count(RaceEntry.id).label('total_starts'),
            func.sum(case((RaceEntry.finish_position == 1, 1), else_=0)).label('wins'),
            func.sum(case((RaceEntry.finish_position == 2, 1), else_=0)).label('places'),
            func.sum(case((RaceEntry.finish_position == 3, 1), else_=0)).label('shows'),
            func.sum(RaceEntry.earnings).label('total_earnings')
        ).filter(RaceEntry.horse_id == horse_id)\
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
        
        # Get best time
        best_time_result = db.query(RaceEntry.finish_time)\
                            .filter(RaceEntry.horse_id == horse_id)\
                            .filter(RaceEntry.finish_time.isnot(None))\
                            .filter(RaceEntry.finish_position == 1)\
                            .order_by(RaceEntry.finish_time)\
                            .first()
        best_time = best_time_result.finish_time if best_time_result else None
        
        # Get recent form (last 5 races)
        recent_races = db.query(RaceEntry.finish_position)\
                        .join(Race)\
                        .filter(RaceEntry.horse_id == horse_id)\
                        .filter(RaceEntry.scratched == False)\
                        .order_by(desc(Race.race_date), desc(Race.race_number))\
                        .limit(5).all()
        
        recent_form = [str(race.finish_position) if race.finish_position else 'DNF' for race in recent_races]
        
        return HorseStatsResponse(
            horse_id=horse_id,
            total_starts=total_starts,
            wins=wins,
            places=places,
            shows=shows,
            win_percentage=round(win_percentage, 2),
            place_percentage=round(place_percentage, 2),
            show_percentage=round(show_percentage, 2),
            total_earnings=total_earnings,
            average_earnings=average_earnings,
            best_time=best_time,
            recent_form=recent_form
        )
    
    def get_horse_races(self, db: Session, horse_id: int, limit: int = 20) -> List[RaceResultResponse]:
        results = db.query(
            RaceEntry.race_id,
            Race.race_number,
            Race.race_date,
            Track.name.label('track_name'),
            Race.distance,
            RaceEntry.finish_position,
            RaceEntry.finish_time,
            RaceEntry.margin,
            RaceEntry.earnings,
            Horse.name.label('horse_name'),
            Driver.name.label('driver_name'),
            Trainer.name.label('trainer_name'),
            RaceEntry.final_odds
        ).join(Race).join(Track).join(Horse).join(Driver).join(Trainer)\
         .filter(RaceEntry.horse_id == horse_id)\
         .filter(RaceEntry.scratched == False)\
         .order_by(desc(Race.race_date), desc(Race.race_number))\
         .limit(limit).all()
        
        return [RaceResultResponse(
            race_id=result.race_id,
            race_number=result.race_number,
            race_date=result.race_date,
            track_name=result.track_name,
            distance=result.distance,
            finish_position=result.finish_position,
            finish_time=result.finish_time,
            margin=result.margin,
            earnings=result.earnings,
            horse_name=result.horse_name,
            driver_name=result.driver_name,
            trainer_name=result.trainer_name,
            final_odds=result.final_odds
        ) for result in results]
    
    def get_total_horses(self, db: Session) -> int:
        return db.query(Horse).filter(Horse.active == True).count()