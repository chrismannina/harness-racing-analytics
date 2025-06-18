# Ontario Harness Racing Analytics Suite

A comprehensive analytics platform for harness racing in Ontario, Canada, featuring real-time data, performance analytics, and betting insights.

## Features

- **Real-time Race Data**: Live updates from Ontario harness racing tracks
- **Performance Analytics**: Detailed statistics for horses, drivers, and trainers
- **Track Analysis**: Performance metrics by track conditions and distance
- **Betting Insights**: Odds analysis and payout predictions
- **Historical Data**: Complete race history and trend analysis
- **Interactive Dashboard**: Modern web interface with charts and visualizations

## Architecture

- **Backend**: FastAPI with PostgreSQL database
- **Frontend**: React with TypeScript and modern UI components
- **Data Pipeline**: Automated data fetching from racing sources
- **Analytics Engine**: Statistical analysis and machine learning models

## Quick Start

1. Install dependencies: `./scripts/setup.sh`
2. Start the database: `docker-compose up -d postgres`
3. Run migrations: `cd backend && python -m alembic upgrade head`
4. Start the API: `cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000`
5. Start the frontend: `cd frontend && npm start`

## API Endpoints

- `/api/races` - Race data and results
- `/api/horses` - Horse profiles and statistics
- `/api/drivers` - Driver performance metrics
- `/api/trainers` - Trainer statistics
- `/api/tracks` - Track information and conditions
- `/api/analytics` - Advanced analytics and predictions

## Data Sources

- Woodbine Mohawk Park
- Ontario Racing Commission
- Standardbred Canada
- Track-specific APIs and feeds