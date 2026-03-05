def test_event_payload_sizes(api_client, db_cursor):
    """Test handling of events with small and large payloads on an empty database."""
    import random
    import string
    import time
    from datetime import datetime, timedelta

    # Helper to generate random strings
    def random_string(length):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    # --- Clear all events (cascade deletes tickets) ---
    db_cursor.execute("DELETE FROM event")
    db_cursor.connection.commit()
    print("\n--- Event Payload Test (starting with empty database) ---")

    # --- Create small event ---
    small_title = "Small Event"
    small_desc = random_string(100)          # short description
    small_tickets = 3
    db_cursor.execute("""
        INSERT INTO event (title, venue, city, description, starts_at, ends_at, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
    """, (small_title, "Small Venue", "Small City", small_desc,
          datetime.now(), datetime.now() + timedelta(hours=1), "active"))
    small_event_id = db_cursor.fetchone()[0]

    for i in range(small_tickets):
        db_cursor.execute("""
            INSERT INTO ticket (event_id, name, price, capacity, remaining)
            VALUES (%s, %s, %s, %s, %s)
        """, (small_event_id, f"Ticket {i}", 10.0, 100, 100))

    db_cursor.connection.commit()

    # --- Fetch events (should contain only small event) ---
    start = time.time()
    resp = api_client.get(f"{api_client.base_url}/api/events")
    elapsed_small = time.time() - start
    content_size_small = len(resp.content)   # response size in bytes

    assert resp.status_code == 200
    events = resp.json()

    small_event = next((e for e in events if e["title"] == small_title), None)
    assert small_event is not None, "Small event not found"
    assert len(small_event["tickets"]) == small_tickets

    print(f"Small event inserted. Tickets: {small_tickets}, "
          f"Response time: {elapsed_small:.3f}s, Response size: {content_size_small} bytes")

    # --- Create large event ---
    large_title = "Large Event with many tickets and long description"
    large_desc = random_string(5000)          # 5 KB description
    large_tickets = 50
    db_cursor.execute("""
        INSERT INTO event (title, venue, city, description, starts_at, ends_at, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
    """, (large_title, "Large Venue", "Large City", large_desc,
          datetime.now(), datetime.now() + timedelta(hours=2), "active"))
    large_event_id = db_cursor.fetchone()[0]

    for i in range(large_tickets):
        db_cursor.execute("""
            INSERT INTO ticket (event_id, name, price, capacity, remaining)
            VALUES (%s, %s, %s, %s, %s)
        """, (large_event_id, f"Ticket {i}", 10.0 + i, 100, 100))

    db_cursor.connection.commit()

    # --- Fetch events again (should contain both) ---
    start = time.time()
    resp = api_client.get(f"{api_client.base_url}/api/events")
    elapsed_large = time.time() - start
    content_size_large = len(resp.content)

    assert resp.status_code == 200
    events = resp.json()

    large_event = next((e for e in events if e["title"] == large_title), None)
    assert large_event is not None, "Large event not found"
    assert len(large_event["tickets"]) == large_tickets

    print(f"Large event inserted. Tickets: {large_tickets}, "
          f"Response time: {elapsed_large:.3f}s, Response size: {content_size_large} bytes")
    print(f"Total events now in DB: {len(events)}")