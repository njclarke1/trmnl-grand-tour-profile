# Building & Shipping the Grand Tour Stage Profile Recipe

End-to-end guide from local development through to community publication.

---

## Architecture recap

The recipe has two parts that work together:

**Backend** — a Flask container on the NAS that reads schedule JSONs, determines which stage to show, and serves both the stage metadata (as JSON) and the profile images (as static files).

**Recipe template** — HTML markup loaded into LaraPaper as a polling plugin. LaraPaper polls the backend's `/api/stage` endpoint, receives the JSON, and renders it using the template to generate a screen image for the device.

```
┌─────────────┐   poll /api/stage   ┌──────────────┐   render   ┌─────────────┐
│  LaraPaper  │ ──────────────────► │  Flask API   │           │  PaperS3    │
│  (polling   │ ◄────── JSON ────── │  container   │           │  device     │
│   plugin)   │                     │  port 5051   │           │  960×540    │
│             │ ──── GET image ───► │              │           │             │
│             │ ◄──── PNG ──────── │              │           │             │
│             │ ── generate PNG ──────────────────────────────►│             │
└─────────────┘                     └──────────────┘           └─────────────┘
```

---

## 1. Prerequisites

Before starting, confirm you have:

- Git installed on your development machine (Windows: `winget install Git.Git`)
- A GitHub account
- SSH access to the NAS (via Termius / Tailscale)
- Docker running on the NAS (`docker --version`)
- LaraPaper running on the NAS (port 4567)
- A TRMNL device registered in LaraPaper

You do not need Python, Node, or any local tooling beyond Git. The Docker image handles all dependencies.

---

## 2. Create the GitHub repository

### 2.1 Create the repo on GitHub

1. Go to https://github.com/new
2. Repository name: `trmnl-grand-tour-profile`
3. Description: "TRMNL BYOS recipe — cycling grand tour stage elevation profiles"
4. Visibility: **Public** (required for community catalog submission)
5. Add a README: **No** (we already have one)
6. Licence: **MIT**
7. Create repository

### 2.2 Push the project files

From the directory where you unzipped the project:

```bash
cd trmnl-grand-tour-profile
git init
git add .
git commit -m "Initial project structure"
git branch -M main
git remote add origin git@github.com:YOUR_USERNAME/trmnl-grand-tour-profile.git
git push -u origin main
```

### 2.3 Add GitHub topics

In the repo's **About** section (gear icon), add these topics for discoverability:

- `trmnl`
- `trmnl-plugin`
- `cycling`
- `grand-tour`
- `e-ink`

---

## 3. Populate tour data

### 3.1 Create schedule JSONs

For each active tour, create a JSON file under `data/<year>/`. The three Grand Tours and their typical windows:

| Tour | Short key | Typical dates |
|------|-----------|---------------|
| Giro d'Italia | `giro` | May |
| Tour de France | `tour` | July |
| Vuelta a España | `vuelta` | Aug–Sep |

```bash
mkdir -p data/2026
```

Create `data/2026/giro.json`, `data/2026/tour.json`, `data/2026/vuelta.json` following the schema in the README. Each stage entry needs a date, start/finish cities, type, distance, and an `image` field matching the filename you'll add in step 3.2.

Key rules:

- Omit rest days entirely (the app detects gaps automatically)
- Dates must be `YYYY-MM-DD` format
- The `short` field must exactly match the folder name under `images/`
- Stage numbers must be sequential (1–21)

Tip: the official tour websites publish full stage lists with dates once the route is announced (typically months before the race). A Wikipedia table of stages is also a reliable source.

### 3.2 Download profile images

Create the image directories:

```bash
mkdir -p images/2026/{giro,tour,vuelta}
```

Download stage elevation profile images from official tour websites or cycling media sites. Name them `stage-01.png` through `stage-21.png` (zero-padded).

Image guidelines for e-ink display:

- **Resolution**: 900×400 px or larger (the template scales to fit within 960×540)
- **Format**: PNG preferred
- **Contrast**: high-contrast black lines on white background display best; colour images work but render as greyscale on the device
- **Optional processing**: convert to greyscale and boost contrast/levels for crisper e-ink rendering

