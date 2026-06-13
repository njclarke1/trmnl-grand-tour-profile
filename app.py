"""
TRMNL Grand Tour Stage Profile — API Server
Serves current/next cycling grand tour stage profile data for LaraPaper.
"""

import json
import os
from datetime import date
from pathlib import Path

from flask import Flask, jsonify, send_from_directory

app = Flask(__name__)

DATA_DIR = os.environ.get("DATA_DIR", "/data")
IMAGES_DIR = os.environ.get("IMAGES_DIR", "/images")
BASE_URL = os.environ.get("BASE_URL", "http://localhost:5000").rstrip("/")


def load_schedules():
    """Load all tour schedule JSONs from the data directory, recursively."""
    schedules = []
    data_path = Path(DATA_DIR)
    if not data_path.exists():
        return schedules
    for json_file in sorted(data_path.rglob("*.json")):
        with open(json_file) as f:
            schedules.append(json.load(f))
    return schedules


def build_stage_list(schedules):
    """Flatten all schedules into a sorted list of stage dicts."""
    stages = []
    for sched in schedules:
        tour = sched["tour"]
        short = sched["short"]
        year = sched["year"]
        for st in sched["stages"]:
            stages.append({
                "tour": tour,
                "short": short,
                "year": year,
                "stage": st["stage"],
                "date": st["date"],
                "parsed_date": date.fromisoformat(st["date"]),
                "start": st.get("start", ""),
                "finish": st.get("finish", ""),
                "type": st.get("type", ""),
                "distance_km": st.get("distance_km", 0),
                "image": st["image"],
            })
    stages.sort(key=lambda s: (s["parsed_date"], s["stage"]))
    return stages


def make_response(status, stage, countdown_days=None, include_image=True):
    """Build a consistent API response dict from a stage record."""
    image_url = None
    if include_image and stage.get("image"):
        image_url = f"{BASE_URL}/images/{stage['year']}/{stage['short']}/{stage['image']}"
    return {
        "status": status,
        "tour": stage["tour"],
        "short": stage["short"],
        "year": stage["year"],
        "stage": stage["stage"],
        "date": stage["date"],
        "start": stage["start"],
        "finish": stage["finish"],
        "type": stage["type"],
        "distance_km": stage["distance_km"],
        "image_url": image_url,
        "countdown_days": countdown_days,
    }


def get_current_stage():
    """Core logic: determine which stage to display today."""
    today = date.today()
    schedules = load_schedules()

    if not schedules:
        return {"status": "no_data", "message": "No schedule files found in data directory."}

    stages = build_stage_list(schedules)

    if not stages:
        return {"status": "no_data", "message": "Schedule files contain no stages."}

    # 1. Stage today → show it
    for s in stages:
        if s["parsed_date"] == today:
            return make_response("live", s, countdown_days=0)

    # 2. Find next future stage
    future = [s for s in stages if s["parsed_date"] > today]

    if not future:
        return {
            "status": "off_season",
            "tour": None,
            "message": "All scheduled tours have finished. Add next year's data.",
            "countdown_days": None,
            "image_url": None,
        }

    next_stage = future[0]
    days_until = (next_stage["parsed_date"] - today).days

    # 3. Rest day during an active tour?
    #    If there's a completed stage from the same tour AND next stage is ≤3 days away
    past_same_tour = [
        s for s in stages
        if s["short"] == next_stage["short"]
        and s["year"] == next_stage["year"]
        and s["parsed_date"] < today
    ]
    if past_same_tour and days_until <= 3:
        return make_response("rest_day", next_stage, countdown_days=days_until)

    # 4. Find stage 1 of the next upcoming tour
    stage_1 = next(
        (s for s in stages
         if s["short"] == next_stage["short"]
         and s["year"] == next_stage["year"]
         and s["stage"] == 1),
        next_stage,
    )
    days_until_tour = (stage_1["parsed_date"] - today).days

    # 5. ≤7 days to tour start → show stage 1 profile
    if 0 < days_until_tour <= 7:
        return make_response("upcoming", stage_1, countdown_days=days_until_tour)

    # 6. Countdown mode
    return make_response("countdown", stage_1, countdown_days=days_until_tour, include_image=False)


# --- Routes ---

@app.route("/api/stage")
def api_stage():
    try:
        return jsonify(get_current_stage())
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/images/<path:filepath>")
def serve_image(filepath):
    return send_from_directory(IMAGES_DIR, filepath)


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
