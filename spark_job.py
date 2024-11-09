# from pyspark.sql import SparkSession
# from pyspark.sql.functions import from_json, col
# from pyspark.sql.types import StructType, StringType, FloatType
#
# # Initialize Spark session
# spark = SparkSession.builder \
#     .appName("KafkaStockDataIntegration") \
#     .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3") \
#     .getOrCreate()
#
# # Define the schema to match the stock data format
# schema = StructType() \
#     .add("timestamp", StringType()) \
#     .add("ticker", StringType()) \
#     .add("open", FloatType()) \
#     .add("high", FloatType()) \
#     .add("low", FloatType()) \
#     .add("close", FloatType()) \
#     .add("volume", FloatType())
#
# # Read data from Kafka topic
# kafka_df = spark.readStream \
#     .format("kafka") \
#     .option("kafka.bootstrap.servers", "localhost:9092") \
#     .option("subscribe", "stock_data") \
#     .load()
#
# # Convert the Kafka data to a structured DataFrame
# value_df = kafka_df.selectExpr("CAST(value AS STRING)")
# json_df = value_df.select(from_json(col("value"), schema).alias("data")).select("data.*")
#
# # Process and display the data in real-time
# query = json_df.writeStream \
#     .outputMode("append") \
#     .format("console") \
#     .start()
#
# query.awaitTermination()

from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, expr
from pyspark.sql.types import StructType, StringType, FloatType

# Initialize Spark session
spark = SparkSession.builder \
    .appName("RealTimeStockAnalysis") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3") \
    .getOrCreate()

# Define schema for stock data
schema = StructType() \
    .add("timestamp", StringType()) \
    .add("ticker", StringType()) \
    .add("open", FloatType()) \
    .add("high", FloatType()) \
    .add("low", FloatType()) \
    .add("close", FloatType()) \
    .add("volume", FloatType())

# Read data from Kafka topic
kafka_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "localhost:9092") \
    .option("subscribe", "stock_data") \
    .load()

# Convert the Kafka data to a structured DataFrame
value_df = kafka_df.selectExpr("CAST(value AS STRING)")
json_df = value_df.select(from_json(col("value"), schema).alias("data")).select("data.*")

# Transformation Example: Calculate the price difference
transformed_df = json_df.withColumn("price_diff", expr("close - open")) \
                        .withColumn("volume_indicator", expr("CASE WHEN volume > 100000 THEN 'High' ELSE 'Normal' END"))

# Write the transformed data to console in real-time
query = transformed_df.writeStream \
    .outputMode("append") \
    .format("console") \
    .start()

query.awaitTermination()