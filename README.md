# PrimePass
This project was built for the Distributed Systems course at the University of Oulu.

# Purpose
 The project aims to reach the following features:

Event ticket sales requires reliable, fault-tolerant systems to handle large amounts of concurrent purchases. The goal is to build a distributed platform for real-time ticket sales and ML-based event recommendations.

Novelty: integrates multiple services (ticket sale, event management, recommendation engine) to ensure consistency, scalability, and personalized suggestions.

The following is a list of features that are to be implemented:
* Introduction: Single-node ticketing simulation with minimal events and users.
* Communication: Build API endpoints for event browsing, ticket reservation, and purchases.
* Concurrency & Consistency: Ensure ticket availability is accurate under heavy traffic.
* Non-Functional Requirements: Fault-tolerant services, horizontal scaling, low-latency responses.
* Replication & Data Management: Each service owns its database; replicate critical data for high availability.
* Resource Management & Load Balancing: Distribute requests across multiple service instances to reduce load on an individual instance.
* System Architecture: Microservices for users, events, tickets, payments, and recommendations using APIs.
* Middleware: Centralized logging, distributed data tracing, and caching of frequently requested data.
* Cloud & Deployment: Containerize services; deploy on Kubernetes or cloud platform with scalable infrastructure.
* ML data collection: Collect user activity and event history for recommendation model training.
* Distributed ML: Provide event suggestions via a scalable recommendation service with  failure handling.
* Personalized recommendations: integrated into event browsing, with fallback to popular events if ML service is unavailable.

# Tools
* Python
* Flask
* Docker
* MariaDB

# Installation

1. Build and start containers in Primepass root folder

        docker-compose up --build -d

Use `populate_db` script to add content (Or if you are trying replication, go to backend/DB_SETUP.md):

        docker exec -it primepass_backend python populate_db.py

2. Test POST request

        curl -X POST "http://localhost:5000/videos" -H "Content-Type: application/json" -d "{\"id\": \"123\"}" # for Windows CMD 

3. Test GET request

        curl -X GET "http://localhost:5000/videos?id=123"

4. Stop containers when done

        docker-compose down


# Note
Qui laborum fugiat sunt dolor. Corrupti velit laboriosam magni voluptatum ipsam dicta. Facere voluptatem quo expedita delectus aut libero maiores. Iure quaerat commodi rerum illum ab voluptatem quis non. Vitae nobis dignissimos ullam id deserunt enim optio.

Ullam aperiam animi qui perspiciatis consequatur dolores. Ea recusandae consequatur necessitatibus dolorem. Sed doloremque adipisci ut natus velit. Sed quam magni natus natus ea ut rerum est.
