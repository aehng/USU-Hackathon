from datetime import timedelta
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import select

from models.models import Entry

def get_user_entries(db: Session, user_id: str):
    return db.query(Entry).filter(Entry.user_id == user_id).order_by(Entry.logged_at.asc()).all()

def compute_trigger_correlation(entries: list[Entry]) -> list[dict]:
    """
    Finds the most common triggers mentioned preceding any symptoms within 24 hours.
    Returns: list of {name, value} for Max's Recharts BarChart.
    """
    if not entries or len(entries) < 5:
        return []

    trigger_counts = defaultdict(int)

    for i, current_entry in enumerate(entries):
        if not current_entry.symptoms:
            continue
            
        # Look back at previous entries within 24 hours
        seen_triggers_for_this_symptom = set()
        j = i - 1
        while j >= 0:
            prev_entry = entries[j]
            time_diff = current_entry.logged_at - prev_entry.logged_at
            
            if time_diff > timedelta(hours=24):
                break
                
            if prev_entry.potential_triggers:
                for trigger in prev_entry.potential_triggers:
                    seen_triggers_for_this_symptom.add(trigger)
            j -= 1
            
        if current_entry.potential_triggers:
            for trigger in current_entry.potential_triggers:
                seen_triggers_for_this_symptom.add(trigger)
                
        for trigger in seen_triggers_for_this_symptom:
            trigger_counts[trigger] += 1

    results = []
    for trigger, count in trigger_counts.items():
        if count >= 3: 
            results.append({
                "name": trigger,
                "value": count
            })

    results.sort(key=lambda x: x["value"], reverse=True)
    return results[:5]

def compute_temporal_patterns(entries: list[Entry]) -> list[dict]:
    """
    Groups entries by day-of-week and time of day ('time_context' field).
    Finds if certain symptoms cluster on specific days or times.
    """
    if not entries or len(entries) < 5:
        return []

    symptom_day_counts = defaultdict(lambda: defaultdict(int))
    symptom_time_counts = defaultdict(lambda: defaultdict(int))
    symptom_totals = defaultdict(int)

    for entry in entries:
        if not entry.symptoms:
            continue
            
        day_of_week = entry.logged_at.strftime("%A") # "Monday", "Tuesday"
        time_context = entry.time_context
        
        for symptom in entry.symptoms:
            symptom_totals[symptom] += 1
            symptom_day_counts[symptom][day_of_week] += 1
            if time_context:
                symptom_time_counts[symptom][time_context] += 1

    results = []
    for symptom, total_count in symptom_totals.items():
        if total_count < 4:
            continue
            
        days = symptom_day_counts[symptom]
        times = symptom_time_counts[symptom]
        
        peak_day, peak_day_count = max(days.items(), key=lambda x: x[1], default=(None, 0))
        peak_time, peak_time_count = max(times.items(), key=lambda x: x[1], default=(None, 0))
        
        has_pattern = False
        if peak_day_count / total_count > 0.50 or peak_time_count / total_count > 0.50:
            has_pattern = True
            
        if has_pattern:
            results.append({
                "symptom": symptom,
                "peak_day": peak_day if peak_day_count / total_count > 0.40 else None,
                "peak_time": peak_time if peak_time_count / total_count > 0.40 else None,
                "frequency": total_count
            })

    return results

def compute_severity_trends(entries: list[Entry]) -> list[dict]:
    """
    Returns an array of daily severity averages for the last 7 days 
    in the format {"date": "YYYY-MM-DD", "severity": N} for Max's LineChart.
    """
    if not entries:
        return []

    daily_severities = defaultdict(list)
    
    for entry in entries:
        if entry.severity is not None:
            date_str = entry.logged_at.strftime("%Y-%m-%d")
            daily_severities[date_str].append(entry.severity)
            
    results = []
    for date_str in sorted(daily_severities.keys()):
        severities = daily_severities[date_str]
        avg_severity = round(sum(severities) / len(severities), 1)
        results.append({
            "date": date_str,
            "severity": avg_severity
        })
        
    return results[-7:]

def compute_symptom_frequency(entries: list[Entry]) -> list[dict]:
    """
    Counts total occurrences of each symptom.
    Returns: list of {name, value} for Max's Recharts PieChart.
    """
    symptom_counts = defaultdict(int)
    
    for entry in entries:
        if entry.symptoms:
            for symptom in entry.symptoms:
                symptom_counts[symptom] += 1
                
    results = []
    for symptom, count in symptom_counts.items():
        results.append({
            "name": symptom,
            "value": count
        })
        
    results.sort(key=lambda x: x["value"], reverse=True)
    return results[:5]

def compute_all_stats(user_id: str, db: Session) -> dict:
    """
    Master function to call all analysis functions and combine their output.
    """
    entries = get_user_entries(db, user_id)
    
    if not entries:
        return {"message": "Insufficient data", "total_entries": 0}
        
    date_range_days = (entries[-1].logged_at - entries[0].logged_at).days if len(entries) > 1 else 0
    
    if len(entries) < 5:
        return {
            "message": "Insufficient data", 
            "total_entries": len(entries),
            "date_range_days": date_range_days
        }

    return {
        "trigger_correlations": compute_trigger_correlation(entries),
        "temporal_patterns": compute_temporal_patterns(entries),
        "severity_trends": compute_severity_trends(entries),
        "symptom_frequency": compute_symptom_frequency(entries),
        "total_entries": len(entries),
        "date_range_days": date_range_days
    }
