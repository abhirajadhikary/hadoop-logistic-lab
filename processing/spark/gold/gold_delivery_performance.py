from pyspark.sql import SparkSession
from pyspark.sql.functions import col, abs, first

# Initialize Spark
spark = SparkSession.builder \
    .appName("Gold Delivery Performance") \
    .master("spark://spark-master:7077") \
    .config("spark.sql.shuffle.partitions", "4") \
    .getOrCreate()

print("Processing Gold: Delivery Performance & SLA Metrics")

# Read Silver Parquet layers
shipments_df = spark.read.parquet("hdfs://namenode:9000/silver/logistics/shipment_events.parquet")
tracking_df = spark.read.parquet("hdfs://namenode:9000/silver/logistics/tracking_events.parquet")

# Pivot tracking events to get Picked Up and Delivered timestamps per shipment
# Pivot tracking events to get Picked Up and Delivered timestamps per shipment
timestamps_df = tracking_df \
    .filter(col("event_type").isin("Picked Up", "Delivered")) \
    .groupBy("shipment_id") \
    .pivot("event_type", ["Picked Up", "Delivered"]) \
    .agg(first(col("event_timestamp"))) \
    .withColumnRenamed("Picked Up", "picked_up_time") \
    .withColumnRenamed("Delivered", "delivered_time")

# Join with shipments metadata and compute duration (in days)
performance_df = shipments_df.join(timestamps_df, on="shipment_id", how="inner") \
    .withColumn("delivery_duration_days", 
                (col("delivered_time").cast("long") - col("picked_up_time").cast("long")) / 86400) \
    .withColumn("is_delayed", col("delivery_duration_days") > 5)  # Example SLA rule: 5 days threshold

# Save to Gold layer
performance_df.write.mode("overwrite").parquet("hdfs://namenode:9000/gold/logistics/delivery_performance")
print("Gold Delivery Performance completed successfully.")
spark.stop()