### 3.3 Commit the data

```bash
git add data/ images/
git commit -m "Add 2026 Giro d'Italia schedule and profiles"
git push
```

Images can be large — if the repo exceeds GitHub's soft 1GB limit, consider Git LFS for the `images/` directory. For three tours at ~21 stages each with ~200KB PNGs, total size is roughly 12MB which is well under the limit.

---

## 4. Build and deploy on the NAS

### 4.1 Clone to the NAS

SSH into the NAS and clone the repo:

```bash
ssh root@100.80.245.93
cd /srv/dev-disk-by-label-data1/config
git clone https://github.com/YOUR_USERNAME/trmnl-grand-tour-profile.git grand-tour
cd grand-tour
```

### 4.2 Build the Docker image

```bash
docker build -t grand-tour .
```

This builds a Python 3.12-slim image with Flask and gunicorn. Build takes ~30 seconds on the i5-4440.

### 4.3 Deploy via Portainer

Option A — **Portainer stack** (preferred):

1. Open Portainer at `http://192.168.68.111:9000`
2. Go to Stacks → Add stack
3. Name: `grand-tour`
4. Paste this compose (adjust the volume paths to where you cloned):

```yaml
version: "3"
services:
  grand-tour:
    image: grand-tour:latest
    container_name: grand-tour
    restart: unless-stopped
    security_opt:
      - seccomp:unconfined
    ports:
      - "5051:5000"
    environment:
      - TZ=Europe/London
      - DATA_DIR=/data
      - IMAGES_DIR=/images
      - BASE_URL=http://192.168.68.111:5051
    volumes:
      - /srv/dev-disk-by-label-data1/config/grand-tour/data:/data:ro
      - /srv/dev-disk-by-label-data1/config/grand-tour/images:/images:ro
```

5. Deploy the stack

Option B — **docker compose** from the clone directory:

```bash
docker compose up -d
```

The compose file in the repo uses relative paths (`./data`, `./images`) which work if run from the clone directory.

### 4.4 Verify the API

```bash
# From the NAS
wget -q -O- http://localhost:5051/api/stage | python3 -m json.tool

# Expected output (varies by date):
# {
#     "status": "countdown",
#     "tour": "Tour de France",
#     "stage": 1,
#     "countdown_days": 21,
#     ...
# }
```

Test image serving:

```bash
wget -q -O /dev/null http://localhost:5051/images/2026/tour/stage-01.png && echo "OK" || echo "FAIL"
```

Test the health endpoint:

```bash
wget -q -O- http://localhost:5051/health
# {"status":"ok"}
```

---

## 5. Configure the LaraPaper recipe

### 5.1 Create the polling plugin

1. Open LaraPaper admin at `http://192.168.68.111:4567`
2. Navigate to **Plugins** → **Create**
3. Configure:
   - **Name**: Grand Tour Stage Profile
   - **Data strategy**: `polling`
   - **Polling URL**: `http://192.168.68.111:5051/api/stage`
   - **Polling interval**: 3600 (hourly — stage data only changes daily)
4. Save the plugin

### 5.2 Add the markup template

1. Open the plugin you just created
2. Go to the **Markup** tab (or equivalent template editor)
3. Paste the contents of `recipe/markup.html` from the repo
4. Save

### 5.3 Assign to device

1. Go to **Devices** in LaraPaper
2. Select your PaperS3 device
3. Add the Grand Tour plugin to the device's rotation
4. Save

### 5.4 Trigger a test render

```bash
docker exec larapaper php artisan tinker \
  --execute="App\Jobs\GenerateScreenJob::dispatchSync(App\Models\Device::first());"
```

Check the generated screen in LaraPaper's admin UI. If the layout looks wrong, adjust the markup template — common issues:

