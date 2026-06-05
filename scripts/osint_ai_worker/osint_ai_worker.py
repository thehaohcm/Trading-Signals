import logging
from apscheduler.schedulers.background import BackgroundScheduler
import time
import os
import sys
import uuid
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_signal_extraction():
    logger.info("Running signal extraction job...")
    try:
        from agents.gemini_client import extract_signals
        db_url = os.getenv("DATABASE_URL")
        if not db_url: return
            
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # Lấy các tin tức chưa có signal
        cur.execute("""
            SELECT id, title, content 
            FROM news_items 
            WHERE id NOT IN (SELECT source_news_id FROM osint_signals)
            AND status = 'active'
            ORDER BY created_at DESC LIMIT 20
        """)
        rows = cur.fetchall()
        
        for r in rows:
            news_id, title, content = r
            text = f"Title: {title}\nContent: {content}"
            result = extract_signals(text)
            if result and "signals" in result:
                for s in result["signals"]:
                    s_id = str(uuid.uuid4())
                    cat = s.get("category", "General")
                    sig = s.get("signal", "")
                    conf = float(s.get("confidence", 0.5))
                    reason = s.get("reason", "")
                    
                    cur.execute(
                        "INSERT INTO osint_signals (id, source_news_id, category, signal, confidence, reason) VALUES (%s, %s, %s, %s, %s, %s)",
                        (s_id, news_id, cat, sig, conf, reason)
                    )
        conn.commit()
        cur.close()
        conn.close()
        logger.info("Successfully extracted signals.")
    except Exception as e:
        logger.error(f"Error in run_signal_extraction: {e}")

def run_thesis_update():
    logger.info("Running thesis update job...")
    try:
        from agents.gemini_client import generate_thesis
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            logger.error("DATABASE_URL not found")
            return
            
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # Lấy 50 tin tức mới nhất có status active
        cur.execute("SELECT title, content FROM news_items WHERE status = 'active' ORDER BY created_at DESC LIMIT 50")
        rows = cur.fetchall()
        
        if not rows:
            logger.info("No active news found to generate thesis.")
            cur.close()
            conn.close()
            return
            
        news_text = "\n".join([f"- {r[0]}: {r[1]}" for r in rows])
        
        logger.info("Generating thesis with AI...")
        result = generate_thesis(news_text)
        
        if result and "theses" in result:
            # Xóa các thesis cũ hoặc đánh dấu là 'expired'
            cur.execute("UPDATE osint_theses SET status = 'expired' WHERE status = 'active'")
            
            for t in result["theses"]:
                t_id = str(uuid.uuid4())
                thesis_text = t.get("thesis", "")
                conf = float(t.get("confidence", 0.5))
                evidence = t.get("supporting_evidence", "")
                
                cur.execute(
                    "INSERT INTO osint_theses (id, thesis, confidence, supporting_evidence, status) VALUES (%s, %s, %s, %s, %s)",
                    (t_id, thesis_text, conf, evidence, 'active')
                )
            conn.commit()
            logger.info("Successfully updated theses in DB!")
        else:
            logger.warning("Failed to generate theses from AI")
            
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Error in run_thesis_update: {e}")

def run_world_state_update():
    logger.info("Running world state update job...")
    try:
        from agents.gemini_client import propose_world_state_changes
        db_url = os.getenv("DATABASE_URL")
        if not db_url: return
            
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        cur.execute("SELECT state_json FROM osint_world_state WHERE id = 1")
        state_row = cur.fetchone()
        state_json = state_row[0] if state_row else "{}"
        
        cur.execute("SELECT category, signal, reason FROM osint_signals ORDER BY created_at DESC LIMIT 20")
        sig_rows = cur.fetchall()
        signals_text = "\n".join([f"[{r[0]}] {r[1]} - {r[2]}" for r in sig_rows])
        
        cur.execute("SELECT thesis, supporting_evidence FROM osint_theses WHERE status = 'active' LIMIT 5")
        thes_rows = cur.fetchall()
        theses_text = "\n".join([f"- {r[0]}: {r[1]}" for r in thes_rows])
        
        result = propose_world_state_changes(str(state_json), signals_text, theses_text)
        
        if result and "proposed_changes" in result:
            for p in result["proposed_changes"]:
                p_id = str(uuid.uuid4())
                tgt = p.get("target_entity", "General")
                fld = p.get("field_name", "trend")
                val = str(p.get("new_value", ""))
                conf = float(p.get("confidence", 0.5))
                reason = p.get("reason", "")
                
                cur.execute(
                    "INSERT INTO osint_proposed_changes (id, target_entity, field_name, new_value, confidence, reason, status) VALUES (%s, %s, %s, %s, %s, %s, 'pending')",
                    (p_id, tgt, fld, val, conf, reason)
                )
            conn.commit()
            logger.info("Successfully proposed world state changes!")
            
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Error in run_world_state_update: {e}")

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
    
    # Run once at startup to populate initial data
    logger.info("Running initial jobs at startup...")
    run_signal_extraction()
    run_thesis_update()
    run_world_state_update()
    
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
