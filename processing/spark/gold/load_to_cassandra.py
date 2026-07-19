from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("Load to Cassandra") \
    .master("spark://spark-master:7077") \
    .config("spark.jars.packages", "com.datastax.spark:spark-cassandra-connector_2.12:3.5.0") \
    .config("spark.cassandra.connection.host", "cassandra") \
    .getOrCreate()

print("Loading Gold layer data to Cassandra")

# 1. Delivery Performance
perf_df = spark.read.parquet("hdfs://namenode:9000/gold/logistics/delivery_performance")
perf_df.write \
    .format("org.apache.spark.sql.cassandra") \
    .options(table="delivery_performance", keyspace="gold_logistics") \
    .mode("append") \
    .save()
print("Successfully loaded delivery performance data to Cassandra")

# 2. Shipment Snapshot
snapshot_df = spark.read.parquet("hdfs://namenode:9000/gold/logistics/shipment_snapshot")
snapshot_df.write \
    .format("org.apache.spark.sql.cassandra") \
    .options(table="shipment_snapshot", keyspace="gold_logistics") \
    .mode("append") \
    .save()
print("Successfully loaded shipment snapshot data to Cassandra")

# 3. Route Optimization
routeopt_df = spark.read.parquet("hdfs://namenode:9000/gold/logistics/route_optimization")
routeopt_df.write \
    .format("org.apache.spark.sql.cassandra") \
    .options(table="route_optimization", keyspace="gold_logistics") \
    .mode("append") \
    .save()
print("Successfully loaded route optimization data to Cassandra")

spark.stop()