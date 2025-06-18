from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal

class TrackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    location: str
    surface: str
    circumference: Optional[float] = None
    active: bool

class TrackDetailResponse(TrackResponse):
    created_at: datetime

class HorseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    registration_number: Optional[str] = None
    foaling_date: Optional[date] = None
    sex: Optional[str] = None
    color: Optional[str] = None
    owner: Optional[str] = None
    active: bool

class HorseDetailResponse(HorseResponse):
    sire: Optional[str] = None
    dam: Optional[str] = None
    breeder: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class HorseStatsResponse(BaseModel):
    horse_id: int
    total_starts: int
    wins: int
    places: int
    shows: int
    win_percentage: float
    place_percentage: float
    show_percentage: float
    total_earnings: Decimal
    average_earnings: Decimal
    best_time: Optional[str] = None
    recent_form: List[str]  # Last 5 finishes

class DriverResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    license_number: Optional[str] = None
    hometown: Optional[str] = None
    active: bool

class DriverDetailResponse(DriverResponse):
    birth_date: Optional[date] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class DriverStatsResponse(BaseModel):
    driver_id: int
    total_starts: int
    wins: int
    places: int
    shows: int
    win_percentage: float
    place_percentage: float
    show_percentage: float
    total_earnings: Decimal
    average_earnings: Decimal

class TrainerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    license_number: Optional[str] = None
    hometown: Optional[str] = None
    active: bool

class TrainerDetailResponse(TrainerResponse):
    birth_date: Optional[date] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class TrainerStatsResponse(BaseModel):
    trainer_id: int
    total_starts: int
    wins: int
    places: int
    shows: int
    win_percentage: float
    place_percentage: float
    show_percentage: float
    total_earnings: Decimal
    average_earnings: Decimal

class RaceEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    post_position: int
    program_number: Optional[str] = None
    morning_line_odds: Optional[str] = None
    final_odds: Optional[str] = None
    finish_position: Optional[int] = None
    finish_time: Optional[str] = None
    margin: Optional[str] = None
    earnings: Optional[Decimal] = None
    scratched: bool
    disqualified: bool
    horse: HorseResponse
    driver: DriverResponse
    trainer: TrainerResponse

class RaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    race_number: int
    race_date: date
    post_time: Optional[datetime] = None
    distance: Optional[int] = None
    purse: Optional[Decimal] = None
    race_type: Optional[str] = None
    track_condition: Optional[str] = None
    status: str
    track: TrackResponse

class RaceDetailResponse(RaceResponse):
    conditions: Optional[str] = None
    weather: Optional[str] = None
    temperature: Optional[float] = None
    entries: List[RaceEntryResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

class RaceResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    race_id: int
    race_number: int
    race_date: date
    track_name: str
    distance: Optional[int] = None
    finish_position: int
    finish_time: Optional[str] = None
    margin: Optional[str] = None
    earnings: Optional[Decimal] = None
    horse_name: str
    driver_name: str
    trainer_name: str
    final_odds: Optional[str] = None

class BettingPoolResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    bet_type: str
    pool_total: Optional[Decimal] = None
    winning_combination: Optional[str] = None
    payout: Optional[Decimal] = None

class DashboardResponse(BaseModel):
    total_races_today: int
    total_horses: int
    total_drivers: int
    total_trainers: int
    recent_races: List[RaceResponse]
    top_horses: List[Dict[str, Any]]
    top_drivers: List[Dict[str, Any]]
    top_trainers: List[Dict[str, Any]]

class TopPerformersResponse(BaseModel):
    category: str
    metric: str
    performers: List[Dict[str, Any]]

class TrendsResponse(BaseModel):
    period: str
    data: List[Dict[str, Any]]

class DataStatusResponse(BaseModel):
    last_fetch: Optional[datetime] = None
    total_races: int
    total_horses: int
    total_drivers: int
    total_trainers: int
    data_freshness: str  # fresh, stale, outdated