- **Variables not resolving**: LaraPaper may use `{{ $status }}` (Blade) rather than `{{ status }}` (Twig). Check the plugin's Data tab to see how the JSON keys are exposed, and update the template syntax accordingly.
- **Image not loading**: verify the `BASE_URL` in docker-compose matches the NAS IP, and that LaraPaper can reach port 5051. Test with `docker exec larapaper wget -q -O /dev/null http://192.168.68.111:5051/images/2026/tour/stage-01.png && echo OK`.
- **Layout overflow**: the template is sized for 960×540. If your device model isn't set correctly (must be `device_model_id = 28` for PaperS3), LaraPaper may render at 800×480.

---

## 6. Testing the display logic

The API determines what to show based on the current date. To verify all four display states without waiting, temporarily modify your schedule data:

### Test "live" (stage today)

Edit a schedule JSON so a stage has today's date:

```json
{ "stage": 1, "date": "2026-06-13", ... }
```

Restart the container (`docker restart grand-tour`), then hit the API:

```bash
wget -q -O- http://localhost:5051/api/stage | python3 -m json.tool
```

Should return `"status": "live"`.

### Test "rest_day"

Set a past stage to yesterday, next stage to tomorrow. Should return `"status": "rest_day"`.

### Test "upcoming" (≤7 days)

Set stage 1 date to 5 days from now. Should return `"status": "upcoming"` with `"countdown_days": 5` and the stage 1 image URL.

### Test "countdown" (>7 days)

Set stage 1 date to 30 days from now. Should return `"status": "countdown"` with `"countdown_days": 30` and `"image_url": null`.

After testing, revert the schedule JSON to real dates and restart the container.

---

## 7. Submit to the TRMNL Recipe Catalog

