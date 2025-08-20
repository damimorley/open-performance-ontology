import os

from fastapi import FastAPI
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
from .pydantic_ontology import ALLOWED_UNITS, DiffOut, MetricIn

load_dotenv(".env")

app = FastAPI(title="Ingestion API", version="0.1.0")


def _driver():
    uri, user, pwd = (
        os.getenv("NEO4J_URI"),
        os.getenv("NEO4J_USER"),
        os.getenv("NEO4J_PASSWORD"),
    )
    if not all([uri, user, pwd]):
        raise RuntimeError("Set NEO4J_* env vars")
    return GraphDatabase.driver(uri, auth=(user, pwd))

# api/main.py
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

from .pydantic_ontology import MetricIn, ALLOWED_UNITS, DiffOut

# ✅ load your .env so NEO4J_* is available when the server starts
load_dotenv(".env")

app = FastAPI(title="Ingestion API", version="0.1.0")

def _driver():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    pwd  = os.getenv("NEO4J_PASSWORD")
    if not all([uri, user, pwd]):
        raise RuntimeError("Set NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD in .env")
    return GraphDatabase.driver(uri, auth=(user, pwd))

# ✅ Redirect root to Swagger so hitting "/" doesn't 404
@app.get("/")
def root():
    return RedirectResponse(url="/docs")

@app.get("/ontology/units")
def units():
    return {"units": ALLOWED_UNITS}

@app.get("/ontology/diff", response_model=DiffOut)
def diff():
    return DiffOut(added_units=[])

@app.post("/ingest")
def ingest(m: MetricIn):
    q = """
    MERGE (a:Athlete {athlete_id: $athlete_id, coach_id: $coach_id})
    MERGE (s:Session {session_id: $session_id, ts: datetime($ts), coach_id: $coach_id})
    MERGE (a)-[:ATTENDED]->(s)
    CREATE (mt:Metric {name: $name, unit: $unit, value: $value, coach_id: $coach_id})
    MERGE (s)-[:RECORDED]->(mt)
    """
    with _driver().session() as s:
        s.run(q, **m.model_dump())
    return {"ok": True}



@app.get("/ontology/diff", response_model=DiffOut)
def diff():
    return DiffOut(added_units=[])


@app.post("/ingest")
def ingest(m: MetricIn):
    q = """
    MERGE (a:Athlete {athlete_id: $athlete_id, coach_id: $coach_id})
    MERGE (s:Session {session_id: $session_id, ts: datetime($ts), coach_id: $coach_id})
    MERGE (a)-[:ATTENDED]->(s)
    CREATE (mt:Metric {name: $name, unit: $unit, value: $value, coach_id: $coach_id})
    MERGE (s)-[:RECORDED]->(mt)
    """
    with _driver().session() as s:
        s.run(q, **m.model_dump())
    return {"ok": True}
