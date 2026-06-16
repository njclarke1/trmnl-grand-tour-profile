# Portainer Setup

This guide walks you through deploying the Grand Tour recipe container using Portainer. Portainer is a web-based interface for managing Docker containers — think of it as a control panel for your server's running services.

If you're comfortable using docker compose directly from the command line, you can skip this guide and just run `docker compose up -d` from the `grand-tour` folder on your server instead.

---

## Before you start

Make sure you have:

- Built the Docker image on your server (`docker build -t grand-tour .` — see [GETTING-STARTED.md](GETTING-STARTED.md))
- Created the `cache` folder on your server (`mkdir -p cache`)
- Noted your server's local IP address (e.g. `192.168.1.100`)
- Noted the full path to where you cloned the recipe (e.g. `/srv/config/grand-tour`)

---

## Creating the stack

1. Open Portainer in your browser (usually `http://YOUR-SERVER-IP:9000`)
2. Click **Stacks** in the left menu
3. Click **Add stack**
4. Give it a name: `grand-tour`
5. Select **Web editor**
6. Paste the following into the editor, replacing the placeholders:

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
      - CACHE_DIR=/cache
      - BASE_URL=http://YOUR-SERVER-IP:5051
    volumes:
      - /YOUR/PATH/grand-tour/data:/data:ro
      - /YOUR/PATH/grand-tour/images:/images:ro
      - /YOUR/PATH/grand-tour/cache:/cache
```

**Replace before saving:**
- `YOUR-SERVER-IP` — your server's local IP address (e.g. `192.168.1.100`)
- `/YOUR/PATH/grand-tour` — the full path to the recipe folder on your server (e.g. `/srv/config/grand-tour`)

7. Click **Deploy the stack**

---

## Verifying the container is running

After deploying, you should see the `grand-tour` stack listed with a green "Running" status.

To double-check from your server's terminal:

```bash
wget -q -O- http://localhost:5051/health
```

Expected response: `{"status":"ok"}`

To see what stage data the API is currently returning:

```bash
wget -q -O- http://localhost:5051/api/stage | python3 -m json.tool
```

---

## Updating the container after a code change

When a new version of the recipe is released (or you've pulled an update via `git pull`), you need to rebuild the Docker image and redeploy:

**On your server:**

```bash
cd /YOUR/PATH/grand-tour
git pull
docker build -t grand-tour .
```

Then in Portainer:
1. Go to **Stacks → grand-tour**
2. Click **Update the stack**
3. Make sure **Re-pull image** is ticked
4. Click **Update**

The container will restart with the new version. Any cached images are preserved in the `cache` folder.

---

## Restarting the container

If the container stops responding, you can restart it without losing anything:

**Via Portainer:**
1. Go to **Containers**
2. Find `grand-tour`
3. Click the restart icon

**Via terminal:**

```bash
docker restart grand-tour
```

---

## Checking container logs

If something isn't working, the logs will usually tell you why:

**Via Portainer:**
1. Go to **Containers → grand-tour**
2. Click **Logs**

**Via terminal:**

```bash
docker logs grand-tour 2>&1 | tail -30
```

Common things to look for:
- `[ERROR]` lines indicate something failed
- `Generated image:` lines confirm images are being processed successfully
- `No JSON file found` means the data folder isn't mounted correctly
