from fastapi import APIRouter

from ..db import get_conn

router = APIRouter(prefix="/api/v1/graph", tags=["graph"])


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
            persons = []
            for row in rows:
                persons.append(
                    {
                        "email": str(row[0]).strip('"'),
                        "display_name": str(row[1]).strip('"'),
                        "domain": str(row[2]).strip('"'),
                        "internal": str(row[3]).lower() == "true",
                    }
                )
            return {"persons": persons, "count": len(persons)}
    except Exception as e:
        return {"persons": [], "count": 0, "error": str(e)}
