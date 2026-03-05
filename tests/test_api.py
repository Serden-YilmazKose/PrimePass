import pytest
import requests

def test_get_events(api_client):
    """GET /api/events should return a list of events with tickets."""
    resp = api_client.get(f"{api_client.base_url}/api/events")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    if data:  
        event = data[0]
        assert "id" in event
        assert "title" in event
        assert "tickets" in event
        assert isinstance(event["tickets"], list)

def test_login_new_user(api_client):
    """POST /api/login should register a new user if email not found."""
    import uuid
    unique = str(uuid.uuid4())[:8]
    payload = {
        "name": "New User",
        "email": f"newuser_{unique}@test.com",
        "password": "secret"
    }
    resp = api_client.post(f"{api_client.base_url}/api/login", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "user_created"
    assert "user_id" in data

def test_login_existing_user(api_client, test_user):
    """POST /api/login should authenticate existing user."""
    payload = {
        "email": test_user["email"],
        "password": test_user["password"]
    }
    resp = api_client.post(f"{api_client.base_url}/api/login", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "login_success"
    assert data["user_id"] == test_user["id"]

def test_purchase_ticket(api_client, test_user, test_event):
    """POST /api/purchase should successfully buy tickets."""
    ticket_id = test_event["tickets"]["Standard"]
    payload = {
        "user_id": test_user["id"],
        "ticket_id": ticket_id,
        "quantity": 2
    }
    resp = api_client.post(f"{api_client.base_url}/api/purchase", json=payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"

def test_purchase_insufficient_tickets(api_client, test_user, test_event):
    """Attempt to buy more tickets than available."""
    ticket_id = test_event["tickets"]["VIP"]  
   
    payload1 = {"user_id": test_user["id"], "ticket_id": ticket_id, "quantity": 5}
    resp1 = api_client.post(f"{api_client.base_url}/api/purchase", json=payload1)
    assert resp1.status_code == 200

    
    payload2 = {"user_id": test_user["id"], "ticket_id": ticket_id, "quantity": 1}
    resp2 = api_client.post(f"{api_client.base_url}/api/purchase", json=payload2)
    assert resp2.status_code == 400
    assert "sold out" in resp2.json()["error"].lower()

def test_get_orders(api_client, test_user, test_event):
    """GET /api/orders?user_id=... should return user's orders."""
    
    ticket_id = test_event["tickets"]["Standard"]
    api_client.post(f"{api_client.base_url}/api/purchase", json={
        "user_id": test_user["id"],
        "ticket_id": ticket_id,
        "quantity": 1
    })

   
    resp = api_client.get(f"{api_client.base_url}/api/orders", params={"user_id": test_user["id"]})
    assert resp.status_code == 200
    orders = resp.json()
    assert isinstance(orders, list)
    assert len(orders) >= 1
    order = orders[0]
    assert "order_id" in order
    assert "ticket_name" in order

def test_track_activity(api_client, test_user, test_event):
    """POST /api/activity should log user activity."""
    payload = {
        "user_id": test_user["id"],
        "event_id": test_event["event_id"],
        "action": "view",
        "meta": {"source": "test"}
    }
    resp = api_client.post(f"{api_client.base_url}/api/activity", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "ok"
    assert "activity_id" in data
