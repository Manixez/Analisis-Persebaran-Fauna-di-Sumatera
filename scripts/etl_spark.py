from pyspark.sql import SparkSession
from pyspark.sql.functions import col

# Buat Spark session langsung (tanpa otak-atik autentikasi)
spark = SparkSession.builder \
    .appName("ETL Occurrence Bronze to Silver") \
    .config("spark.hadoop.fs.defaultFS", "hdfs://namenode:9000") \
    .config("spark.hadoop.hadoop.security.authentication", "simple") \
    .getOrCreate()

# Path input/output di HDFS
input_path = "hdfs://namenode:9000/data/bronze/occurrence.txt"
output_path = "hdfs://namenode:9000/data/silver/occurrence.parquet"

# Baca file TSV dari HDFS
df = spark.read.option("header", True).option("sep", "\t").csv(input_path)

# Filter hanya baris dengan koordinat lengkap
df_clean = df.filter(
    (col("decimalLatitude").isNotNull()) &
    (col("decimalLongitude").isNotNull())
)

# Simpan hasil bersih ke format Parquet tanpa kompresi
df_clean.write.option("compression", "none").mode("overwrite").parquet(output_path)

print("ETL selesai: occurrence.parquet disimpan di Silver Layer")
spark.stop()
