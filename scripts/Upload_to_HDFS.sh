#!/bin/bash

echo "Menjalankan upload ke HDFS..."

docker exec namenode hdfs dfs -mkdir -p /data/bronze
docker exec namenode hdfs dfs -put -f /data/occurrence.txt /data/bronze/
docker exec namenode hdfs dfs -put -f /data/verbatim.txt /data/bronze/

echo "✅ Upload selesai ke /data/bronze di HDFS"