# etl_verbatim.py

from pyspark.sql import SparkSession

# Inisialisasi Spark Session
spark = SparkSession.builder \
    .appName("ETL Verbatim Bronze to Silver") \
    .config("spark.hadoop.fs.defaultFS", "hdfs://namenode:9000") \
    .config("spark.hadoop.hadoop.security.authentication", "simple") \
    .getOrCreate()

# Path input/output HDFS
input_path = "hdfs://namenode:9000/data/bronze/verbatim.txt"
output_path = "hdfs://namenode:9000/data/silver/verbatim.parquet"

# Baca file TSV
df = spark.read.option("header", True).option("sep", "\t").csv(input_path)

# Simpan ke Parquet
df.write.option("compression", "uncompressed").mode("overwrite").parquet(output_path)

print("ETL selesai: verbatim.parquet disimpan di Silver Layer")
spark.stop()