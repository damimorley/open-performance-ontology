CREATE CONSTRAINT cleaned IF NOT EXISTS
FOR (a:Athlete) REQUIRE a.athlete_id IS UNIQUE;

MERGE (a:Athlete {athlete_id: "ath-001", coach_id: "doe"})
MERGE (s:Session {session_id: "sess-001", ts: datetime("2025-08-01T10:00:00Z"), coach_id: "doe"})
MERGE (m:Metric {name: "HR", unit: "bpm", value: 148.0, coach_id: "doe"})
MERGE (a)-[:ATTENDED]->(s)
MERGE (s)-[:RECORDED]->(m);
