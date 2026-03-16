from fastapi import APIRouter

from ..db import get_conn

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])


@router.get("/attention-cost")
async def attention_cost():
    """Return attention cost metrics for all senders."""
    try:
        async with get_conn() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    SELECT person_email, display_name, attention_cost_index,
                           message_count, avg_density, computed_at
                    FROM metrics_attention_cost
                    ORDER BY attention_cost_index DESC
                """)
                rows = await cur.fetchall()
                metrics = []
                for row in rows:
                    metrics.append({
                        "person_email": row[0],
                        "display_name": row[1],
                        "attention_cost_index": row[2],
                        "message_count": row[3],
                        "avg_density": row[4],
                        "computed_at": row[5].isoformat() if row[5] else None,
                    })
                return {"metrics": metrics, "count": len(metrics)}
    except Exception as e:
        return {"metrics": [], "count": 0, "error": str(e)}
