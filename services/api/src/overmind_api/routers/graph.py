from fastapi import APIRouter, Query
from psycopg import sql

from ..db import get_conn

router = APIRouter(prefix="/api/v1/graph", tags=["graph"])


def _strip_agtype(val) -> str:
    """Strip AGE agtype quoting from a returned value."""
    return str(val).strip('"')


def _age_escape(value: str) -> str:
    """Escape a string value for embedding in AGE Cypher.

    Apache AGE does NOT support Cypher parameterisation through the SQL
    wrapper — values must be interpolated into the Cypher string.
    This mirrors the escaping in graph-writer/queries.py.
    """
    return value.replace("\\", "\\\\").replace("'", "\\'")


@router.get("/persons")
async def list_persons():
    """Return all Person nodes from the AGE graph."""
    try:
        async with get_conn() as conn, conn.cursor() as cur:
            await cur.execute("LOAD 'age';")
            await cur.execute('SET search_path = ag_catalog, "$user", public;')
            await cur.execute("""
                    SELECT * FROM ag_catalog.cypher('overmind', $$
                        MATCH (p:Person)
                        RETURN p.email, p.display_name, p.domain, p.internal
                    $$) AS (email ag_catalog.agtype, display_name ag_catalog.agtype,
                            domain ag_catalog.agtype, internal ag_catalog.agtype);
                """)
            rows = await cur.fetchall()
            persons = [
                {
                    "email": _strip_agtype(row[0]),
                    "display_name": _strip_agtype(row[1]),
                    "domain": _strip_agtype(row[2]),
                    "internal": _strip_agtype(row[3]).lower() == "true",
                }
                for row in rows
            ]
            return {"persons": persons, "count": len(persons)}
    except Exception as e:
        return {"persons": [], "count": 0, "error": str(e)}


def _person_outbound_query(email: str) -> str:
    """Build AGE Cypher SQL for outbound SENT_TO edges.

    AGE requires Cypher embedded in a SQL function call — standard SQL
    parameterisation cannot reach inside the Cypher string, so we escape
    the value and interpolate it into the Cypher literal.
    """
    escaped = _age_escape(email)
    return f"""
    SELECT * FROM ag_catalog.cypher('overmind', $$
        MATCH (s:Person {{email: '{escaped}'}})-[e:SENT_TO]->(r:Person)
        RETURN r.email, r.display_name, e.count, e.avg_density, e.last_at
    $$) AS (email ag_catalog.agtype, display_name ag_catalog.agtype,
            msg_count ag_catalog.agtype, avg_density ag_catalog.agtype,
            last_at ag_catalog.agtype);
    """


def _person_inbound_query(email: str) -> str:
    """Build AGE Cypher SQL for inbound SENT_TO edges."""
    escaped = _age_escape(email)
    return f"""
    SELECT * FROM ag_catalog.cypher('overmind', $$
        MATCH (s:Person)-[e:SENT_TO]->(r:Person {{email: '{escaped}'}})
        RETURN s.email, s.display_name, e.count, e.avg_density, e.last_at
    $$) AS (email ag_catalog.agtype, display_name ag_catalog.agtype,
            msg_count ag_catalog.agtype, avg_density ag_catalog.agtype,
            last_at ag_catalog.agtype);
    """


def _parse_connection_rows(rows) -> list[dict]:
    return [
        {
            "email": _strip_agtype(r[0]),
            "display_name": _strip_agtype(r[1]),
            "message_count": int(_strip_agtype(r[2])) if r[2] else 0,
            "avg_density": float(_strip_agtype(r[3])) if r[3] else 0.0,
            "last_at": _strip_agtype(r[4]) if r[4] else None,
        }
        for r in rows
    ]


@router.get("/persons/{email}/connections")
async def person_connections(email: str):
    """Return SENT_TO edges for a specific person (both directions)."""
    try:
        async with get_conn() as conn, conn.cursor() as cur:
            await cur.execute("LOAD 'age';")
            await cur.execute('SET search_path = ag_catalog, "$user", public;')

            await cur.execute(sql.SQL(_person_outbound_query(email)))
            outbound = _parse_connection_rows(await cur.fetchall())

            await cur.execute(sql.SQL(_person_inbound_query(email)))
            inbound = _parse_connection_rows(await cur.fetchall())

            return {
                "person": email,
                "sends_to": outbound,
                "receives_from": inbound,
            }
    except Exception as e:
        return {"person": email, "sends_to": [], "receives_from": [], "error": str(e)}


@router.get("/threads")
async def list_threads(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Return classified messages with pagination."""
    try:
        async with get_conn() as conn, conn.cursor() as cur:
            await cur.execute(
                """
                SELECT
                    c.message_id,
                    c.message_type,
                    c.thread_role,
                    c.information_density,
                    c.action_required,
                    c.classified_at
                FROM classifications c
                ORDER BY c.classified_at DESC
                LIMIT %s OFFSET %s
                """,
                (limit, offset),
            )
            rows = await cur.fetchall()
            messages = [
                {
                    "message_id": row[0],
                    "message_type": row[1],
                    "thread_role": row[2],
                    "information_density": row[3],
                    "action_required": row[4],
                    "classified_at": row[5].isoformat() if row[5] else None,
                }
                for row in rows
            ]
            return {"messages": messages, "count": len(messages)}
    except Exception as e:
        return {"messages": [], "count": 0, "error": str(e)}
