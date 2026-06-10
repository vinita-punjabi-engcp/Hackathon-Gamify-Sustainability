🚀 The Core Architecture

1. **The Ingestion Layer (`ingest_metrics.py`):** An automated background pipeline that aggregates raw computing resource profiles per namespace, maps them to high-level engineering teams, and handles data persistence.
2. **The Database Layer (`greenops.db`):** A lightweight, relational local database utilizing SQLite and SQLAlchemy models where telemetry and environmental computations are synchronized via unique primary keys (`team_name`).
3. **The Presentation Engine (`app.py`):** A high-performance FastAPI microservice layer exposing granular team investigative tracking metrics and partitioned leaderboards tracking organizational optimization profiles.

---

## 🛠️ Installation & Environment Setup

### 1. Prerequisites
Ensure your local environment possesses:
- **Python 3.10+**
- Active access to your cluster via the **Kubectl CLI client** (`kubectl config current-context`)

### 2. Clone and Setup
```bash
# Clone the repository
git clone [https://github.com/YOUR_ORGANIZATION/eco-trace-ai.git](https://github.com/YOUR_ORGANIZATION/eco-trace-ai.git)
cd eco-trace-ai


# Install the required application dependencies
python3 -m venv venv
source venv/bin/activate && pip install -r requirements.txt 

HOW TO RUN

Step 1: Run this command in your project directory:
Bash
source venv/bin/activate && python3 app.py

What happens: You will see a file named greenops.db appear in your directory. Your local database is now officially created and waiting for data. Keep this server terminal running.

Step 2: Populate the DB using your Ingestion Script
Now, open a second terminal window, make sure your kubectl context is connected to your active cluster, and run your scraper pipeline:
Bash
source venv/bin/activate && python3 ingest_metrics.py


If you prefer a clean UI over a terminal window to check your data tables during the hackathon, install DB Browser for SQLite:

Mac (via Homebrew): brew install --cask db-browser-for-sqlite

Once installed, just click "Open Database" and select your greenops.db file. You will be able to see every row, metric, and carbon calculation update in real-time as your kubectl script runs!

Check the API

1. FOR LEADERSHIP BOARD -> http://127.0.0.1:8000/api/leaderboard
2. FOR TEAM-USUAGR -> http://127.0.0.1:8000/api/team-metrics?team_name=<team-name>