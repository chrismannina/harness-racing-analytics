from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from typing import List, Optional
from datetime import date, datetime
from models import Race, Track, RaceEntry, Horse, Driver, Trainer
from schemas import RaceResponse, RaceDetailResponse, TrackResponse, TrackDetailResponse, RaceResultResponse

class RaceService:
    def get_races(self, db: Session, date: Optional[date] = None, track_id: Optional[int] = None, limit: int = 50) -> List[RaceResponse]:
        query = db.query(Race).join(Track)
        
        if date:
            query = query.filter(Race.race_date == date)
        if track_id:
            query = query.filter(Race.track_id == track_id)
            
        races = query.order_by(desc(Race.race_date), Race.race_number).limit(limit).all()
        return [RaceResponse.model_validate(race) for race in races]
    
    def get_race_by_id(self, db: Session, race_id: int) -> Optional[RaceDetailResponse]:
        race = db.query(Race).filter(Race.id == race_id).first()
        if race:
            return RaceDetailResponse.model_validate(race)
        return None
    
    def get_race_results(self, db: Session, race_id: int) -> List[RaceResultResponse]:
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
         .filter(RaceEntry.race_id == race_id)\
         .filter(RaceEntry.finish_position.isnot(None))\
         .order_by(RaceEntry.finish_position).all()
        
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
    
    def get_tracks(self, db: Session) -> List[TrackResponse]:
        tracks = db.query(Track).filter(Track.active == True).all()
        return [TrackResponse.model_validate(track) for track in tracks]
    
    def get_track_by_id(self, db: Session, track_id: int) -> Optional[TrackDetailResponse]:
        track = db.query(Track).filter(Track.id == track_id).first()
        if track:
            return TrackDetailResponse.model_validate(track)
        return None
    
    def get_today_race_count(self, db: Session) -> int:
        return db.query(Race).filter(Race.race_date == date.today()).count()
    
    def get_recent_races(self, db: Session, limit: int = 10) -> List[RaceResponse]:
        races = db.query(Race).join(Track)\
                  .filter(Race.status == 'finished')\
                  .order_by(desc(Race.race_date), desc(Race.race_number))\
                  .limit(limit).all()
        return [RaceResponse.model_validate(race) for race in races]