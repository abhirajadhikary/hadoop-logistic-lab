from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, sum, avg

# Initialize Spark
spark = SparkSession.builder \
    .appName("Gold Route Optimization") \
    .master("spark://spark-master:7077") \
    .config("spark.sql.shuffle.partitions", "4") \
    .getOrCreate()

print("Processing Gold: Route Optimization Analytics")

# Read Silver Parquet layers
shipments_df = spark.read.parquet("hdfs://namenode:9000/silver/logistics/shipment_events.parquet")
tracking_df = spark.read.parquet("hdfs://namenode:9000/silver/logistics/tracking_events.parquet")

# Cast numerical fields to float/double for math operations
shipments_clean = shipments_df \
    .withColumn("weight_kg", col("weight_kg").cast("double")) \
    .withColumn("declared_value", col("declared_value").cast("double"))

# Join tracking locations with shipment origins/destinations
route_df = tracking_df.join(shipments_clean, on="shipment_id", how="inner")

# Aggregate route metrics
optimized_routes = route_df.groupBy("origin", "destination", "location") \
    .agg(
        count("shipment_id").alias("total_shipments"),
        sum("declared_value").alias("total_value_at_risk"),
        avg("weight_kg").alias("avg_weight_kg")
    )

# Save to Gold layer
optimized_routes.write.mode("overwrite").parquet("hdfs://namenode:9000/gold/logistics/route_optimization")
print("Gold Route Optimization completed successfully.")
spark.stop()