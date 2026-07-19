from pyspark.sql import SparkSession
from pyspark.sql.window import Window
from pyspark.sql.functions import col, row_number

# Initialize Spark
spark = SparkSession.builder \
    .appName("Gold Shipment Snapshot") \
    .master("spark://spark-master:7077") \
    .config("spark.sql.shuffle.partitions", "4") \
    .getOrCreate()

print("Processing Gold: Latest Shipment Snapshot")

# Read Silver Parquet layers
shipments_df = spark.read.parquet("hdfs://namenode:9000/silver/logistics/shipment_events.parquet")
tracking_df = spark.read.parquet("hdfs://namenode:9000/silver/logistics/tracking_events.parquet")

# Create a window to isolate the latest tracking log per shipment
window_spec = Window.partitionBy("shipment_id").orderBy(col("event_timestamp").desc())

# Deduplicate tracking data to only retain the newest state
latest_tracking = tracking_df \
    .withColumn("row_num", row_number().over(window_spec)) \
    .filter(col("row_num") == 1) \
    .drop("row_num")

# Enrich the latest update with target route details
snapshot_df = shipments_df.join(latest_tracking, on="shipment_id", how="left") \
    .select(
        col("shipment_id"),
        col("origin"),
        col("destination"),
        col("event_type").alias("current_status"),
        col("location").alias("current_location"),
        col("event_timestamp").alias("last_updated_at")
    )

# Save to Gold layer
snapshot_df.write.mode("overwrite").parquet("hdfs://namenode:9000/gold/logistics/shipment_snapshot")
print("Gold Shipment Snapshot completed successfully.")
spark.stop()