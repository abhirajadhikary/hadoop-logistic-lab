"""
backend.py
----------
FastAPI service that sits in front of Cassandra and exposes the three
logistics tables (shipment_snapshot, delivery_performance, route_optimization)
as JSON for the Gradio dashboard (app.py) to consume.
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from cassandra.cluster import Cluster

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("logistics-backend")

# ---------------------------------------------------------------------------
# Config (overridable via environment variables so this works the same way
# in docker-compose, k8s, or bare-metal without code changes)
# ---------------------------------------------------------------------------
CASSANDRA_HOST = os.getenv("CASSANDRA_HOST", "cassandra")
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "gold_logistics")

cluster: Cluster | None = None
session = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Open the Cassandra connection once on startup, close it cleanly on shutdown."""
    global cluster, session
    logger.info("Connecting to Cassandra at '%s' (keyspace=%s) ...", CASSANDRA_HOST, CASSANDRA_KEYSPACE)
    try:
        cluster = Cluster([CASSANDRA_HOST])
        session = cluster.connect(CASSANDRA_KEYSPACE)
        logger.info("Connected to Cassandra.")
    except Exception:
        logger.exception("Could not connect to Cassandra on startup.")
        raise
    yield
    logger.info("Shutting down Cassandra connection...")
    if cluster:
        cluster.shutdown()


app = FastAPI(title="Logistics Dashboard API", lifespan=lifespan)

# Allow the Gradio frontend (or any local dev tool) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

TABLES = {
    "shipments": "shipment_snapshot",
    "performance": "delivery_performance",
    "routes": "route_optimization",
}


def fetch_table(table_name: str):
    """Run SELECT * against a table and return a list of JSON-safe dicts."""
    rows = session.execute(f"SELECT * FROM {table_name}")
    result = []
    for row in rows:
        record = row._asdict()
        # Cassandra date/timestamp objects aren't JSON serializable by default
        for key, value in record.items():
            if hasattr(value, "isoformat"):
                record[key] = value.isoformat()
        result.append(record)
    return result


@app.get("/health")
def health():
    return {"status": "ok", "keyspace": CASSANDRA_KEYSPACE}


@app.get("/all-data")
def get_all_data():
    """Single call the dashboard uses to hydrate every tab at once."""
    try:
        return {key: fetch_table(table) for key, table in TABLES.items()}
    except Exception as exc:
        logger.exception("Failed to fetch data from Cassandra")
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/table/{name}")
def get_table(name: str):
    """Fetch a single table by its logical name (shipments/performance/routes)."""
    if name not in TABLES:
        raise HTTPException(status_code=404, detail=f"Unknown table '{name}'. Valid options: {list(TABLES)}")
    try:
        return fetch_table(TABLES[name])
    except Exception as exc:
        logger.exception("Failed to fetch table %s", name)
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=True)