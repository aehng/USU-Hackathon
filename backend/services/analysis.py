from datetime import timedelta
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import select

from models.models import Entry

def get_user_entries(db: Session, user_id: str):
    return db.query(Entry).filter(Entry.user_id == user_id).order_by(Entry.logged_at.asc()).all()

def compute_trigger_correlation(entries: list[Entry]) -> list[dict]:
    """
    For each symptom, finds what triggers appeared in entries within the preceding 24 hours.
    Returns: list of {symptom, trigger, score (0-1), sample_size}
    """
    if not entries or len(entries) < 5:
        return []

    # Map of symptom -> trigger -> count of times trigger preceded symptom within 24h
    symptom_trigger_counts = defaultdict(lambda: defaultdict(int))
    # Count of total times a symptom appeared (for calculating percentage/score)
    symptom_total_counts = defaultdict(int)

    for i, current_entry in enumerate(entries):
        if not current_entry.symptoms:
            continue
            
        for symptom in current_entry.symptoms:
            symptom_total_counts[symptom] += 1
            
            # Look back at previous entries within 24 hours
            seen_triggers_for_this_symptom = set()
            j = i - 1
            while j >= 0:
                prev_entry = entries[j]
                time_diff = current_entry.logged_at - prev_entry.logged_at
                
                # We only care about triggers within the last 24 hours
                if time_diff > timedelta(hours=24):
                    break
                    
                if prev_entry.potential_triggers:
                    for trigger in prev_entry.potential_triggers:
                        seen_triggers_for_this_symptom.add(trigger)
                j -= 1
                
            # Current entry triggers count as "preceding 24 hours" too (e.g. "drank coffee and have a headache now")
            if current_entry.potential_triggers:
                for trigger in current_entry.potential_triggers:
                    seen_triggers_for_this_symptom.add(trigger)
                    
            for trigger in seen_triggers_for_this_symptom:
                symptom_trigger_counts[symptom][trigger] += 1

    results = []
    for symptom, triggers in symptom_trigger_counts.items():
        total_occurrences = symptom_total_counts[symptom]
        
        # We only want statistically relevant data
        if total_occurrences < 5:
            continue
            
        for trigger, count in triggers.items():
            # Only report if this specific trigger-symptom pair has happened enough times to not just be noise
            if count >= 3: 
                score = round(count / total_occurrences, 2)
                # Only surface strong correlations (>40% of the time)
                if score >= 0.40:
                    results.append({
                        "symptom": symptom,
                        "trigger": trigger,
                        "score": score,
                        "sample_size": count
                    })

    # Sort by highest correlation score
    results.sort(key=lambda x: x["score"], reverse=True)
    return results

def compute_temporal_patterns(entries: list[Entry]) -> list[dict]:
    """
    Groups entries by day-of-week and time of day ('time_context' field).
    Finds if certain symptoms cluster on specific days or times.
    Returns: list of {symptom, peak_day, peak_time, frequency}
    """
    if not entries or len(entries) < 5:
        return []

    # Map of symptom -> day of week -> count
    symptom_day_counts = defaultdict(lambda: defaultdict(int))
    # Map of symptom -> time of day -> count
    symptom_time_counts = defaultdict(lambda: defaultdict(int))
    # Total count for percentage
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
        
        # Find peak day
        peak_day, peak_day_count = max(days.items(), key=lambda x: x[1], default=(None, 0))
        # Find peak time
        peak_time, peak_time_count = max(times.items(), key=lambda x: x[1], default=(None, 0))
        
        has_pattern = False
        # If >50% of the occurrences are on the same day or same time of day
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
    For major symptoms, pulls the severity scores over time.
    Fits a simple linear regression.
    Returns: {symptom, trend ("improving"/"worsening"/"stable"), slope, data_points}
    """
    if not entries or len(entries) < 5:
        return []

    # Map of symptom -> list of (timestamp_offset_hours, severity)
    symptom_severities = defaultdict(list)
    base_time = entries[0].logged_at

    for entry in entries:
        if not entry.symptoms or entry.severity is None:
            continue
            
        hours_since_start = (entry.logged_at - base_time).total_seconds() / 3600
        
        for symptom in entry.symptoms:
            symptom_severities[symptom].append((hours_since_start, entry.severity))

    results = []
    for symptom, data in symptom_severities.items():
        if len(data) < 5:
            continue
            
        # Linear Regression (Least Squares)
        n = len(data)
        sum_x = sum(point[0] for point in data)
        sum_y = sum(point[1] for point in data)
        sum_xy = sum(point[0] * point[1] for point in data)
        sum_xx = sum(point[0] ** 2 for point in data)
        
        # Calculate slope (m)
        denominator = (n * sum_xx - sum_x ** 2)
        if denominator == 0:
            slope = 0
        else:
            slope = (n * sum_xy - sum_x * sum_y) / denominator
            
        # Determine trend string (slope > 0 = worsening, slope < 0 = improving)
        if slope > 0.005:  # Slight threshold to avoid "worsening" on basically flat lines
            trend = "worsening"
        elif slope < -0.005:
            trend = "improving"
        else:
            trend = "stable"
            
        results.append({
            "symptom": symptom,
            "trend": trend,
            "slope": round(slope, 5),
            "data_points": n
        })

    return results

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
        "total_entries": len(entries),
        "date_range_days": date_range_days
    }
