from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import RedirectResponse
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
from .pydantic_ontology import MetricIn, ALLOWED_UNITS
from pydantic import BaseModel
from typing import List
from fastapi.middleware.cors import CORSMiddleware


load_dotenv(".env")

app = FastAPI(title="Ingestion API", version="0.7.0")
print("🟢 API 0.7.0 booted (X-API-Key required)")


ALLOWED_ORIGINS = [
    "https://clovisathlete.com",
    "https://www.clovisathlete.com",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key"],
    allow_credentials=False,
)


def _driver():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    pwd = os.getenv("NEO4J_PASSWORD")
    if not all([uri, user, pwd]):
        raise RuntimeError("Missing NEO4J_* env vars")
    return GraphDatabase.driver(uri, auth=(user, pwd))


API_KEYS = {"demo-doe-key": "doe"}


def _coach_from_key(x_api_key: str) -> str:
    cid = API_KEYS.get(x_api_key)
    if not cid:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return cid


@app.get("/")
def root():
    return RedirectResponse("/docs")


@app.get("/_debug")
def debug():
    return {"file": __file__, "version": app.version}


@app.get("/ontology/units")
def units():
    return {"units": ALLOWED_UNITS}


_WRITE_Q = """
MERGE (a:Athlete {athlete_id: $athlete_id, coach_id: $coach_id})
MERGE (s:Session {session_id: $session_id, ts: datetime($ts), coach_id: $coach_id})
MERGE (a)-[:ATTENDED]->(s)
CREATE (m:Metric {name: $name, unit: $unit, value: $value, coach_id: $coach_id})
MERGE (s)-[:RECORDED]->(m)
"""


@app.post("/ingest")
def ingest(m: MetricIn, x_api_key: str = Header(..., alias="X-API-Key")):
    coach_id = _coach_from_key(x_api_key)
    data = m.model_dump()
    data["coach_id"] = coach_id
    with _driver().session() as s:
        s.run(_WRITE_Q, **data)
    return {"ok": True}


class MetricsBatch(BaseModel):
    items: List[MetricIn]


@app.post("/ingest/batch")
def ingest_batch(batch: MetricsBatch, x_api_key: str = Header(..., alias="X-API-Key")):
    coach_id = _coach_from_key(x_api_key)
    with _driver().session() as s:
        for item in batch.items:
            data = item.model_dump()
            data["coach_id"] = coach_id
            s.run(_WRITE_Q, **data)
    return {"ok": True, "count": len(batch.items)}
