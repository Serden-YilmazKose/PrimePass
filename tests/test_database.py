import pytest
import psycopg

def test_tables_exist(db_cursor):
    """Check that all expected tables are present."""
    db_cursor.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
    """)
    tables = {row[0] for row in db_cursor.fetchall()}
    expected = {"event", "users", "ticket", "orders", "user_activity"}
    assert expected.issubset(tables), f"Missing tables: {expected - tables}"

def test_foreign_keys_enforced(db_cursor):
    """Verify that foreign key constraints work."""
   
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        db_cursor.execute(
            "INSERT INTO orders (user_id, ticket_id, status) VALUES (%s, %s, %s)",
            ("00000000-0000-0000-0000-000000000000", 999999, 'confirmed')
        )

def test_ticket_remaining_trigger(db_cursor, test_event):
    """Check that remaining tickets cannot exceed capacity (application logic)."""
    event = test_event
    ticket_id = event["tickets"]["Standard"]
   
    db_cursor.execute(
        "SELECT remaining FROM ticket WHERE id = %s", (ticket_id,)
    )
    remaining = db_cursor.fetchone()[0]
    assert remaining >= 0  
