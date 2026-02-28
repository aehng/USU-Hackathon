import random
import uuid
from datetime import datetime, timedelta
import pytz

# Add the parent directory to the path so we can import from the backend module
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from database import SessionLocal
    from models.models import User, Entry, TriggerTaxonomy
except ImportError:
    from backend.database import SessionLocal
    from backend.models.models import User, Entry, TriggerTaxonomy

# Constants
DEMO_USER_ID = "00000000-0000-0000-0000-000000000001"
DAYS_OF_DATA = 30
TIMEZONE = pytz.timezone("US/Mountain")

def get_random_time(date, time_period):
    if time_period == "morning":
        hour = random.randint(6, 11)
    elif time_period == "afternoon":
        hour = random.randint(12, 16)
    elif time_period == "evening":
        hour = random.randint(17, 21)
    else:  # night
        hour = random.randint(22, 23)
        
    minute = random.randint(0, 59)
    dt = datetime(date.year, date.month, date.day, hour, minute)
    return TIMEZONE.localize(dt)

def generate_entries():
    start_date = datetime.now() - timedelta(days=DAYS_OF_DATA)
    entries_data = []
    
    # Track states to apply rules
    had_caffeine_yesterday = False
    had_poor_sleep_yesterday = False
    had_alcohol_yesterday = False

    for day_offset in range(DAYS_OF_DATA):
        current_date = start_date + timedelta(days=day_offset)
        
        # Daily decisions
        has_caffeine = random.random() < 0.6  # 60% chance of caffeine
        has_poor_sleep = random.random() < 0.3  # 30% chance of poor sleep
        has_stress = random.random() < 0.4  # 40% chance of stress
        has_alcohol = random.random() < 0.2  # 20% chance of alcohol
        
        # --- Morning Entry ---
        morning_symptoms = []
        morning_triggers = []
        morning_mood = random.choice(["okay", "good", "tired", "groggy"])
        morning_transcript = "Woke up feeling alright."
        
        if had_poor_sleep_yesterday and random.random() < 0.80:
            morning_symptoms.append("fatigue")
            morning_transcript = "I'm so exhausted this morning, barely slept."
            morning_mood = "exhausted"
            
        if had_alcohol_yesterday and random.random() < 0.85:
            morning_symptoms.append("headache")
            morning_transcript = "Woke up with a pounding headache."
            morning_mood = "awful"

        if has_caffeine:
            morning_triggers.append("caffeine")
            if "headache" not in morning_symptoms:
                morning_transcript += " Having my morning coffee."
            
        if morning_symptoms or morning_triggers:
            entries_data.append(Entry(
                user_id=DEMO_USER_ID,
                raw_transcript=morning_transcript,
                symptoms=morning_symptoms,
                severity=random.randint(4, 9) if morning_symptoms else random.randint(1, 3),
                potential_triggers=morning_triggers,
                mood=morning_mood,
                body_location=["head"] if "headache" in morning_symptoms else [],
                time_context="morning",
                notes="",
                logged_at=get_random_time(current_date, "morning")
            ))

        # --- Afternoon/Evening Entry ---
        afternoon_symptoms = []
        afternoon_triggers = []
        afternoon_mood = random.choice(["okay", "stressed", "fine"])
        afternoon_transcript = "Just getting through the day."
        
        if had_caffeine_yesterday and random.random() < 0.75:
            afternoon_symptoms.append("headache")
            afternoon_transcript = "Got this nagging headache."
            
        if has_stress:
            afternoon_triggers.append("stress")
            if random.random() < 0.65:
                afternoon_symptoms.append("stomach ache")
                afternoon_transcript = "So stressed out and my stomach is in knots."
                afternoon_mood = "stressed"
            else:
                afternoon_transcript = "Really stressful day at work."
                
        if has_alcohol:
            afternoon_triggers.append("alcohol")
            afternoon_transcript += " Having a drink to unwind."
            
        if has_poor_sleep:
            afternoon_triggers.append("poor sleep")
            
        if afternoon_symptoms or afternoon_triggers:
            entries_data.append(Entry(
                user_id=DEMO_USER_ID,
                raw_transcript=afternoon_transcript,
                symptoms=afternoon_symptoms,
                severity=random.randint(4, 8) if afternoon_symptoms else random.randint(1, 3),
                potential_triggers=afternoon_triggers,
                mood=afternoon_mood,
                body_location=["stomach"] if "stomach ache" in afternoon_symptoms else (["head"] if "headache" in afternoon_symptoms else []),
                time_context=random.choice(["afternoon", "evening"]),
                notes="",
                logged_at=get_random_time(current_date, random.choice(["afternoon", "evening"]))
            ))
            
        # Update yesterday flags for tomorrow
        had_caffeine_yesterday = has_caffeine
        had_poor_sleep_yesterday = has_poor_sleep
        had_alcohol_yesterday = has_alcohol

    return entries_data

def seed_database():
    print("Starting database seed...")
    db = SessionLocal()
    try:
        # Clear existing entries and taxonomy for demo user
        db.query(Entry).filter(Entry.user_id == DEMO_USER_ID).delete()
        db.query(TriggerTaxonomy).filter(TriggerTaxonomy.user_id == DEMO_USER_ID).delete()
        db.commit()
        
        # Populate Taxonomy mapping demo
        taxonomies = [
            TriggerTaxonomy(user_id=DEMO_USER_ID, raw_trigger="coffee", root_cause="Caffeine"),
            TriggerTaxonomy(user_id=DEMO_USER_ID, raw_trigger="monster energy", root_cause="Caffeine"),
            TriggerTaxonomy(user_id=DEMO_USER_ID, raw_trigger="red bull", root_cause="Caffeine"),
            TriggerTaxonomy(user_id=DEMO_USER_ID, raw_trigger="latte", root_cause="Caffeine"),
            TriggerTaxonomy(user_id=DEMO_USER_ID, raw_trigger="beer", root_cause="Alcohol"),
            TriggerTaxonomy(user_id=DEMO_USER_ID, raw_trigger="wine", root_cause="Alcohol"),
            TriggerTaxonomy(user_id=DEMO_USER_ID, raw_trigger="traffic", root_cause="Stress"),
            TriggerTaxonomy(user_id=DEMO_USER_ID, raw_trigger="work", root_cause="Stress"),
            TriggerTaxonomy(user_id=DEMO_USER_ID, raw_trigger="late night", root_cause="Lack Of Sleep")
        ]
        db.add_all(taxonomies)
        
        # Generate and insert new entries
        entries = generate_entries()
        db.add_all(entries)
        db.commit()
        
        print(f"Successfully seeded {len(entries)} entries for demo user.")
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
