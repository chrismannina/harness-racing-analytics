#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from database import SessionLocal
from services.analytics_service import AnalyticsService

def test_dashboard():
    db = SessionLocal()
    try:
        analytics_service = AnalyticsService()
        print("Testing dashboard data generation...")
        
        # Test each component individually
        print("Testing race service...")
        total_races_today = analytics_service.race_service.get_today_race_count(db)
        print(f"Today's races: {total_races_today}")
        
        print("Testing horse service...")
        total_horses = analytics_service.horse_service.get_total_horses(db)
        print(f"Total horses: {total_horses}")
        
        print("Testing driver service...")
        total_drivers = analytics_service.driver_service.get_total_drivers(db)
        print(f"Total drivers: {total_drivers}")
        
        print("Testing trainer service...")
        total_trainers = analytics_service.trainer_service.get_total_trainers(db)
        print(f"Total trainers: {total_trainers}")
        
        print("Testing recent races...")
        recent_races = analytics_service.race_service.get_recent_races(db, limit=5)
        print(f"Recent races: {len(recent_races)}")
        
        print("Testing top horses...")
        top_horses = analytics_service.get_top_horses_by_wins(db, limit=5)
        print(f"Top horses: {len(top_horses)}")
        
        print("Testing top drivers...")
        top_drivers = analytics_service.driver_service.get_top_drivers_by_wins(db, limit=5)
        print(f"Top drivers: {len(top_drivers)}")
        
        print("Testing top trainers...")
        top_trainers = analytics_service.trainer_service.get_top_trainers_by_wins(db, limit=5)
        print(f"Top trainers: {len(top_trainers)}")
        
        print("Testing full dashboard...")
        dashboard_data = analytics_service.get_dashboard_data(db)
        print(f"Dashboard data created successfully: {dashboard_data}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_dashboard() 