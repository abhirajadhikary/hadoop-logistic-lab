from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date, to_timestamp

spark = SparkSession.builder \
    .appName("Silver Transform Shipment") \
    .master("spark://spark-master:7077") \
    .config("spark.sql.shuffle.partitions", "4") \
    .getOrCreate()

print("Processing shipment events from Bronze to Silver layer")

raw_df = spark.read.json("hdfs://namenode:9000/bronze/logistics/shipment_events.json")

cleaned_df = raw_df \
    .withColumn("weight_kg", col("weight_kg").cast("double")) \
    .withColumn("declared_value", col("declared_value").cast("double")) \
    .withColumn("shipping_date", to_date(col("shipping_date"), "yyyy-MM-dd")) \
    .filter(col("shipment_id").isNotNull()) \
    .dropDuplicates(["shipment_id"])

cleaned_df.write \
    .mode("overwrite") \
    .parquet("hdfs://namenode:9000/silver/logistics/shipment_events.parquet")

print("Silver layer transformation completed successfully.")
spark.stop()