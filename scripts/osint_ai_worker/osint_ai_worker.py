import logging
from apscheduler.schedulers.background import BackgroundScheduler
import time
import os
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_signal_extraction():
    logger.info("Running signal extraction job...")
    # TODO: Connect to DB, fetch un processed news, pass to gemini_client, save to signals table

def run_thesis_update():
    logger.info("Running thesis update job...")
    # TODO: Fetch recent signals, fetch current theses, pass to gemini_client, update theses

def run_world_state_update():
    logger.info("Running world state update job...")
    # TODO: Fetch world state, signals, theses, pass to gemini_client, propose changes

if __name__ == "__main__":
    logger.info("Starting OSINT AI Worker...")
    
    scheduler = BackgroundScheduler()
    # Run signal extraction every 10 minutes
    scheduler.add_job(run_signal_extraction, 'interval', minutes=10)
    # Run thesis update every hour
    scheduler.add_job(run_thesis_update, 'interval', hours=1)
    # Run world state update every 4 hours
    scheduler.add_job(run_world_state_update, 'interval', hours=4)
    
    scheduler.start()
    
    # Normally we would start the Pyrogram client here as well, 
    # but Pyrogram has its own event loop. We can run Pyrogram in the main thread.
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    try:
        from collectors.telegram_scraper import start_scraping
        start_scraping()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Shutting down...")
