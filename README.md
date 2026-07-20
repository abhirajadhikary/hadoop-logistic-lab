<p align="center">
  <img width="2974" height="1094" alt="Logistics Big Data Pipeline" src="https://github.com/user-attachments/assets/e144db84-929a-4242-90dd-bd12f7d33e44" />
</p>

---

# Logistics Hadoop Big Data Pipeline

A comprehensive **end-to-end big data engineering platform** for logistics analytics built on the Hadoop ecosystem. This project demonstrates how to ingest, process, store, and analyze large-scale shipment and tracking data using industry-standard distributed technologies.

The implementation covers the complete data lifecycle: from raw data ingestion through HDFS and Kafka, multi-stage ETL transformations using Apache Spark, storage in Apache Cassandra, workflow orchestration with Airflow, and interactive analytics dashboards powered by Gradio and FastAPI.

This is a **production-grade reference implementation** showcasing real-world data engineering patterns rather than standalone technology tutorials.

---

# Project Overview

The platform processes logistics data from multiple sources to generate actionable business intelligence:

* **Shipment Data**
  * Shipment identifiers and metadata
  * Origin and destination information
  * Weight, declared value, and carrier details

* **Tracking Events**
  * Real-time event stream from shipments
  * Event types: Pick-up, In Transit, Delivery, Exceptions
  * Timestamps and location updates

* **Business Analytics**
  * Delivery performance metrics
  * Route optimization insights
  * Shipment snapshots and KPIs

---

# Data Pipeline Architecture

```text
                    Data Sources
           ┌────────────┬──────────────┐
           │            │              │
           ▼            ▼              ▼
    Shipment Data  Tracking Events  (Streaming)
           │            │              │
           └────────────┬──────────────┘
                        ▼
                    ┌──────────┐
                    │  Kafka   │
                    └──────────┘
                        │
                        ▼
                ┌───────────────────┐
                │  HDFS (Bronze)    │
                └───────────────────┘
                        │
                        ▼
         ┌──────────────────────────────────┐
         │                                  │
         ▼                                  ▼
    ┌─────────────┐              ┌─────────────────┐
    │ PySpark ETL │              │   Airflow DAG   │
    │   (Silver)  │              │  Orchestration  │
    └─────────────┘              └─────────────────┘
         │
         ▼
    ┌─────────────┐
    │ PySpark     │
    │ (Gold Layer)│
    └─────────────┘
         │
         ├─────────────┬───────────────┐
         ▼             ▼               ▼
    Cassandra     Hive Tables    HDFS Parquet
         │
         ▼
    ┌──────────────────────────────────┐
    │   FastAPI Backend + Gradio UI    │
    │   (Analytics Dashboard)          │
    └──────────────────────────────────┘
```

---

# Technologies Implemented

| Component | Purpose | Version |
|-----------|---------|---------|
| **HDFS** | Distributed storage (Bronze/Silver/Gold layers) | Hadoop 3.x |
| **Apache Spark** | Multi-stage ETL processing | 3.x |
| **Apache Kafka** | Streaming data ingestion | 3.x |
| **Apache Cassandra** | NoSQL analytics data store | 4.x |
| **Apache Airflow** | Workflow orchestration & monitoring | 2.x |
| **Apache Hive** | SQL-based querying | 3.x |
| **FastAPI** | REST API backend | Latest |
| **Gradio** | Interactive analytics dashboard | Latest |
| **Prometheus** | Metrics collection | Latest |
| **Grafana** | Metrics visualization | Latest |
| **Docker** | Container orchestration | Latest |

---

# Project Structure

