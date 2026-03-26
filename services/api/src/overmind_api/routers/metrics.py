from fastapi import APIRouter, Query

from ..db import get_conn

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])


@router.get("/attention-cost")
async def attention_cost():
    """Return attention cost metrics for all senders, ranked highest first."""
    try:
        async with get_conn() as conn, conn.cursor() as cur:
            await cur.execute("""
                    SELECT person_email, display_name, attention_cost_index,
                           message_count, avg_density, computed_at
                    FROM metrics_attention_cost
                    ORDER BY attention_cost_index DESC
                """)
            rows = await cur.fetchall()
            metrics = [
                {
                    "person_email": row[0],
                    "display_name": row[1],
                    "attention_cost_index": row[2],
                    "message_count": row[3],
                    "avg_density": row[4],
                    "computed_at": row[5].isoformat() if row[5] else None,
                }
                for row in rows
            ]
            return {"metrics": metrics, "count": len(metrics)}
    except Exception as e:
        return {"metrics": [], "count": 0, "error": str(e)}


@router.get("/density")
async def density_distribution(
    limit: int = Query(100, ge=1, le=1000),
):
    """Return information density distribution across classified messages.

    Useful for heatmap visualisation — groups messages by density bucket
    and message type.
    """
    try:
        async with get_conn() as conn, conn.cursor() as cur:
            await cur.execute(
                """
                SELECT
                    message_type,
                    ROUND(information_density::numeric, 1) AS density_bucket,
                    COUNT(*) AS message_count,
                    AVG(information_density) AS avg_density
                FROM classifications
                GROUP BY message_type, ROUND(information_density::numeric, 1)
                ORDER BY density_bucket, message_type
                LIMIT %s
                """,
                (limit,),
            )
            rows = await cur.fetchall()
            buckets = [
                {
                    "message_type": row[0],
                    "density_bucket": float(row[1]),
                    "message_count": row[2],
                    "avg_density": float(row[3]),
                }
                for row in rows
            ]
            return {"buckets": buckets, "count": len(buckets)}
    except Exception as e:
        return {"buckets": [], "count": 0, "error": str(e)}


@router.get("/automation")
async def automation_candidates(
    limit: int = Query(50, ge=1, le=500),
):
    """Return messages flagged as automation candidates, grouped by type."""
    try:
        async with get_conn() as conn, conn.cursor() as cur:
            await cur.execute(
                """
                SELECT
                    automation_type,
                    COUNT(*) AS occurrence_count,
                    AVG(information_density) AS avg_density,
                    AVG(confidence) AS avg_confidence
                FROM classifications
                WHERE automation_candidate = true
                  AND automation_type IS NOT NULL
                GROUP BY automation_type
                ORDER BY occurrence_count DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = await cur.fetchall()
            candidates = [
                {
                    "automation_type": row[0],
                    "occurrence_count": row[1],
                    "avg_density": float(row[2]),
                    "avg_confidence": float(row[3]),
                }
                for row in rows
            ]
            return {"candidates": candidates, "count": len(candidates)}
    except Exception as e:
        return {"candidates": [], "count": 0, "error": str(e)}


@router.get("/message-types")
async def message_type_breakdown():
    """Return message count and avg density grouped by message type."""
    try:
        async with get_conn() as conn, conn.cursor() as cur:
            await cur.execute("""
                SELECT
                    message_type,
                    COUNT(*) AS message_count,
                    AVG(information_density) AS avg_density,
                    SUM(CASE WHEN action_required THEN 1 ELSE 0 END) AS action_required_count
                FROM classifications
                GROUP BY message_type
                ORDER BY message_count DESC
            """)
            rows = await cur.fetchall()
            types = [
                {
                    "message_type": row[0],
                    "message_count": row[1],
                    "avg_density": float(row[2]),
                    "action_required_count": row[3],
                }
                for row in rows
            ]
            return {"types": types, "count": len(types)}
    except Exception as e:
        return {"types": [], "count": 0, "error": str(e)}


@router.get("/sentiment")
async def sentiment_overview():
    """Return sentiment distribution across classified messages."""
    try:
        async with get_conn() as conn, conn.cursor() as cur:
            await cur.execute("""
                SELECT
                    sentiment_valence,
                    COUNT(*) AS message_count,
                    AVG(information_density) AS avg_density
                FROM classifications
                GROUP BY sentiment_valence
                ORDER BY message_count DESC
            """)
            rows = await cur.fetchall()
            sentiments = [
                {
                    "sentiment": row[0],
                    "message_count": row[1],
                    "avg_density": float(row[2]),
                }
                for row in rows
            ]
            return {"sentiments": sentiments, "count": len(sentiments)}
    except Exception as e:
        return {"sentiments": [], "count": 0, "error": str(e)}
