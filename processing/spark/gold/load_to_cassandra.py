from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("Load to Cassandra") \
    .master("spark://spark-master:7077") \
    .config("spark.jars.packages", "com.datastax.spark:spark-cassandra-connector_2.12:3.5.0") \
    .config("spark.cassandra.connection.host", "cassandra") \
    .config("spark.executor.memory", "512m") \
    .config("spark.driver.memory", "512m") \
    .config("spark.memory.fraction", "0.6") \
    .config("spark.cassandra.output.concurrent.writes", "5") \
    .config("spark.cassandra.output.batch.size.rows", "100") \
    .getOrCreate()

print("Loading Gold layer data to Cassandra")

def write_to_cassandra(df, table_name):
    print(f"Writing data to Cassandra table: {table_name}")
    df.write \
        .format("org.apache.spark.sql.cassandra") \
        .options(table=table_name, keyspace="gold_logistics") \
        .mode("append") \
        .save()
    print(f"Successfully loaded data to Cassandra table: {table_name}")

# 1. Delivery Performance
perf_df = spark.read.parquet("hdfs://namenode:9000/gold/logistics/delivery_performance")
write_to_cassandra(perf_df.repartition(2), "delivery_performance")

# 2. Shipment Snapshot
snapshot_df = spark.read.parquet("hdfs://namenode:9000/gold/logistics/shipment_snapshot")
write_to_cassandra(snapshot_df.repartition(2), "shipment_snapshot")

# 3. Route Optimization
routeopt_df = spark.read.parquet("hdfs://namenode:9000/gold/logistics/route_optimization")
write_to_cassandra(routeopt_df.repartition(2), "route_optimization")

spark.stop()