from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, current_timestamp, to_timestamp

spark = SparkSession.builder \
    .appName("Silver Transform Tracking") \
    .master("spark://spark-master:7077") \
    .config("spark.sql.shuffle.partitions", "4") \
    .getOrCreate()

print("Processing tracking events from Bronze to Silver layer")

raw_df = spark.read.json("hdfs://namenode:9000/bronze/logistics/tracking_events.json")

cleaned_df = raw_df \
    .withColumn("event_timestamp", to_timestamp(col("event_timestamp"))) \
    .filter(col("event_timestamp").isNotNull()) \
    .dropDuplicates(["event_id"]) \

cleaned_df.write \
    .mode("overwrite") \
    .parquet("hdfs://namenode:9000/silver/logistics/tracking_events.parquet")

print("Silver layer transformation completed successfully.")
spark.stop()