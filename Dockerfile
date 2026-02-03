# ClearBlueSky Stock Scanner - runs on any OS (Linux, macOS, Windows with WSL2)
# GUI is shown via X11 forwarding from the container to the host.

FROM python:3.11-bookworm

# Install tkinter (and dependencies for pygame if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-tk \
    libsdl2-mixer-2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY app/ .

# Default: run the GUI app (expects DISPLAY set by host for X11)
ENTRYPOINT ["python", "app.py"]
