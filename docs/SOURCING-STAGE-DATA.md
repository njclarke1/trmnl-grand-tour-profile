# Sourcing Stage Data Each Season

This guide walks through exactly how to find and compile the schedule data and stage profile images you need for each Grand Tour. Plan for about 30–60 minutes per tour, done once per year when the route is announced.

---

## When to do this

Routes are typically announced in October/November the year before:

| Tour | Route announcement | Race dates |
|------|--------------------|------------|
| Giro d'Italia | October/November | May |
| Tour de France | October/November | July |
| Vuelta a España | January/February | August–September |

You can add data as soon as the route is announced — the recipe will show a countdown until the race starts.

---

## Part 1 — Stage schedule data

You need: stage number, date, start city, finish city, stage type, distance, start time, estimated finish time.

### Step 1 — Find the official stage list

The most reliable sources are:

**Wikipedia** — search `"Tour de France 2027"` (or Giro/Vuelta). The article includes a stages table with dates, start/finish towns, distances, and stage types. It's usually complete within days of the route announcement.

**Official tour websites:**
- Tour de France: [letour.fr/en/overall-route](https://www.letour.fr/en/overall-route)
- Giro d'Italia: [giroditalia.it/eng/giro/tappe](https://www.giroditalia.it/eng/giro/tappe)
- Vuelta a España: [lavuelta.es/en/recorrido](https://www.lavuelta.es/en/recorrido)

### Step 2 — Find start times

Official start times are published by ASO but aren't always easy to find on the official sites. The most reliable source is:

**[franceletour.com/tour-de-france-YEAR-schedule](https://franceletour.com/tour-de-france-2026-schedule/)** — lists confirmed start times for every stage in multiple timezones.

For the Giro and Vuelta, similar fan sites publish confirmed times. Search `"Giro 2027 stage start times"`.

**Standard patterns** (if exact times aren't yet published):

| Stage type | Start time (BST) | Notes |
|------------|-----------------|-------|
| Flat | 12:05 | Standard afternoon start |
| Hilly | 12:05 | Standard afternoon start |
| Mountain | 11:15 | Earlier start for longer stages |
| Individual time trial | 11:30 | First rider; GC riders finish ~17:30 |
| Team time trial | Varies | Often evening start for spectacle |
| Paris finale | 15:30 | Ceremonial afternoon start |

### Step 3 — Estimate finish times

Finish times aren't published in advance — they depend on race pace. Use these average speeds as a guide:

| Stage type | Average speed | Calculation |
|------------|--------------|-------------|
| Flat | 45 km/h | Distance ÷ 45, add 0.5h for neutralised start |
| Hilly | 40 km/h | Distance ÷ 40, add 0.5h |
| Mountain | 35 km/h | Distance ÷ 35, add 0.5h |
| ITT | 50 km/h | First rider time only; last GC rider ~5–6h later |
| TTT | 55 km/h | Distance ÷ 55; all teams finish within ~1h |
| Paris finale | 30 km/h | Ceremonial pace with multiple laps |

**Example:** Stage 6, Pau → Gavarnie-Gèdre, 186 km, mountain stage, starts 11:15 BST
- 186 ÷ 35 = 5.3 hours racing
- Add 0.5h = 5.8 hours total
- 11:15 + 5:48 = 17:03 → round to **17:05 BST**

For the ITT (Stage 16 in 2026): first rider off at 11:30, last GC rider finishes around 17:30. Put `"start_time": "11:30"` and `"est_finish": "17:30"`.

### Step 4 — Build the JSON file

Create `data/YEAR/tour.json` (or `giro.json` / `vuelta.json`). Copy this structure:

```json
{
  "tour": "Tour de France",
  "short": "tour",
  "year": 2027,
  "stages": [
    {
      "stage": 1,
      "date": "2027-07-03",
      "start": "Start City",
      "finish": "Finish City",
      "type": "flat",
      "distance_km": 180,
      "image": "stage-01.jpg",
      "start_time": "12:05",
      "est_finish": "16:35"
    },
    {
      "stage": 2,
      "date": "2027-07-04",
      "start": "Start City",
      "finish": "Finish City",
      "type": "mountain",
      "distance_km": 165,
      "image": "stage-02.jpg",
      "start_time": "11:15",
      "est_finish": "16:30"
    }
  ]
}
```

**Values for `short`:** `"tour"`, `"giro"`, or `"vuelta"` — must match the folder name under `images/`

**Values for `type`:** `"flat"`, `"hilly"`, `"mountain"`, `"ttt"` (team time trial), `"itt"` (individual time trial)

**Rest days:** leave them out entirely. The recipe detects gaps automatically.

**Dates:** always `YYYY-MM-DD` format. Don't include rest day dates.

---

## Part 2 — Stage profile images

### Where to download them

The best sources for clean, high-resolution profile images:

**Official tour websites** — each stage has a dedicated page with a downloadable profile graphic. Quality is highest here.

- Tour de France: `letour.fr/en/stage-N` (replace N with stage number)
- Giro: `giroditalia.it/eng/giro/tappe/tappa-N`
- Vuelta: `lavuelta.es/en/recorrido/etapa-N`

**Cycling media sites** (if official site doesn't have downloadable images yet):
- [FirstCycling.com](https://firstcycling.com) — profiles published soon after route announcement
- [ProCyclingStats.com](https://procyclingstats.com) — also publishes profiles early

### How to save and name them

1. Right-click the profile image on the stage page → Save image as
2. Save to `images/YEAR/tour/` (or `giro/` or `vuelta/`)
3. Rename to `stage-01.jpg`, `stage-02.jpg`, etc. (zero-pad single digits)

**Tip for bulk downloading:** most browsers let you open each stage page in a tab, right-click → save image. With 21 stages this takes about 10–15 minutes.

### Image quality tips for e-ink

The recipe automatically processes images for e-ink display — you don't need to edit them. However, images with these characteristics render best:

- **High contrast** — bold black outlines, clear typography
- **Resolution** — 900×400px or larger (the recipe scales to fit)
- **Format** — JPG or PNG both work
- **Background** — white or very light grey preferred

The recipe automatically:
- Converts yellow elevation fills to mid-grey (so they're visible on the white e-ink background)
- Makes distance marker numbers in the black bar white (so they're legible on black)
- Applies sharpening to compensate for e-ink's natural softening

---

## Part 3 — Commit and deploy

Once you have the images and JSON ready:

**On your computer:**

```bash
cd your-project-folder
git add data/ images/
git commit -m "Add Tour de France 2027 stage data and profiles"
git push
```

**On your server:**

```bash
cd /path/to/grand-tour
git pull
docker restart grand-tour
```

No rebuild needed — the container reads data and images from mounted folders and picks up changes immediately on restart.

---

## Checklist

Before deploying, run through this:

- [ ] JSON file exists at `data/YEAR/tour.json` (or giro/vuelta)
- [ ] All 21 stages present (or however many the tour has)
- [ ] No rest days included in the stage list
- [ ] All dates in `YYYY-MM-DD` format
- [ ] `short` field matches the image folder name
- [ ] Image files exist for every stage listed in the JSON
- [ ] Images named `stage-01.jpg` through `stage-21.jpg`
- [ ] `image` field in each stage entry matches the actual filename

**Quick API test** after deploying:

```bash
wget -q -O- "http://YOUR-SERVER-IP:5051/api/stage" | python3 -m json.tool
```

If `status` is `"countdown"` or `"live"`, the data is loading correctly.
