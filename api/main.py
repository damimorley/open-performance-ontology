
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from neo4j import GraphDatabase
from pydantic import BaseModel

# keep this import path the same as in your repo
from .pydantic_ontology import ALLOWED_UNITS, MetricIn  # type: ignore

# ------------------------------------------------------------
# App + config
# ------------------------------------------------------------
load_dotenv(".env")

app = FastAPI(title="Ingestion API", version="0.7.0")
print("✅ API 0.7.0 booted (X-API-Key required)")

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

# ------------------------------------------------------------
# Neo4j driver factory — always use _driver().session()
# ------------------------------------------------------------
def _driver():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    pwd = os.getenv("NEO4J_PASSWORD") or os.getenv("NEO4J_PASS") or "testpassword"
    if not all([uri, user, pwd]):
        raise RuntimeError("Missing NEO4J_* env vars (NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)")
    return GraphDatabase.driver(uri, auth=(user, pwd))

# ------------------------------------------------------------
# Models
# ------------------------------------------------------------
class AthleteIn(BaseModel):
    id: str
    name: str

class MetricsBatch(BaseModel):
    items: List[MetricIn]

class CypherReq(BaseModel):
    query: str
    params: Optional[Dict[str, Any]] = None

class MeasurementIn(BaseModel):
    athlete_id: str
    metric_name: str
    value: float
    unit: str | None = None


API_KEYS = {"demo-doe-key": "doe"}

def _coach_from_key(x_api_key: str) -> str:
    cid = API_KEYS.get(x_api_key)
    if not cid:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return cid



# ------------------------------------------------------------
# Routes
# ------------------------------------------------------------
@app.get("/")
def root():
    return RedirectResponse("/docs")

@app.get("/_debug")
def debug():
    return {"file": __file__, "version": app.version}

@app.get("/health")
def health():
    with _driver().session() as s:
        s.run("RETURN 1").single()
    return {"status": "ok"}

@app.get("/athletes", summary="List Athletes")
def list_athletes():
    cypher = """
    MATCH (a:Athlete)
    RETURN a.id AS id, a.name AS name
    ORDER BY name
    """
    with _driver().session() as s:
        return [r.data() for r in s.run(cypher)]

@app.get("/ontology/units", summary="Units")
def units():
    return {"units": ALLOWED_UNITS}

_WRITE_Q = """
MERGE (a:Athlete {athlete_id: $athlete_id, coach_id: $coach_id})
MERGE (s:Session {session_id: $session_id, ts: datetime($ts), coach_id: $coach_id})
MERGE (a)-[:ATTENDED]->(s)
MERGE (m:Metric {name: $name, unit: $unit, value: $value, coach_id: $coach_id})
MERGE (s)-[:RECORDED]->(m)
"""

@app.post("/ingest", summary="Ingest")
def ingest(m: MetricIn, x_api_key: str = Header(..., alias="X-API-Key")):
    coach_id = _coach_from_key(x_api_key)
    data = m.model_dump()
    data["coach_id"] = coach_id
    with _driver().session() as s:
        s.run(_WRITE_Q, **data)
    return {"ok": True}

@app.post("/measurements", summary="Create Athlete→MEASURED→Metric")
def create_measurement(m: MeasurementIn):
    cypher = """
    MERGE (a:Athlete {id: $athlete_id})
    MERGE (m:Metric {name: $metric_name})
    // keep existing unit if set; otherwise set from payload
    SET m.unit = coalesce(m.unit, $unit)
    MERGE (a)-[r:MEASURED]->(m)
    SET r.value = $value
    RETURN a.id AS athlete_id, m.name AS metric, m.unit AS unit, r.value AS value
    """
    with _driver().session() as s:
        rec = s.run(
            cypher,
            athlete_id=m.athlete_id,
            metric_name=m.metric_name,
            value=m.value,
            unit=m.unit,
        ).single()
    return rec.data() if rec else {}

@app.post("/ingest/batch", summary="Ingest Batch")
def ingest_batch(batch: MetricsBatch, x_api_key: str = Header(..., alias="X-API-Key")):
    coach_id = _coach_from_key(x_api_key)
    with _driver().session() as s:
        for item in batch.items:
            data = item.model_dump()
            data["coach_id"] = coach_id
            s.run(_WRITE_Q, **data)
    return {"ok": True, "count": len(batch.items)}

@app.post("/athletes", summary="Create Athlete")
def create_athlete(athlete: AthleteIn):
    cypher = """
    MERGE (a:Athlete {id: $id})
    SET a.name = $name
    RETURN a.id AS id, a.name AS name
    """
    with _driver().session() as s:
        rec = s.run(cypher, id=athlete.id, name=athlete.name).single()
    return rec.data() if rec else {}

ALLOWED_PREFIXES = ("MATCH", "RETURN", "WITH", "UNWIND", "CALL", "PROFILE", "EXPLAIN")

@app.post("/cypher", summary="Run read-only Cypher (demo)")
def cypher_read(req: CypherReq):
    q = (req.query or "").strip()
    if not q.upper().startswith(ALLOWED_PREFIXES):
        raise HTTPException(400, "Only read-style queries are allowed here for the demo.")
    with _driver().session() as s:
        result = s.run(q, req.params or {})
        rows = [r.data() for r in result]
    return {"rows": rows, "count": len(rows)}