```
hadoop-logistic-lab/
├── airflow/                          # Workflow orchestration
│   ├── dags/
│   │   └── logistics_pipeline.py    # Main DAG with health checks
│   ├── config/
│   ├── plugins/
│   └── requirements.txt
│
├── processing/                       # Data transformations
│   └── spark/
│       ├── silver/                  # Data cleansing & standardization
│       │   ├── silver_transform_shipment.py
│       │   └── silver_transform_tracking.py
│       └── gold/                    # Business analytics
│           ├── gold_delivery_performance.py
│           ├── gold_route_optimization.py
│           ├── gold_shipment_snapshot.py
│           └── load_to_cassandra.py
│
├── ingestion/                       # Data intake pipelines
│   ├── kafka/                       # Kafka topic management
│   │   ├── create_topics.sh
│   │   ├── send_demo_data.sh
│   │   └── verify_kafka.sh
│   └── data-source/                 # Batch data ingestion
│       ├── load_to_hdfs.py
│       ├── stream_csv.py
│       └── requirements.txt
│
├── dashboard-app/                   # Analytics UI
│   ├── app.py                      # Gradio dashboard
│   ├── backend.py                  # FastAPI backend
│   └── requirements.txt
│
├── infrastructure/                  # Configuration & deployment
│   ├── docker/
│   │   ├── docker-compose.*.yml    # Service definitions
│   │   └── Dockerfiles/
│   ├── hadoop/                     # Hadoop configs (core-site.xml, etc.)
│   ├── hive/                       # Hive metastore configs
│   ├── kafka/                      # Kafka broker configs
│   ├── monitoring/                 # Prometheus & Grafana configs
│   └── pig/
│
├── dataset/                         # Sample data
│   ├── shipment_master.csv
│   └── tracking_events.csv
│
└── cassandra/                       # Cassandra keyspace definitions
    └── ingestion/data/
```

---

# Core Modules

## 1. Data Ingestion (Bronze Layer)

**Technologies:** HDFS, Kafka

- Raw shipment and tracking data loaded into HDFS Bronze layer
- Kafka topics stream real-time tracking events
- Data stored as JSON and CSV formats

**Key Files:**
- [data-source/load_to_hdfs.py](data-source/load_to_hdfs.py)
- [ingestion/kafka/create_topics.sh](ingestion/kafka/create_topics.sh)

---

## 2. Data Transformation - Silver Layer

**Technologies:** Apache Spark, HDFS Parquet

- Data cleansing and standardization
- Type casting and schema normalization
- Deduplication and null handling
- Format conversion to Parquet for optimized querying

**Implementations:**
- [processing/spark/silver/silver_transform_shipment.py](processing/spark/silver/silver_transform_shipment.py) — Cleans shipment metadata
- [processing/spark/silver/silver_transform_tracking.py](processing/spark/silver/silver_transform_tracking.py) — Standardizes tracking events

---

## 3. Business Analytics - Gold Layer

**Technologies:** Apache Spark, HDFS, Apache Cassandra

Generates analytics-ready datasets for business intelligence:

- **Delivery Performance** — SLA metrics, on-time delivery rates, delay analysis
- **Route Optimization** — Route efficiency, cost metrics, performance benchmarks
- **Shipment Snapshot** — Current shipment states, KPI aggregations

**Implementations:**
- [processing/spark/gold/gold_delivery_performance.py](processing/spark/gold/gold_delivery_performance.py)
- [processing/spark/gold/gold_route_optimization.py](processing/spark/gold/gold_route_optimization.py)
- [processing/spark/gold/gold_shipment_snapshot.py](processing/spark/gold/gold_shipment_snapshot.py)
- [processing/spark/gold/load_to_cassandra.py](processing/spark/gold/load_to_cassandra.py)

---

## 4. Workflow Orchestration

**Technologies:** Apache Airflow

Orchestrates the entire pipeline with automated health checks:

- **Health Checks:** HDFS, Kafka, Spark, Cassandra, FastAPI availability verification
- **Task Dependencies:** Manages sequential and parallel task execution
- **Monitoring:** Tracks pipeline execution and failure handling
- **Scheduling:** Runs batch processing on configurable schedules

**Implementation:** [airflow/dags/logistics_pipeline.py](airflow/dags/logistics_pipeline.py)

---

## 5. Distributed Storage

**Technologies:** Apache Cassandra, HDFS

