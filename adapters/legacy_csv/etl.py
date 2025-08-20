import argparse
import os
import pathlib
import sys

import pandas as pd
import yaml
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

ROOT = pathlib.Path(__file__).resolve().parents[2]
MAP_DIR = ROOT / "adapters" / "legacy_csv" / "coach_doe"
MAP_DIR.mkdir(parents=True, exist_ok=True)


def propose_mappings(df):
    defaults = {
        "athlete_id": None,
        "session_id": None,
        "ts": None,
        "name": None,
        "unit": None,
        "value": None,
        "coach_id": "doe",
    }
    mapping = {}
    for k in defaults:
        for c in df.columns:
            if c.lower().startswith(k[:3]):
                mapping[k] = c
                break
        mapping.setdefault(k, defaults[k])
    return mapping


def save_mappings(path, mapping):
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(mapping, f)


def load_mappings(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def to_graph(rows):
    uri, user, pwd = (
        os.getenv("NEO4J_URI"),
        os.getenv("NEO4J_USER"),
        os.getenv("NEO4J_PASSWORD"),
    )
    if not all([uri, user, pwd]):
        print("Set NEO4J_* env or .env", file=sys.stderr)
        sys.exit(1)
    driver = GraphDatabase.driver(uri, auth=(user, pwd))
    q = """
    MERGE (a:Athlete {athlete_id: $athlete_id, coach_id: $coach_id})
    MERGE (s:Session {session_id: $session_id, ts: datetime($ts), coach_id: $coach_id})
    MERGE (a)-[:ATTENDED]->(s)
    CREATE (m:Metric {name: $name, unit: $unit, value: toFloat($value), coach_id: $coach_id})
    MERGE (s)-[:RECORDED]->(m)
    """
    with driver.session() as s:
        for r in rows:
            s.run(q, **r)
    driver.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--coach", required=True)
    ap.add_argument("--csv", required=True)
    args = ap.parse_args()
    df = pd.read_csv(args.csv)
    map_path = MAP_DIR / "mappings.yaml"
    if not map_path.exists():
        mapping = propose_mappings(df)
        save_mappings(map_path, mapping)
        print(f"[info] wrote mappings: {map_path}")
    else:
        mapping = load_mappings(map_path)
    missing = [k for k, v in mapping.items() if v is None and k not in ("coach_id",)]
    if missing:
        print("[error] unmapped required columns:", missing, "\n[hint] edit", map_path)
        sys.exit(2)
    rows = []
    for _, row in df.iterrows():
        rows.append(
            {
                k: (str(row[mapping[k]]) if k != "value" else row[mapping[k]])
                for k in ("athlete_id", "session_id", "ts", "name", "unit", "value")
            }
        )
        rows[-1]["coach_id"] = mapping.get("coach_id", "doe")
    to_graph(rows)
    print(f"[ok] loaded {len(rows)} rows into Neo4j.")


if __name__ == "__main__":
    main()
