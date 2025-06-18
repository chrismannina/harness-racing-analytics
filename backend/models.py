from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Boolean, Text, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Track(Base):
    __tablename__ = "tracks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    location = Column(String(100), nullable=False)
    surface = Column(String(20), default="dirt")  # dirt, synthetic, etc.
    circumference = Column(Float)  # in meters
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    races = relationship("Race", back_populates="track")

class Horse(Base):
    __tablename__ = "horses"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    registration_number = Column(String(50), unique=True, index=True)
    foaling_date = Column(Date)
    sex = Column(String(10))  # stallion, mare, gelding, colt, filly
    color = Column(String(20))
    sire = Column(String(100))
    dam = Column(String(100))
    breeder = Column(String(100))
    owner = Column(String(100))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    race_entries = relationship("RaceEntry", back_populates="horse")

class Driver(Base):
    __tablename__ = "drivers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    license_number = Column(String(50), unique=True)
    birth_date = Column(Date)
    hometown = Column(String(100))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    race_entries = relationship("RaceEntry", back_populates="driver")

class Trainer(Base):
    __tablename__ = "trainers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    license_number = Column(String(50), unique=True)
    birth_date = Column(Date)
    hometown = Column(String(100))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    race_entries = relationship("RaceEntry", back_populates="trainer")

class Race(Base):
    __tablename__ = "races"
    
    id = Column(Integer, primary_key=True, index=True)
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=False)
    race_number = Column(Integer, nullable=False)
    race_date = Column(Date, nullable=False, index=True)
    post_time = Column(DateTime)
    distance = Column(Integer)  # in meters
    purse = Column(Numeric(10, 2))
    race_type = Column(String(50))  # claiming, allowance, stakes, etc.
    conditions = Column(Text)
    track_condition = Column(String(20))  # fast, good, sloppy, etc.
    weather = Column(String(50))
    temperature = Column(Float)
    status = Column(String(20), default="scheduled")  # scheduled, running, finished, cancelled
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    track = relationship("Track", back_populates="races")
    entries = relationship("RaceEntry", back_populates="race")

class RaceEntry(Base):
    __tablename__ = "race_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=False)
    horse_id = Column(Integer, ForeignKey("horses.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    trainer_id = Column(Integer, ForeignKey("trainers.id"), nullable=False)
    post_position = Column(Integer, nullable=False)
    program_number = Column(String(10))
    morning_line_odds = Column(String(10))
    final_odds = Column(String(10))
    finish_position = Column(Integer)
    finish_time = Column(String(20))  # MM:SS.ff format
    margin = Column(String(20))  # winning margin
    earnings = Column(Numeric(10, 2))
    scratched = Column(Boolean, default=False)
    disqualified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    race = relationship("Race", back_populates="entries")
    horse = relationship("Horse", back_populates="race_entries")
    driver = relationship("Driver", back_populates="race_entries")
    trainer = relationship("Trainer", back_populates="race_entries")

class BettingPool(Base):
    __tablename__ = "betting_pools"
    
    id = Column(Integer, primary_key=True, index=True)
    race_id = Column(Integer, ForeignKey("races.id"), nullable=False)
    bet_type = Column(String(20), nullable=False)  # win, place, show, exacta, trifecta, etc.
    pool_total = Column(Numeric(12, 2))
    winning_combination = Column(String(50))
    payout = Column(Numeric(10, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    race = relationship("Race")

class DataFetch(Base):
    __tablename__ = "data_fetches"
    
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(100), nullable=False)
    fetch_type = Column(String(50), nullable=False)  # races, results, entries, etc.
    fetch_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False)  # success, failed, partial
    records_processed = Column(Integer, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))