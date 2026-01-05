"""
NHL Shots Betting Analysis API

FastAPI backend to expose betting predictions and historical results.
"""
import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import ALLOWED_ORIGINS
from .routers import health, predictions, results, stats, players, lineups, auth, ai_summaries

# Configure logging to output to stdout (required for Railway)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="NHL Shots Betting API",
    description="API for NHL player shots betting predictions and results",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(predictions.router)
app.include_router(results.router)
app.include_router(stats.router)
app.include_router(players.router)
app.include_router(lineups.router)
app.include_router(auth.router)
app.include_router(ai_summaries.router)


@app.on_event("startup")
async def startup_event():
    """Log app startup"""
    logger.info("="*50)
    logger.info("🚀 NHL Shots Betting API Starting Up")
    logger.info("="*50)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)