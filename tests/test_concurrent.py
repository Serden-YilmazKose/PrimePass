import pytest
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def test_concurrent_purchases(api_client, test_user, test_event):
    """
    Simulate many users trying to buy tickets for the same event concurrently.
    Oversubscribe a limited ticket pool and verify correct handling:
    - No overselling
    - Expected 'sold out' responses for excess requests
    - No unexpected errors (e.g., 500, timeouts)
    """
    ticket_id = test_event["tickets"]["Standard"]
    available = 10
    num_requests = 20
    quantity_per_request = 1

    def purchase(i):
        url = f"{api_client.base_url}/api/purchase"
        payload = {
            "user_id": test_user["id"],
            "ticket_id": ticket_id,
            "quantity": quantity_per_request
        }
        start = time.time()
        try:
            resp = requests.post(url, json=payload, timeout=5)
            elapsed = time.time() - start
            return {
                "status_code": resp.status_code,
                "text": resp.text,
                "elapsed": elapsed,
                "exception": None
            }
        except Exception as e:
            elapsed = time.time() - start
            return {
                "status_code": None,
                "text": str(e),
                "elapsed": elapsed,
                "exception": e
            }

    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(purchase, i) for i in range(num_requests)]
        for future in as_completed(futures):
            results.append(future.result())

    # Categorise results
    successes = [r for r in results if r["status_code"] == 200]
    expected_failures = [
        r for r in results
        if r["status_code"] == 400 and "sold out" in r["text"].lower()
    ]
    unexpected_failures = [
        r for r in results
        if r not in successes and r not in expected_failures
    ]

    print(f"\n--- Concurrent Purchase Test ---")
    print(f"Total requests:          {num_requests}")
    print(f"Successful purchases:    {len(successes)}")
    print(f"Expected failures (sold out): {len(expected_failures)}")
    print(f"Unexpected failures:     {len(unexpected_failures)}")

    # Verify no overselling
    total_sold = len(successes) * quantity_per_request
    assert total_sold <= available, f"Oversold! Sold {total_sold} of {available}"

    # Verify all unexpected failures are zero
    assert len(unexpected_failures) == 0, \
        f"Unexpected failures occurred: {unexpected_failures}"

    # Latency for successful purchases
    if successes:
        latencies = [r["elapsed"] for r in successes]
        avg_latency = sum(latencies) / len(latencies)
        print(f"Avg latency (success):   {avg_latency:.3f}s")
        print(f"Min latency:             {min(latencies):.3f}s")
        print(f"Max latency:             {max(latencies):.3f}s")

    # Correct handling rate = (successes + expected_failures) / total * 100
    correct = len(successes) + len(expected_failures)
    correct_rate = correct / num_requests * 100
    print(f"Correct handling rate:   {correct_rate:.1f}%")
    print(f"Unexpected error rate:   {len(unexpected_failures)/num_requests*100:.1f}%")