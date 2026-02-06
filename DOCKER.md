# Running ClearBlueSky with Docker (any OS)

Run the same app on **Linux**, **macOS**, or **Windows (with WSL2)** without using the Windows installer. The app is a GUI; Docker shows it by forwarding your display (X11).

---

## Prerequisites

- **Docker** and **Docker Compose** installed.
- **X11** so the GUI can display:
  - **Linux:** X11 is usually already there. Allow Docker to use it:  
    `xhost +local:docker`
  - **macOS:** Install [XQuartz](https://www.xquartz.org/), start it, then:  
    `xhost +localhost`
  - **Windows:** Use WSL2 and an X server (e.g. [VcXsrv](https://sourceforge.net/projects/vcxsrv/)). In WSL2, set `DISPLAY` to your Windows host (e.g. `export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0`). Then run Docker from WSL2.

---

## Build and run

From the project root (where `Dockerfile` and `docker-compose.yml` are):

```bash
# Build the image
docker compose build

# Run the app (GUI will open on your display)
docker compose up
```

Reports and scan CSVs are written to `./reports` and `./scans` on your machine (mounted into the container).

---

## Run without Docker Compose

```bash
# Build
docker build -t clearbluesky:7.0 .

# Run (Linux example; allow X11 first: xhost +local:docker)
docker run --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v "$(pwd)/reports:/app/reports" -v "$(pwd)/scans:/app/scans" \
  -it clearbluesky:7.0
```

On **macOS**, use the same `docker run` but ensure XQuartz is running and `DISPLAY` is set (e.g. `:0` or `host.docker.internal:0` depending on your setup).

---

## Optional: persist settings

Your Finviz API key and preferences are stored in `user_config.json` inside the container. To keep them across runs:

1. Copy the file out once:  
   `docker run --rm clearbluesky:7.0 cat /app/user_config.json > user_config.json`  
   (edit it, then use the volume below.)
2. Run with a bind mount:  
   add `-v "$(pwd)/user_config.json:/app/user_config.json"` to your `docker run` or add it under `volumes` in `docker-compose.yml`.

---

*ClearBlueSky v7.0*
