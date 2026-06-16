# Getting Started

This guide walks you through setting up the Grand Tour Stage Profile recipe on your TRMNL BYOS device. It assumes you have LaraPaper running on a home server or NAS, and a TRMNL device registered in it.

You do not need to know how to code. Every command you need is written out in full — you just copy and paste.

---

## What this recipe does

Your TRMNL display will automatically show the right thing depending on the time of year:

| When | What you see |
|------|-------------|
| During a Grand Tour (Giro, TdF, Vuelta) | Today's stage elevation profile with start time and estimated finish |
| Rest day during a tour | Tomorrow's stage profile, marked "Next Up" |
| 7 days before a tour starts | Stage 1 profile with a countdown |
| Off season | Countdown to the next tour's Stage 1 |

It supports all three Grand Tours. You add the schedule data once per year when each tour's route is announced.

---

## What you need

- A home server or NAS running Docker (Synology, Unraid, TrueNAS, etc.)
- LaraPaper installed and running on that server
- A TRMNL device registered in your LaraPaper instance
- A GitHub account (free)
- Git installed on your computer ([download here](https://git-scm.com/downloads))
- SSH access to your server

That's it. No Python, no Node.js, no local development environment needed.

---

## Step 1 — Get the files onto your computer

Open a terminal (Command Prompt or PowerShell on Windows, Terminal on Mac) and run:

```bash
git clone https://github.com/njclarke1/trmnl-grand-tour-profile.git
cd trmnl-grand-tour-profile
```

This downloads all the recipe files into a folder called `trmnl-grand-tour-profile`.

---

## Step 2 — Add stage profile images

You need to download elevation profile images for each stage of the tour(s) you want to show. The official tour websites publish these once the route is announced.

**Where to find them:**
- Tour de France: [letour.fr](https://www.letour.fr)
- Giro d'Italia: [giroditalia.it](https://www.giroditalia.it)
- Vuelta a España: [lavuelta.es](https://www.lavuelta.es)

**How to name and organise them:**

Create folders inside the `images` folder like this:

```
images/
└── 2026/
    ├── tour/
    │   ├── stage-01.jpg
    │   ├── stage-02.jpg
    │   └── ... (up to stage-21.jpg)
    ├── giro/
    │   └── stage-01.jpg ... stage-21.jpg
    └── vuelta/
        └── stage-01.jpg ... stage-21.jpg
```

The images must be named `stage-01.jpg` through `stage-21.jpg` (note the leading zero on single-digit stages). JPG and PNG both work.

**Don't worry about colours** — the recipe automatically converts yellow elevation fills to grey so they're visible on e-ink, and makes the distance markers in the black bar white so they're legible. You don't need to edit the images yourself.

---

## Step 3 — Add the tour schedule

The recipe needs to know the dates and details of each stage. This data lives in JSON files inside the `data` folder.

Create a file for each tour you want to support at `data/2026/tour.json` (or `giro.json` / `vuelta.json`).

Here's what a stage entry looks like:

```json
{
  "stage": 1,
  "date": "2026-07-04",
  "start": "Barcelona",
  "finish": "Barcelona",
  "type": "ttt",
  "distance_km": 19.7,
  "image": "stage-01.jpg",
  "start_time": "16:05",
  "est_finish": "16:55"
}
```

**Field guide:**

| Field | What it is | Example |
|-------|-----------|---------|
| `stage` | Stage number | `1` |
| `date` | Date in YYYY-MM-DD format | `"2026-07-04"` |
| `start` | Start city | `"Barcelona"` |
| `finish` | Finish city | `"Barcelona"` |
| `type` | Stage type | `"flat"`, `"hilly"`, `"mountain"`, `"ttt"`, `"itt"` |
| `distance_km` | Distance in kilometres | `186` |
| `image` | Image filename in your images folder | `"stage-06.jpg"` |
| `start_time` | Race start time in BST | `"11:15"` |
| `est_finish` | Estimated finish time in BST | `"17:05"` |

**Rest days:** simply leave them out. The recipe detects gaps between stage dates automatically.

A complete example file for the Tour de France is included at `data/2026/tour.json` in this repository.

---

## Step 4 — Deploy to your server

SSH into your server and run these commands one at a time, waiting for each to finish before running the next.

**Clone the repo onto your server:**

```bash
cd /your/config/folder
git clone https://github.com/njclarke1/trmnl-grand-tour-profile.git grand-tour
cd grand-tour
```

**Build the Docker image:**

```bash
docker build -t grand-tour .
```

This downloads the required software and packages it up. It takes about a minute the first time.

**Create the cache folder** (used to store processed images):

```bash
mkdir -p cache
```

**Start the container** using Portainer or docker compose. See [PORTAINER-SETUP.md](PORTAINER-SETUP.md) for step-by-step Portainer instructions.

**Verify it's running:**

```bash
wget -q -O- http://localhost:5051/health
```

You should see: `{"status":"ok"}`

---

## Step 5 — Set up the LaraPaper recipe

1. Open your LaraPaper admin panel
2. Go to **Plugins → Create**
3. Fill in:
   - **Name:** `Grand Tour Stage Profile`
   - **Data strategy:** `polling`
   - **Polling URL:** `http://YOUR-SERVER-IP:5051/api/stage`
   - **Polling interval:** `60`
4. Save
5. Go to the plugin's markup/template tab
6. Paste the entire contents of `recipe/markup.blade.php`
7. Save
8. Go to **Devices**, find your device, and add this plugin to its rotation

---

## Step 6 — Test it

Check the LaraPaper preview for your plugin. You should see either:

- A countdown screen (if no tour is currently running)
- A stage elevation profile (if a stage date matches today or is within 7 days)

If the preview shows "No stage data available", check that your `data/` folder is correctly mounted — see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

---

## Updating each season

When a new year's tour routes are announced:

1. Add new schedule JSON files to `data/2027/` (or whatever year)
2. Download new stage profile images into `images/2027/`
3. On your computer: `git add . && git commit -m "Add 2027 season data" && git push`
4. On your server: `git pull && docker restart grand-tour`

No code changes needed. The recipe picks up new data automatically.
