from datetime import datetime

import requests
from cassandra.cluster import Cluster
from kafka import KafkaAdminClient

from airflow import DAG
from airflow.exceptions import AirflowException
from airflow.operators.python import PythonOperator


# ---------------------------------------------------------
# Health Checks
# ---------------------------------------------------------

def check_hdfs():
    try:
        r = requests.get("http://namenode:9870", timeout=5)

        if r.status_code != 200:
            raise AirflowException("NameNode is unavailable.")

        print("HDFS OK")

    except Exception as e:
        raise AirflowException(str(e))


def check_kafka():
    try:
        # Create a socket object and try connecting to the host/port
        with socket.create_connection(("kafka", 9093), timeout=5):
            print("Successfully connected to Kafka port.")
    except Exception as e:
        raise AirflowException(f"Kafka check failed: {e}")


def check_spark():

    try:

        r = requests.get(
            "http://spark-master:8080",
            timeout=5
        )

        if r.status_code != 200:
            raise AirflowException("Spark Master unavailable")

        print("Spark OK")

    except Exception as e:
        raise AirflowException(str(e))


def check_cassandra():

    try:

        cluster = Cluster(["cassandra"])

        session = cluster.connect()

        session.execute(
            "SELECT release_version FROM system.local"
        )

        cluster.shutdown()

        print("Cassandra OK")

    except Exception as e:
        raise AirflowException(str(e))


def check_fastapi():

    try:

        r = requests.get(
            "http://api-service:8000/docs",
            timeout=5
        )

        if r.status_code != 200:
            raise AirflowException("FastAPI unavailable")

        print("FastAPI OK")

    except Exception as e:
        raise AirflowException(str(e))


# ---------------------------------------------------------
# DAG
# ---------------------------------------------------------

default_args = {
    "owner": "abhiraj",
}

with DAG(
    dag_id="logistics_pipeline",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    default_args=default_args,
    tags=["logistics"],
) as dag:

    hdfs = PythonOperator(
        task_id="check_hdfs",
        python_callable=check_hdfs,
    )

    kafka = PythonOperator(
        task_id="check_kafka",
        python_callable=check_kafka,
    )

    spark = PythonOperator(
        task_id="check_spark",
        python_callable=check_spark,
    )

    cassandra = PythonOperator(
        task_id="check_cassandra",
        python_callable=check_cassandra,
    )

    fastapi = PythonOperator(
        task_id="check_fastapi",
        python_callable=check_fastapi,
    )

    hdfs >> kafka >> spark >> cassandra >> fastapi