from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn
from datetime import datetime, date
import logging

from database import get_db, engine
from models import Base
from schemas import *
from services.race_service import RaceService
from services.horse_service import HorseService
from services.driver_service import DriverService
from services.trainer_service import TrainerService
from services.analytics_service import AnalyticsService
from services.data_fetcher import DataFetcher

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Ontario Harness Racing Analytics API",
    description="Comprehensive analytics API for harness racing in Ontario, Canada",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
race_service = RaceService()
horse_service = HorseService()
driver_service = DriverService()
trainer_service = TrainerService()
analytics_service = AnalyticsService()
data_fetcher = DataFetcher()

@app.get("/")
async def root():
    return {"message": "Ontario Harness Racing Analytics API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

# Race endpoints
@app.get("/api/races", response_model=List[RaceResponse])
async def get_races(
    date: Optional[date] = Query(None, description="Filter by race date"),
    track_id: Optional[int] = Query(None, description="Filter by track"),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db)
):
    """Get races with optional filtering"""
    return race_service.get_races(db, date=date, track_id=track_id, limit=limit)

@app.get("/api/races/{race_id}", response_model=RaceDetailResponse)
async def get_race(race_id: int, db: Session = Depends(get_db)):
    """Get detailed race information"""
    race = race_service.get_race_by_id(db, race_id)
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")
    return race

@app.get("/api/races/today", response_model=List[RaceResponse])
async def get_today_races(db: Session = Depends(get_db)):
    """Get today's races"""
    return race_service.get_races(db, date=date.today())

@app.get("/api/races/{race_id}/results", response_model=List[RaceResultResponse])
async def get_race_results(race_id: int, db: Session = Depends(get_db)):
    """Get race results"""
    return race_service.get_race_results(db, race_id)

# Horse endpoints
@app.get("/api/horses", response_model=List[HorseResponse])
async def get_horses(
    name: Optional[str] = Query(None, description="Search by horse name"),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db)
):
    """Get horses with optional name search"""
    return horse_service.get_horses(db, name=name, limit=limit)

@app.get("/api/horses/{horse_id}", response_model=HorseDetailResponse)
async def get_horse(horse_id: int, db: Session = Depends(get_db)):
    """Get detailed horse information"""
    horse = horse_service.get_horse_by_id(db, horse_id)
    if not horse:
        raise HTTPException(status_code=404, detail="Horse not found")
    return horse

@app.get("/api/horses/{horse_id}/stats", response_model=HorseStatsResponse)
async def get_horse_stats(horse_id: int, db: Session = Depends(get_db)):
    """Get horse performance statistics"""
    return horse_service.get_horse_stats(db, horse_id)

@app.get("/api/horses/{horse_id}/races", response_model=List[RaceResultResponse])
async def get_horse_races(horse_id: int, limit: int = Query(20, le=50), db: Session = Depends(get_db)):
    """Get horse's race history"""
    return horse_service.get_horse_races(db, horse_id, limit)

# Driver endpoints
@app.get("/api/drivers", response_model=List[DriverResponse])
async def get_drivers(
    name: Optional[str] = Query(None, description="Search by driver name"),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db)
):
    """Get drivers with optional name search"""
    return driver_service.get_drivers(db, name=name, limit=limit)

@app.get("/api/drivers/{driver_id}", response_model=DriverDetailResponse)
async def get_driver(driver_id: int, db: Session = Depends(get_db)):
    """Get detailed driver information"""
    driver = driver_service.get_driver_by_id(db, driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver

@app.get("/api/drivers/{driver_id}/stats", response_model=DriverStatsResponse)
async def get_driver_stats(driver_id: int, db: Session = Depends(get_db)):
    """Get driver performance statistics"""
    return driver_service.get_driver_stats(db, driver_id)

# Trainer endpoints
@app.get("/api/trainers", response_model=List[TrainerResponse])
async def get_trainers(
    name: Optional[str] = Query(None, description="Search by trainer name"),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db)
):
    """Get trainers with optional name search"""
    return trainer_service.get_trainers(db, name=name, limit=limit)

@app.get("/api/trainers/{trainer_id}", response_model=TrainerDetailResponse)
async def get_trainer(trainer_id: int, db: Session = Depends(get_db)):
    """Get detailed trainer information"""
    trainer = trainer_service.get_trainer_by_id(db, trainer_id)
    if not trainer:
        raise HTTPException(status_code=404, detail="Trainer not found")
    return trainer

@app.get("/api/trainers/{trainer_id}/stats", response_model=TrainerStatsResponse)
async def get_trainer_stats(trainer_id: int, db: Session = Depends(get_db)):
    """Get trainer performance statistics"""
    return trainer_service.get_trainer_stats(db, trainer_id)

# Track endpoints
@app.get("/api/tracks", response_model=List[TrackResponse])
async def get_tracks(db: Session = Depends(get_db)):
    """Get all tracks"""
    return race_service.get_tracks(db)

@app.get("/api/tracks/{track_id}", response_model=TrackDetailResponse)
async def get_track(track_id: int, db: Session = Depends(get_db)):
    """Get detailed track information"""
    track = race_service.get_track_by_id(db, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return track

# Analytics endpoints
@app.get("/api/analytics/dashboard", response_model=DashboardResponse)
async def get_dashboard_data(db: Session = Depends(get_db)):
    """Get dashboard analytics data"""
    return analytics_service.get_dashboard_data(db)

@app.get("/api/analytics/top-performers", response_model=TopPerformersResponse)
async def get_top_performers(
    category: str = Query("horses", regex="^(horses|drivers|trainers)$"),
    metric: str = Query("wins", regex="^(wins|earnings|win_rate)$"),
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db)
):
    """Get top performers by category and metric"""
    return analytics_service.get_top_performers(db, category, metric, limit)

@app.get("/api/analytics/trends", response_model=TrendsResponse)
async def get_trends(
    period: str = Query("month", regex="^(week|month|quarter|year)$"),
    db: Session = Depends(get_db)
):
    """Get performance trends over time"""
    return analytics_service.get_trends(db, period)

# Data management endpoints
@app.post("/api/data/fetch")
async def fetch_latest_data(db: Session = Depends(get_db)):
    """Manually trigger data fetching"""
    try:
        result = await data_fetcher.fetch_latest_data(db)
        return {"message": "Data fetch completed", "result": result}
    except Exception as e:
        logger.error(f"Data fetch failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Data fetch failed: {str(e)}")

@app.get("/api/data/status")
async def get_data_status(db: Session = Depends(get_db)):
    """Get data freshness and status"""
    return data_fetcher.get_data_status(db)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )