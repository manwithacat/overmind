def test_upsert_person_cypher():
    from overmind_graph_writer.queries import upsert_person_cypher

    sql = upsert_person_cypher("alice@overmind.local", "Alice", "overmind.local", True)
    assert "ag_catalog.cypher" in sql
    assert "MERGE" in sql
    assert "alice@overmind.local" in sql
    assert "true" in sql  # internal flag


def test_upsert_sent_to_cypher():
    from overmind_graph_writer.queries import upsert_sent_to_cypher

    sql = upsert_sent_to_cypher("alice@overmind.local", "bob@overmind.local", 0.7)
    assert "alice@overmind.local" in sql
    assert "bob@overmind.local" in sql
    assert "SENT_TO" in sql


def test_age_escape_handles_quotes():
    from overmind_graph_writer.queries import _age_escape

    assert _age_escape("O'Brien") == "O\\'Brien"
    assert _age_escape("back\\slash") == "back\\\\slash"
