# TRMNL Grand Tour Stage Profile

A [TRMNL](https://usetrmnl.com) recipe for BYOS (LaraPaper) that displays the elevation profile of the current cycling grand tour stage on your e-ink display.

Supports all three Grand Tours: **Giro d'Italia**, **Tour de France**, and **Vuelta a España**.

## What it shows

| Scenario | Display |
|----------|---------|
| Stage day | That stage's elevation profile with route and distance |
| Rest day during a tour | Next stage's profile, marked "Next up" |
| ≤7 days before a tour | Stage 1 profile with countdown |
| Off-season | Countdown to the next scheduled tour |

Optimised for **960×540** (M5Stack PaperS3) but works at any TRMNL-supported resolution.

## Requirements

- TRMNL device with BYOS / [LaraPaper](https://github.com/usetrmnl/larapaper) server
- Docker on the same host as LaraPaper
- Stage profile images (you download these — see [Image preparation](#image-preparation))

## Quick start

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/trmnl-grand-tour-profile.git
cd trmnl-grand-tour-profile
```

### 2. Add schedule data

Create a JSON file per tour in `data/<year>/`:

```bash
mkdir -p data/2026
```

See [Schedule format](#schedule-format) below. An example is provided at `data/example/tour.json`.

### 3. Add stage profile images

```bash
mkdir -p images/2026/{giro,tour,vuelta}
```

Drop your downloaded profile PNGs into the matching folder, named `stage-01.png` through `stage-21.png`. See [Image preparation](#image-preparation).

### 4. Configure BASE_URL

Edit `docker-compose.yml` and set `BASE_URL` to your NAS IP and the exposed port:

```yaml
- BASE_URL=http://YOUR_NAS_IP:5051
```

### 5. Build and start

```bash
docker compose up -d --build
```

Verify the API is running:

```bash
curl http://localhost:5051/api/stage
```

### 6. Create LaraPaper recipe

1. Open LaraPaper admin
2. Go to **Plugins → Create**
3. Set **Data strategy** to `polling`
4. Set **Polling URL** to `http://YOUR_NAS_IP:5051/api/stage`
5. Paste the contents of `recipe/markup.html` into the **Markup** field
6. Assign the plugin to your device
7. Trigger a screen regeneration:

```bash
docker exec larapaper php artisan tinker \
  --execute="App\Jobs\GenerateScreenJob::dispatchSync(App\Models\Device::first());"
```

## Schedule format

Each tour needs a JSON file in `data/<year>/`. The `short` field must match the folder name under `images/`.

```json
{
  "tour": "Tour de France",
  "short": "tour",
  "year": 2026,
  "stages": [
    {
      "stage": 1,
      "date": "2026-07-04",
      "start": "Lille",
      "finish": "Lille",
      "type": "flat",
      "distance_km": 185,
      "image": "stage-01.png"
    }
  ]
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `tour` | Yes | Full display name |
| `short` | Yes | Folder name: `giro`, `tour`, or `vuelta` |
| `year` | Yes | Must match the data directory name |
| `stages[].stage` | Yes | Stage number (1–21) |
| `stages[].date` | Yes | `YYYY-MM-DD` — rest days are omitted, not listed |
| `stages[].start` | Yes | Start city |
| `stages[].finish` | Yes | Finish city |
| `stages[].type` | No | e.g. `flat`, `hilly`, `mountain`, `itt` |
| `stages[].distance_km` | No | Stage distance in km |
| `stages[].image` | Yes | Filename in `images/<year>/<short>/` |

**Rest days**: simply don't include them. The app detects gaps between stages automatically.

**Multiple tours in one year**: create separate files per tour (e.g. `giro.json`, `tour.json`, `vuelta.json`). The app loads all JSONs and sorts by date.

## Image preparation

Profile images are not included — you download them yourself for each tour.

### Sources

- Official tour websites publish stage profiles once the route is announced
- Cycling media sites (FirstCycling, ProCyclingStats) often have clean profile graphics

### Tips for e-ink

- **High contrast**: profiles with strong black lines on white background display best on e-ink
- **Resolution**: 900×400 px or larger recommended (the template scales to fit)
- **Format**: PNG preferred
- **Naming**: `stage-01.png` through `stage-21.png` (zero-padded)
- **Colour**: colour images work but will render as greyscale; consider converting to greyscale + boosting contrast for best results

### Folder structure

```
images/
└── 2026/
    ├── giro/
    │   ├── stage-01.png
    │   ├── stage-02.png
    │   └── ...
    ├── tour/
    │   ├── stage-01.png
    │   └── ...
    └── vuelta/
        ├── stage-01.png
        └── ...
```

## API reference

### `GET /api/stage`

Returns the current or next stage to display.

**Response fields:**

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `live`, `rest_day`, `upcoming`, `countdown`, `off_season`, `no_data` |
| `tour` | string | Full tour name |
| `short` | string | Short tour key |
| `year` | int | Tour year |
| `stage` | int | Stage number |
| `date` | string | Stage date (`YYYY-MM-DD`) |
| `start` | string | Start city |
| `finish` | string | Finish city |
| `type` | string | Stage type |
| `distance_km` | int | Distance in km |
| `image_url` | string | Full URL to the profile image |
| `countdown_days` | int/null | Days until stage/tour |

### `GET /images/<year>/<tour>/<filename>`

Serves stage profile images from the mounted volume.

### `GET /health`

Returns `{"status": "ok"}`.

## Display logic

```
Is there a stage today?
  └─ Yes → Show it (status: "live")
  └─ No  → Is there a future stage?
              └─ No  → "off_season" (all tours done)
              └─ Yes → Is same tour already started AND next stage ≤3 days?
                          └─ Yes → Rest day — show next stage
                          └─ No  → Is next tour's Stage 1 ≤7 days away?
                                      └─ Yes → Show Stage 1 profile ("upcoming")
                                      └─ No  → Countdown to next tour
```

## Portainer deployment

If deploying via Portainer rather than `docker compose`, you'll need to build the image first and reference it by name, or use a Portainer stack with a build context pointing at the cloned repo directory.

**Option A — pre-build the image:**

```bash
cd /path/to/trmnl-grand-tour-profile
docker build -t grand-tour .
```

Then in Portainer, create a stack with:

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
      - BASE_URL=http://YOUR_NAS_IP:5051
    volumes:
      - /path/to/data:/data:ro
      - /path/to/images:/images:ro
```

## Updating for a new season

1. Create `data/<year>/` and add schedule JSONs once routes are announced
2. Download profile images into `images/<year>/<tour>/`
3. Restart the container: `docker restart grand-tour`

No code changes needed — the app scans all files in the data directory on each request.

## Licence

MIT
