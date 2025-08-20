import os
import pathlib
import sys

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

uri, user, password = (
    os.getenv("NEO4J_URI"),
    os.getenv("NEO4J_USER"),
    os.getenv("NEO4J_PASSWORD"),
)
if not all([uri, user, password]):
    print("Set NEO4J_URI/NEO4J_USER/NEO4J_PASSWORD", file=sys.stderr)
    sys.exit(1)

cypher_file = sys.argv[1] if len(sys.argv) > 1 else "scripts/demo.cypher"
stmt = pathlib.Path(cypher_file).read_text(encoding="utf-8")

driver = GraphDatabase.driver(uri, auth=(user, password))
with driver.session() as s:
    for q in stmt.split(";"):
        q = q.strip()
        if q:
            s.run(q)
driver.close()
print("Done.")
