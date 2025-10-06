"""Query GPT helpers for translating natural language to SQL."""

from __future__ import annotations

import datetime as dt
import json
import re
import sqlite3
import textwrap
from typing import Any, Dict, List, Tuple

from web.config import (
    QUERY_GPT_DB_PATH,
    QUERY_GPT_HISTORY_LIMIT,
    QUERY_SCHEMA_TTL,
)
from web.services.llm import call_openai, is_openai_configured

query_gpt_history: List[Dict[str, Any]] = []
query_schema_cache: Dict[str, Any] = {}
_query_schema_cached_at: dt.datetime | None = None

FORBIDDEN_SQL_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\bDROP\b",
        r"\bDELETE\b",
        r"\bUPDATE\b",
        r"\bINSERT\b",
        r"\bALTER\b",
        r"\bTRUNCATE\b",
        r";\s*$",
    ]
]


def get_query_db() -> sqlite3.Connection:
    conn = sqlite3.connect(QUERY_GPT_DB_PATH)
    conn.row_factory = sqlite3.Row
    seed_query_demo_db(conn)
    return conn


def seed_query_demo_db(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys = ON")
    with conn:
        conn.executescript(
            """
        CREATE TABLE IF NOT EXISTS product_metrics (
            id INTEGER PRIMARY KEY,
            product TEXT NOT NULL,
            snapshot_date TEXT NOT NULL,
            active_users INTEGER NOT NULL,
            conversion_rate REAL NOT NULL,
            revenue REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS traffic_sources (
            id INTEGER PRIMARY KEY,
            source TEXT NOT NULL,
            metric_date TEXT NOT NULL,
            sessions INTEGER NOT NULL,
            signups INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS support_tickets (
            id INTEGER PRIMARY KEY,
            opened_at TEXT NOT NULL,
            closed_at TEXT,
            customer_tier TEXT NOT NULL,
            status TEXT NOT NULL,
            category TEXT NOT NULL
        );
        """
        )
        product_rows = [
            (1, "Core", "2024-01-01", 1320, 0.34, 45210.0),
            (2, "Core", "2024-02-01", 1480, 0.36, 48750.0),
            (3, "Pro", "2024-01-01", 620, 0.42, 39120.0),
            (4, "Pro", "2024-02-01", 705, 0.44, 41500.0),
            (5, "Studio", "2024-02-01", 280, 0.29, 15230.0),
        ]
        traffic_rows = [
            (1, "Search", "2024-02-01", 5200, 640),
            (2, "Paid", "2024-02-01", 3100, 410),
            (3, "Referral", "2024-02-01", 1700, 305),
            (4, "Email", "2024-02-01", 2200, 510),
            (5, "Community", "2024-02-01", 950, 180),
        ]
        support_rows = [
            (1, "2024-01-03", "2024-01-04", "Enterprise", "closed", "onboarding"),
            (2, "2024-01-05", "2024-01-09", "Growth", "closed", "billing"),
            (3, "2024-01-12", None, "Enterprise", "open", "integration"),
            (4, "2024-02-02", "2024-02-03", "Starter", "closed", "bug"),
            (5, "2024-02-05", None, "Growth", "open", "feature-request"),
        ]

        conn.executemany(
            "INSERT OR IGNORE INTO product_metrics VALUES (?, ?, ?, ?, ?, ?)", product_rows
        )
        conn.executemany(
            "INSERT OR IGNORE INTO traffic_sources VALUES (?, ?, ?, ?, ?)", traffic_rows
        )
        conn.executemany(
            "INSERT OR IGNORE INTO support_tickets VALUES (?, ?, ?, ?, ?, ?)", support_rows
        )


def introspect_query_schema(force: bool = False) -> Dict[str, Any]:
    global query_schema_cache, _query_schema_cached_at
    now = dt.datetime.now()
    if (
        not force
        and query_schema_cache
        and _query_schema_cached_at
        and now - _query_schema_cached_at < QUERY_SCHEMA_TTL
    ):
        return query_schema_cache

    conn = get_query_db()
    try:
        tables = []
        table_rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        for row in table_rows:
            table_name = row[0]
            columns = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
            sample_rows = conn.execute(f"SELECT * FROM {table_name} LIMIT 3").fetchall()
            tables.append(
                {
                    "name": table_name,
                    "columns": [
                        {
                            "name": column[1],
                            "type": column[2],
                            "nullable": not bool(column[3]),
                        }
                        for column in columns
                    ],
                    "sample_rows": [dict(sample) for sample in sample_rows],
                }
            )
    finally:
        conn.close()

    query_schema_cache = {"tables": tables, "refreshed_at": now.isoformat()}
    _query_schema_cached_at = now
    return query_schema_cache


def format_schema_description(schema: Dict[str, Any]) -> str:
    lines = []
    for table in schema.get("tables", []):
        column_descriptions = ", ".join(
            f"{col['name']} {col['type']}" + (" NULL" if col["nullable"] else " NOT NULL")
            for col in table.get("columns", [])
        )
        lines.append(f"Table {table['name']}: {column_descriptions}")
        if table.get("sample_rows"):
            lines.append("Sample rows:")
            for sample in table["sample_rows"]:
                lines.append(json.dumps(sample))
        lines.append("")
    return "\n".join(lines).strip()


def extract_structured_json(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            return {}
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}


def sanitise_sql(sql: str) -> str:
    statement = sql.strip()
    if not statement:
        return statement
    statement = statement.replace("\n", " ")
    return re.sub(r"\s+", " ", statement)


def detect_sql_risk(sql: str) -> Tuple[bool, str | None]:
    statement = sql.strip()
    if not statement:
        return True, "No SQL was generated."
    if not statement.lower().startswith("select"):
        return True, "Only SELECT queries are allowed."
    for pattern in FORBIDDEN_SQL_PATTERNS:
        if pattern.search(statement):
            return True, "Query contains a forbidden operation."
    return False, None


def ensure_limit_clause(sql: str, default_limit: int = 200) -> str:
    statement = sql.strip().rstrip(";")
    if " limit " in statement.lower():
        return statement
    return f"{statement} LIMIT {default_limit}"


def run_sql(sql: str) -> Dict[str, Any]:
    conn = get_query_db()
    start = dt.datetime.now()
    try:
        with conn:
            cursor = conn.execute(sql)
            rows = cursor.fetchmany(201)
            truncated = len(rows) == 201
            preview = [dict(row) for row in rows[:200]]
    finally:
        conn.close()

    duration_ms = (dt.datetime.now() - start).total_seconds() * 1000
    return {
        "rows": preview,
        "truncated": truncated,
        "runtime_ms": round(duration_ms, 2),
        "row_count": len(preview),
    }


def generate_offline_sql_plan(question: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    lowered = question.lower()

    if "revenue" in lowered:
        sql = (
            "SELECT metric_date, product, SUM(revenue) AS total_revenue "
            "FROM product_metrics GROUP BY metric_date, product ORDER BY metric_date"
        )
        rationale = "Assumes revenue per product over time lives in product_metrics."
        confidence = 0.6
    elif "conversion" in lowered:
        sql = (
            "SELECT metric_date, product, AVG(conversion_rate) AS avg_conversion_rate "
            "FROM product_metrics GROUP BY metric_date, product ORDER BY metric_date"
        )
        rationale = "Uses conversion_rate column from product_metrics to estimate averages."
        confidence = 0.55
    elif "active" in lowered and "user" in lowered:
        sql = (
            "SELECT metric_date, product, SUM(active_users) AS active_users "
            "FROM product_metrics GROUP BY metric_date, product ORDER BY metric_date"
        )
        rationale = "Aggregates active_users from product_metrics by product and date."
        confidence = 0.5
    elif "ticket" in lowered or "support" in lowered:
        sql = (
            "SELECT status, category, COUNT(*) AS ticket_count "
            "FROM support_tickets GROUP BY status, category ORDER BY ticket_count DESC"
        )
        rationale = "Summarises support_tickets by status and category."
        confidence = 0.45
    elif "signup" in lowered or "traffic" in lowered:
        sql = (
            "SELECT metric_date, source, sessions, signups, "
            "ROUND(CASE WHEN sessions = 0 THEN 0 ELSE CAST(signups AS FLOAT)/sessions END, 3) AS signup_rate "
            "FROM traffic_sources ORDER BY metric_date, source"
        )
        rationale = "Pulls sessions/signups from traffic_sources and calculates signup rate."
        confidence = 0.5
    else:
        sql = "SELECT * FROM product_metrics ORDER BY metric_date LIMIT 50"
        rationale = "Default fallback: inspect recent rows in product_metrics."
        confidence = 0.3

    return {
        "sql": sql,
        "confidence": confidence,
        "rationale": rationale,
        "schema_snapshot": schema,
        "raw_response": None,
        "offline": True,
    }


def generate_text_to_sql_plan(question: str) -> Dict[str, Any]:
    schema = introspect_query_schema()

    if not is_openai_configured():
        return generate_offline_sql_plan(question, schema)
    schema_description = format_schema_description(schema)
    prompt = textwrap.dedent(
        f"""
        You are a cautious analytics engineer producing SQL for a read-only sqlite database.
        Use only the provided schema and respond with a JSON object containing:
        - sql: string SELECT statement or empty string if answering is impossible
        - confidence: float between 0 and 1
        - rationale: brief explanation of assumptions
        Rules:
        - Only emit SELECT statements.
        - Prefer safe filters and LIMIT clauses when helpful.
        - Explain if the question cannot be answered.

        Schema reference:
        {schema_description}
        """
    ).strip()

    response = call_openai(
        [
            {
                "role": "system",
                "content": "You translate product analytics questions into safe, read-only SQL and reply strictly as JSON.",
            },
            {
                "role": "user",
                "content": f"Question: {question}\n\nReturn JSON with keys sql, confidence, rationale.\n\n{prompt}",
            },
        ]
    )

    if not response or response.lower().startswith("openai api key not configured"):
        return {"error": response or "OpenAI call failed."}

    structured = extract_structured_json(response)
    if not structured:
        return {"error": "Model response was not valid JSON.", "raw": response}

    structured.setdefault("sql", "")
    structured.setdefault("confidence", 0.0)
    structured.setdefault("rationale", "")

    try:
        structured["confidence"] = float(structured["confidence"])
    except (ValueError, TypeError):
        structured["confidence"] = 0.0
    structured["sql"] = str(structured.get("sql", ""))
    structured["rationale"] = str(structured.get("rationale", ""))
    structured["raw_response"] = response
    structured["schema_snapshot"] = schema
    return structured


def push_query_history(entry: Dict[str, Any]) -> None:
    query_gpt_history.append(entry)
    excess = len(query_gpt_history) - QUERY_GPT_HISTORY_LIMIT
    if excess > 0:
        del query_gpt_history[:excess]


def parse_bool_flag(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y", "run"}


def process_query_request(question_text: str, run_flag: bool) -> Tuple[Dict[str, Any], int]:
    if not question_text:
        schema = introspect_query_schema()
        payload = {
            "message": "Submit a question to generate SQL.",
            "schema": schema,
            "history": query_gpt_history[-5:],
        }
        return payload, 200

    plan = generate_text_to_sql_plan(question_text)
    payload: Dict[str, Any] = {
        "timestamp": dt.datetime.utcnow().isoformat() + "Z",
        "question": question_text,
        "requested_run": run_flag,
    }
    status_code = 200

    if plan.get("error"):
        payload.update(
            {
                "error": plan["error"],
                "raw_response": plan.get("raw_response") or plan.get("raw"),
                "schema_snapshot": plan.get("schema_snapshot"),
            }
        )
        push_query_history(payload)
        return payload, 502

    sql = sanitise_sql(str(plan.get("sql", "")))
    risk_flagged, risk_reason = detect_sql_risk(sql)
    payload.update(
        {
            "sql": sql,
            "confidence": plan.get("confidence", 0.0),
            "rationale": plan.get("rationale", ""),
            "risk_flagged": risk_flagged,
            "risk_reason": risk_reason,
            "schema_snapshot": plan.get("schema_snapshot"),
            "raw_response": plan.get("raw_response"),
            "offline": plan.get("offline", False),
        }
    )

    if run_flag and not risk_flagged and sql:
        safe_sql = ensure_limit_clause(sql)
        execution_details = run_sql(safe_sql)
        payload["sql"] = safe_sql
        payload["execution"] = execution_details
    elif run_flag and risk_flagged:
        payload["warning"] = "Query execution blocked due to safety checks."

    push_query_history(payload)
    return payload, status_code

__all__ = [
    "query_gpt_history",
    "get_query_db",
    "introspect_query_schema",
    "generate_text_to_sql_plan",
    "generate_offline_sql_plan",
    "process_query_request",
    "parse_bool_flag",
    "sanitise_sql",
    "detect_sql_risk",
    "ensure_limit_clause",
]
