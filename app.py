"""
TRMNL Grand Tour Stage Profile — API Server
Serves current/next cycling grand tour stage profile data for LaraPaper.
"""

import hashlib
import json
import os
from datetime import date
from pathlib import Path

import numpy as np
from flask import Flask, jsonify, request, send_file, send_from_directory
from PIL import Image

app = Flask(__name__)

DATA_DIR = os.environ.get("DATA_DIR", "/data")
IMAGES_DIR = os.environ.get("IMAGES_DIR", "/images")
CACHE_DIR = os.environ.get("CACHE_DIR", "/cache")
BASE_URL = os.environ.get("BASE_URL", "http://localhost:5000").rstrip("/")
FAKE_TODAY = os.environ.get("FAKE_TODAY")  # optional YYYY-MM-DD override for testing

# E-ink processing: ASO yellow elevation fill is too close to white in
# greyscale (~215/255) and disappears on 4-bit e-ink panels. Recolour it
# to mid-grey so the profile fill remains visible.
EINK_YELLOW_REPLACEMENT = (100, 100, 100)


def process_for_eink(src_path, dst_path):
    """
    Process stage profile image for e-ink display:

    1. Context-aware yellow recolouring:
       - Detects the solid black distance bar at the bottom of the image
         (the horizontal band with km markers like 5.1 / 17.3 etc.)
       - Yellow pixels within/adjacent to that bar → white (legible on black)
       - Yellow pixels elsewhere (elevation fill) → mid-grey (visible on white)
    2. Unsharp mask to sharpen fine text/line detail before e-ink dithering.
    """
    from PIL import ImageFilter

    img = Image.open(src_path).convert("RGB")
    arr = np.array(img).astype(np.float32)
    h, w = arr.shape[:2]

    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

    # Detect yellow pixels
    yellow_mask = (r > 180) & (g > 160) & (b < 150) & ((r - b) > 60) & ((g - b) > 60)

    # Find the solid black bar by scanning up from the bottom.
    # It's the lowest continuous band where >60% of pixels are dark.
    dark_mask = (r < 60) & (g < 60) & (b < 60)
    dark_per_row = dark_mask.sum(axis=1)
    bar_rows = []
    for y in range(h - 1, 0, -1):
        if dark_per_row[y] > w * 0.6:
            bar_rows.append(y)
        elif bar_rows:
            break  # stop at first non-dense-dark row scanning upward

    if bar_rows:
        # Extend 4px above bar top to catch transition/antialiased yellow pixels
        bar_top = max(0, min(bar_rows) - 4)
        bar_bottom = max(bar_rows)
    else:
        # Fallback: treat bottom 8% of image as bar zone
        bar_top = int(h * 0.92)
        bar_bottom = h

    # Build row-based mask for the bar zone
    bar_zone = np.zeros((h, w), dtype=bool)
    bar_zone[bar_top:bar_bottom + 1, :] = True

    # Apply context-aware recolouring
    arr[yellow_mask & ~bar_zone] = EINK_YELLOW_REPLACEMENT   # elevation fill → grey
    arr[yellow_mask & bar_zone] = [255, 255, 255]             # bar text → white

    img_processed = Image.fromarray(arr.astype(np.uint8))
    img_sharpened = img_processed.filter(
        ImageFilter.UnsharpMask(radius=1.5, percent=180, threshold=3)
    )
    img_sharpened.save(dst_path)


def get_eink_image_path(filepath):
    """
    Return the path to an e-ink-processed version of the requested image,
    generating and caching it on first request. Returns None if the source
    image doesn't exist.
    """
    src_path = Path(IMAGES_DIR) / filepath
    if not src_path.is_file():
        return None

    # Cache key includes source mtime so updated source images bust the cache
    mtime = int(src_path.stat().st_mtime)
    cache_key = hashlib.sha1(f"{filepath}:{mtime}".encode()).hexdigest()
    cache_path = Path(CACHE_DIR) / f"{cache_key}.png"

    if not cache_path.is_file():
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        process_for_eink(src_path, cache_path)

    return cache_path


def resolve_today(override=None):
    """
    Determine 'today' for the purposes of stage selection.

    Precedence: explicit override (query param) > FAKE_TODAY env var > real date.
    Raises ValueError if override/env value isn't a valid YYYY-MM-DD date.
    """
    if override:
        return date.fromisoformat(override)
    if FAKE_TODAY:
        return date.fromisoformat(FAKE_TODAY)
    return date.today()


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
                "start_time": st.get("start_time", ""),
                "est_finish": st.get("est_finish", ""),
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
        "start_time": stage.get("start_time", ""),
        "est_finish": stage.get("est_finish", ""),
    }


def get_current_stage(today=None):
    """Core logic: determine which stage to display today."""
    if today is None:
        today = resolve_today()
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
        override = request.args.get("date")
        today = resolve_today(override)
        result = get_current_stage(today)
        result["_today"] = today.isoformat()
        if override:
            result["_date_source"] = "query_param"
        elif FAKE_TODAY:
            result["_date_source"] = "FAKE_TODAY_env"
        else:
            result["_date_source"] = "real"
        return jsonify(result)
    except ValueError as e:
        return jsonify({"status": "error", "message": f"Invalid date: {e}"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/images/<path:filepath>")
def serve_image(filepath):
    try:
        cache_path = get_eink_image_path(filepath)
        if cache_path is None:
            return jsonify({"status": "error", "message": "Image not found"}), 404
        return send_file(cache_path, mimetype="image/png")
    except Exception as e:
        # Fall back to serving the original if processing fails for any reason
        app.logger.error(f"E-ink processing failed for {filepath}: {e}")
        return send_from_directory(IMAGES_DIR, filepath)


@app.route("/images/original/<path:filepath>")
def serve_original_image(filepath):
    """Serve the unprocessed source image, e.g. for debugging."""
    return send_from_directory(IMAGES_DIR, filepath)


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
