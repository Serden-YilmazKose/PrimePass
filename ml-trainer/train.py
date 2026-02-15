import os
import pandas as pd
import redis
import json
from collections import Counter

LOG_FILE = "/logs/purchases.log"
POPULAR_KEY = "popular_events"
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")

def train():
    # Read purchase logs
    if not os.path.exists(LOG_FILE):
        print("No purchase log found. Generating dummy data...")
        # Create dummy data for demonstration
        generate_dummy_data()

    df = pd.read_csv(LOG_FILE, names=["timestamp", "user_id", "event_id", "quantity"])
    # Compute popular events (most frequently purchased)
    popular_event_ids = df["event_id"].value_counts().head(10).index.tolist()

    # Store in Redis
    r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
    r.set(POPULAR_KEY, json.dumps(popular_event_ids))
    print(f"Popular events updated: {popular_event_ids}")

    # Optionally compute per-user recommendations (simple: user's most purchased + popular)
    # For demonstration, we'll just set a dummy recommendation for each user
    user_purchases = df.groupby("user_id")["event_id"].apply(list).to_dict()
    for user_id, events in user_purchases.items():
        # Simple: top events bought by this user, fallback to popular
        user_counter = Counter(events)
        user_top = [eid for eid, _ in user_counter.most_common(5)]
        # Merge with popular, deduplicate
        recs = list(dict.fromkeys(user_top + popular_event_ids))[:10]
        r.setex(f"rec:{user_id}", 86400, json.dumps(recs))  # 24h TTL

    print("Recommendations stored in Redis.")

def generate_dummy_data():
    import random
    from datetime import datetime, timedelta
    with open(LOG_FILE, "w") as f:
        for _ in range(1000):
            ts = (datetime.utcnow() - timedelta(days=random.randint(0,30))).isoformat()
            user = random.randint(1,20)
            event = random.randint(1,5)
            qty = random.randint(1,3)
            f.write(f"{ts},{user},{event},{qty}\n")
    print("Dummy purchase log generated.")

if __name__ == "__main__":
    train()