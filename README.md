# open-performance-ontology (starter)
Minimal, working starter: tiny ontology, CSV→Neo4j ETL, FastAPI ingestion, CI.

## Quick start
1) Fill .env with your Neo4j Aura creds
2) Install deps
3) Load demo and run API

See steps at the bottom of this README.

## Repo layout
core/ontology.ttl
coach_extensions/doe.ttl
adapters/legacy_csv/etl.py
adapters/legacy_csv/coach_doe/{raw,mappings.yaml,validate.py}
api/{main.py,pydantic_ontology.py,requirements.txt}
scripts/{load_to_neo4j.py,demo.cypher,protect_main.sh}
.github/workflows/ci.yml

## Local run
cp .env.example .env
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r adapters/legacy_csv/requirements.txt -r api/requirements.txt
python scripts/load_to_neo4j.py scripts/demo.cypher
uvicorn api.main:app --reload  # http://127.0.0.1:8000/docs