The BYOS community catalog at [bnussbau.github.io/trmnl-recipe-catalog](https://bnussbau.github.io/trmnl-recipe-catalog/) collects TRMNLP-compatible recipes. Submission is via pull request to the `catalog.yaml` file.

### 7.1 Prepare the repo for submission

Before submitting, ensure:

- [ ] README.md has clear setup instructions
- [ ] At least one screenshot of the recipe on a device (or a rendered preview)
- [ ] Licence file is present (MIT)
- [ ] The repo is public

For the screenshot, you can:
- Take a photo of the PaperS3 showing the recipe
- Or screenshot the rendered preview from LaraPaper's admin UI
- Upload it to the repo as `assets/screenshot.png`

### 7.2 Fork and edit the catalog

1. Fork `bnussbau/trmnl-recipe-catalog`
2. Edit `catalog.yaml` and add an entry in alphabetical order:

```yaml
YOUR_USERNAME-trmnl-grand-tour-profile:
  name: 'Grand Tour Stage Profile'
  trmnlp:
    repo: 'https://github.com/YOUR_USERNAME/trmnl-grand-tour-profile'
    zip_url: 'https://github.com/YOUR_USERNAME/trmnl-grand-tour-profile/archive/main.zip'
  screenshot_url: 'https://github.com/YOUR_USERNAME/trmnl-grand-tour-profile/raw/main/assets/screenshot.png'
  license: 'MIT'
  byos:
    byos_laravel:
      compatibility: true
      compatibility_note: 'Requires companion Docker container for API + image serving'
  author:
    github: 'YOUR_USERNAME'
    name: 'Your Name'
  author_bio:
    description: 'Displays the elevation profile for the current cycling grand tour stage (Giro, Tour de France, Vuelta). Includes countdown for off-season.'
    github_url: 'https://github.com/YOUR_USERNAME/trmnl-grand-tour-profile'
    learn_more_url: 'https://github.com/YOUR_USERNAME/trmnl-grand-tour-profile/blob/main/README.md'
```

3. Commit with message: `Add recipe: Grand Tour Stage Profile`
4. Open a pull request to `bnussbau/trmnl-recipe-catalog`

### 7.3 Note on TRMNLP compatibility

This recipe differs from a pure TRMNLP recipe because it requires a companion Docker container — it's not a standalone markup + polling-from-public-API recipe. The catalog supports this pattern (other recipes like train monitors and Home Assistant integrations work similarly), but it means users can't one-click install. The README should make the Docker requirement clear.

If you later want to support the TRMNL cloud marketplace (not just BYOS), you'd need to host the API publicly (e.g. via Cloudflare Tunnel or a small VPS) and create Liquid templates (`full.liquid`, `half_horizontal.liquid`, etc.) using the TRMNL Design System framework. That's a separate effort and not required for the community catalog.

---

## 8. Updating for a new season

When the next tour's route is announced:

### 8.1 Add new schedule data

```bash
mkdir -p data/2027
# Create giro.json, tour.json, vuelta.json with the new dates
```

### 8.2 Download new profile images

```bash
mkdir -p images/2027/{giro,tour,vuelta}
# Download and name stage-01.png through stage-21.png per tour
```

### 8.3 Push and pull

```bash
# On your development machine
git add data/2027 images/2027
git commit -m "Add 2027 season data"
git push

# On the NAS
cd /srv/dev-disk-by-label-data1/config/grand-tour
git pull
docker restart grand-tour
```

No image rebuilds needed — the Flask app reads data and images from mounted volumes and picks up changes on the next API request.

### 8.4 Cleaning up old seasons

Old season data can remain (it's harmless — the app ignores past stages). If you want to trim the repo:

```bash
git rm -r data/2025 images/2025
git commit -m "Remove 2025 season data"
git push
```

---

## 9. Updating the application code

If you change `app.py`, `Dockerfile`, or `requirements.txt`, you need to rebuild:

```bash
# On the NAS
cd /srv/dev-disk-by-label-data1/config/grand-tour
git pull
docker build -t grand-tour .
docker stop grand-tour && docker rm grand-tour

# Then redeploy via Portainer (update the stack) or:
docker compose up -d
```

If only data/images changed, `docker restart grand-tour` is sufficient.

---

## 10. Troubleshooting

### Container won't start

```bash
docker logs grand-tour 2>&1 | tail -20
```

Common causes:

- Port 5051 already in use: `ss -tlnp | grep 5051`
- Volume mount path doesn't exist: verify `/srv/dev-disk-by-label-data1/config/grand-tour/data/` exists

### API returns "no_data"

No schedule JSON files found. Check:

```bash
ls /srv/dev-disk-by-label-data1/config/grand-tour/data/
# Should list year directories containing .json files
```

### Images return 404

Verify the image path matches what the API returns:

```bash
# Check what the API thinks the image path is
wget -q -O- http://localhost:5051/api/stage | grep image_url

# Then try fetching that exact URL
wget -q -O /dev/null "THE_URL_FROM_ABOVE" && echo OK
```

Common cause: `short` field in JSON doesn't match the folder name under `images/`.

### LaraPaper shows blank/broken screen

1. Check the plugin's **Data** tab — does it show the JSON from `/api/stage`?
2. If data is there but rendering fails, the template syntax may need adjusting (Blade `{{ $var }}` vs Twig `{{ var }}`)
3. Verify `device_model_id = 28` is set for PaperS3 (960×540)

### Screen shows old/cached data

LaraPaper caches rendered screens. Force a regeneration:

```bash
docker exec larapaper php artisan tinker \
  --execute="App\Jobs\GenerateScreenJob::dispatchSync(App\Models\Device::first());"
```

---

## Quick reference — command cheat sheet

```bash
# Deploy (first time)
cd /srv/dev-disk-by-label-data1/config
git clone https://github.com/USER/trmnl-grand-tour-profile.git grand-tour
cd grand-tour
docker build -t grand-tour .
docker compose up -d

# Verify
wget -q -O- http://localhost:5051/api/stage
wget -q -O- http://localhost:5051/health

# Update data only (no rebuild)
cd /srv/dev-disk-by-label-data1/config/grand-tour
git pull
docker restart grand-tour

# Update code (rebuild needed)
cd /srv/dev-disk-by-label-data1/config/grand-tour
git pull
docker build -t grand-tour .
docker compose up -d

# Force screen refresh
docker exec larapaper php artisan tinker \
  --execute="App\Jobs\GenerateScreenJob::dispatchSync(App\Models\Device::first());"

# Check logs
docker logs grand-tour 2>&1 | tail -20
```