- **Cassandra:** Operational analytics queries, fast data retrieval
- **HDFS:** Cost-effective distributed storage for raw and processed data

---

## 6. Analytics & Visualization

**Technologies:** FastAPI, Gradio, Prometheus, Grafana

**FastAPI Backend:**
- REST endpoints for querying Cassandra gold tables
- Delivery performance metrics API
- Route optimization data endpoint
- Shipment snapshot queries

**Gradio Dashboard:**
- Interactive KPI cards
- Cross-filter slicers for dynamic analysis
- Real-time performance tracking
- Styled with Power BI-like design patterns

**Monitoring:**
- Prometheus metrics collection
- Grafana dashboards for infrastructure health
- Custom alerts for pipeline failures

**Implementation:** [dashboard-app/app.py](dashboard-app/app.py), [dashboard-app/backend.py](dashboard-app/backend.py)

---

# Quick Start

## Prerequisites

- Docker & Docker Compose
- Git
- Minimum 8GB RAM, 32GB disk space

## Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/abhirajadhikary06/hadoop-logistic-lab.git
   cd hadoop-logistic-lab
   ```

2. **Configure environment:**
   ```bash
   cd infrastructure/docker
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Start the infrastructure:**
   ```bash
   docker-compose -f docker-compose.hadoop.yml up -d
   docker-compose -f docker-compose.kafka.yml up -d
   docker-compose -f docker-compose.spark.yml up -d
   docker-compose -f docker-compose.cassandra.yml up -d
   docker-compose -f docker-compose.airflow.yml up -d
   docker-compose -f docker-compose.api.yml up -d
   docker-compose -f docker-compose.monitoring.yml up -d
   ```

4. **Load sample data:**
   ```bash
   cd ingestion/kafka
   bash create_topics.sh
   bash send_demo_data.sh
   ```

5. **Access dashboards:**
   - Airflow: http://localhost:8080
   - Gradio Dashboard: http://localhost:7860
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3000
   - Spark Master: http://localhost:8081
   - HDFS NameNode: http://localhost:9870

---

# Data Flow Example

1. **Ingestion:** Shipment CSV loaded to HDFS Bronze layer via [data-source/load_to_hdfs.py](data-source/load_to_hdfs.py)
2. **Streaming:** Tracking events published to Kafka topic
3. **Orchestration:** Airflow DAG triggered, runs health checks
4. **Silver Transform:** Spark cleanses and deduplicates data, stores as Parquet
5. **Gold Transform:** Spark calculates delivery performance, route metrics, snapshots
6. **Storage:** Gold datasets written to Cassandra tables
7. **Analytics:** FastAPI backend queries Cassandra
8. **Visualization:** Gradio dashboard displays interactive reports

---

# Key Features

✅ **End-to-End Pipeline** — Complete data journey from ingestion to analytics

✅ **Distributed Processing** — Scalable Apache Spark transformations

✅ **NoSQL Analytics** — High-performance Cassandra queries

✅ **Automated Workflows** — Airflow orchestration with health checks

✅ **Real-Time Streaming** — Kafka-based event processing

✅ **Interactive Dashboard** — Power BI-style Gradio analytics UI

✅ **Infrastructure as Code** — Docker Compose for reproducible deployment

✅ **Production Monitoring** — Prometheus + Grafana observability

---

# Use Cases

- **Delivery SLA Monitoring** — Real-time tracking of on-time delivery rates
- **Route Optimization** — Identify inefficient routes and cost reduction opportunities
- **Performance Analytics** — Compare carrier performance and shipment metrics
- **Anomaly Detection** — Flag delayed or stuck shipments
- **Business Intelligence** — KPI dashboards for logistics operations

---

# Development

### Running Tests
```bash
# Execute Spark jobs locally (dev mode)
spark-submit processing/spark/silver/silver_transform_shipment.py
```

### Pipeline Logs
```bash
# View Airflow logs
docker logs <airflow-webserver-container>

# View Spark driver logs
docker logs <spark-master-container>