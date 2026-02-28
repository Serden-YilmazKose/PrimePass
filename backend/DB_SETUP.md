# MariaDB Primary–Replica Replication Setup (Minimal Commands)

## Overview of Replication
MariaDB replication allows one database server (the **primary**) to automatically copy all data and schema changes to one or more **replica** servers.  
- **Primary**: Handles all writes and schema changes.  
- **Replica**: Follows the primary, reflecting its state. Used for read-scaling, backup, or failover.  
- **Important**: Schema creation and migrations should only run on the primary. Replicas automatically replicate all changes.

---

## 1. Start Containers
    docker compose down -v

    docker compose build
    docker compose up -d

---

## 2. Configure Primary for Replication
 Enter the primary container, password is pass
      
      docker exec -it mariadb_primary mariadb -u root -p

 Inside MariaDB prompt:

      USE primepass_db;

        CREATE USER 'replica'@'%' IDENTIFIED BY 'pass';
        GRANT REPLICATION SLAVE ON *.* TO 'replica'@'%';
        FLUSH PRIVILEGES;
        SHOW MASTER STATUS;

 Note the File and Position values for the replica setup

Then, `exit`

### 2a. Initialize Replica with Primary Data (Schema + Initial Data)

Before starting replication, the replica must have the database and tables from the primary.

On the host:

      
Dump the primary database using your backend container

      docker exec -i primepass_backend sh -c \
      "mysqldump -h mariadb_primary -u root -p --databases primepass_db --single-transaction --master-data=2" > primepass_db.sql

      docker exec -i mariadb_replica1 mariadb -u root -p < primepass_db.sql

---

## 3. Configure Replica
 Enter the replica container, password is pass

      docker exec -it mariadb_replica1 mariadb -u root -p

 Inside MariaDB prompt:

        CHANGE MASTER TO
            MASTER_HOST='mariadb_primary',
            MASTER_USER='replica',
            MASTER_PASSWORD='pass',
            MASTER_LOG_FILE='[File from primary]',
            MASTER_LOG_POS=[Position from primary];

        START SLAVE;
        SHOW SLAVE STATUS\G

 Ensure Slave_IO_Running: Yes and Slave_SQL_Running: Yes

---

## 4. Initialize Database and Tables via Application
 Run populate_db script against the primary

      docker exec -it primepass_backend python populate_db.py

 This creates all tables and seed data on the primary; replicas will automatically replicate it

---

## 5. Verify Replication on Replica
 Enter the replica container
    docker exec -it mariadb_replica1 mariadb -u root -p

 Inside MariaDB prompt:

        USE primepass_db;
        SELECT * FROM events;

 The replica should automatically have the same tables and rows as the primary

---

## 6. Test Live Replication
 Insert new data on primary
    docker exec -it mariadb_primary mariadb -u root -p

 Inside MariaDB prompt:

        USE primepass_db;
        INSERT INTO events (name, date, available) VALUES ('Pop Festival', '2026-06-15', 40);

 Check on replica
    docker exec -it mariadb_replica1 mariadb -u root -p

 Inside MariaDB prompt:

        USE primepass_db;
        SELECT * FROM events;

 New row should appear automatically on the replica