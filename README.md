HEAD
[![Gitter chat](https://badges.gitter.im/gitterHQ/gitter.png)](https://gitter.im/big-data-europe/Lobby)

# Changes

Version 2.0.0 introduces uses wait_for_it script for the cluster startup

# Hadoop Docker

## Supported Hadoop Versions
See repository branches for supported hadoop versions

## Quick Start

To deploy an example HDFS cluster, run:
```
  docker-compose up
```

Run example wordcount job:
```
  make wordcount
```

Or deploy in swarm:
```
docker stack deploy -c docker-compose-v3.yml hadoop
```

`docker-compose` creates a docker network that can be found by running `docker network list`, e.g. `dockerhadoop_default`.

Run `docker network inspect` on the network (e.g. `dockerhadoop_default`) to find the IP the hadoop interfaces are published on. Access these interfaces with the following URLs:

* Namenode: http://<dockerhadoop_IP_address>:9870/dfshealth.html#tab-overview
* History server: http://<dockerhadoop_IP_address>:8188/applicationhistory
* Datanode: http://<dockerhadoop_IP_address>:9864/
* Nodemanager: http://<dockerhadoop_IP_address>:8042/node
* Resource manager: http://<dockerhadoop_IP_address>:8088/

## Configure Environment Variables

The configuration parameters can be specified in the hadoop.env file or as environmental variables for specific services (e.g. namenode, datanode etc.):
```
  CORE_CONF_fs_defaultFS=hdfs://namenode:8020
```

CORE_CONF corresponds to core-site.xml. fs_defaultFS=hdfs://namenode:8020 will be transformed into:
```
  <property><name>fs.defaultFS</name><value>hdfs://namenode:8020</value></property>
```
To define dash inside a configuration parameter, use triple underscore, such as YARN_CONF_yarn_log___aggregation___enable=true (yarn-site.xml):
```
  <property><name>yarn.log-aggregation-enable</name><value>true</value></property>
```

The available configurations are:
* /etc/hadoop/core-site.xml CORE_CONF
* /etc/hadoop/hdfs-site.xml HDFS_CONF
* /etc/hadoop/yarn-site.xml YARN_CONF
* /etc/hadoop/httpfs-site.xml HTTPFS_CONF
* /etc/hadoop/kms-site.xml KMS_CONF
* /etc/hadoop/mapred-site.xml  MAPRED_CONF

If you need to extend some other configuration file, refer to base/entrypoint.sh bash script.

# Analisis-Persebaran-Fauna-di-Sumatera
7afbe0807aa4b72a4d35c7525479ab591c1c20a6

# Klasifikasi Spesies Kelelawar Berdasarkan Persebaran Dominasi

## Deskripsi Singkat

Proyek ini bertujuan untuk:
- Membersihkan data kemunculan spesies dari file `occurrence.parquet`
- Mengidentifikasi spesies kelelawar dominan di tiap kecamatan (`level3Name`)
- Menghitung rata-rata koordinat (latitude dan longitude) tiap kecamatan
- Mengklasifikasikan kecamatan berdasarkan dominasi spasial spesies menggunakan algoritma KMeans
- Menyimpan hasil klasifikasi ke dalam file CSV agar dapat divisualisasikan di QGIS

---

## Tahap 1: Pembersihan Data Occurrence
```scala
val selectedCols = Seq(
  "eventDate", "countryCode", "stateProvince", "municipality", "locality",
  "decimalLatitude", "decimalLongitude", "datasetKey", "lastInterpreted",
  "elevation", "issue", "mediaType", "taxonKey", "acceptedTaxonKey", "familyKey",
  "genusKey", "speciesKey", "species", "lastParsed",
  "level0Name", "level1Gid", "level1Name", "level2Gid", "level2Name",
  "level3Gid", "level3Name", "iucnRedListCategory"
)

val df = spark.read.parquet("/data/silver/occurrence.parquet")

val cleaned = df
  .select(selectedCols.map(col): _*)
  .withColumn("eventDate", to_date(col("eventDate"), "yyyy-MM-dd"))
  .filter(
    col("decimalLatitude").isNotNull &&
    col("decimalLongitude").isNotNull &&
    col("eventDate").isNotNull
  )
```

---

## Tahap 2: Agregasi Dominasi Spesies per Kecamatan
```scala
val speciesByKecamatan = cleaned
  .groupBy("level3Name", "species")
  .agg(count("*").as("count"))

val windowSpec = Window.partitionBy("level3Name").orderBy(desc("count"))

val dominantSpeciesPerKecamatan = speciesByKecamatan
  .withColumn("rank", row_number().over(windowSpec))
  .filter(col("rank") === 1)
  .drop("rank")
```

---

## Tahap 3: Koordinat Rata-rata per Kecamatan
```scala
val coords = cleaned
  .groupBy("level3Name")
  .agg(
    avg(col("decimalLatitude").cast("double")).alias("lat"),
    avg(col("decimalLongitude").cast("double")).alias("lon")
  )
```

---

## Tahap 4: Gabungkan Dominasi Spesies + Koordinat
```scala
val dataset = dominantSpeciesPerKecamatan
  .join(coords, Seq("level3Name"))
  .filter(col("lat").isNotNull && col("lon").isNotNull)
```

---

## Tahap 5: KMeans Clustering
```scala
val assembler = new VectorAssembler()
  .setInputCols(Array("lat", "lon"))
  .setOutputCol("features")

val vectorized = assembler.transform(dataset).cache()

val kmeans = new KMeans()
  .setK(3)
  .setSeed(42)
  .setFeaturesCol("features")
  .setPredictionCol("cluster")

val model = kmeans.fit(vectorized)
val clustered = model.transform(vectorized)
```

---

## Tahap 6: Simpan Hasil Clustering ke CSV (untuk QGIS)
```scala
clustered
  .select("level3Name", "species", "count", "lat", "lon", "cluster")
  .coalesce(1)
  .write
  .option("header", "true")
  .mode("overwrite")
  .csv("/tmp/species_clusters")
```

---

## Tahap 7: Salin ke Host (Windows)
```bash
docker cp spark-master:/tmp/species_clusters/part-00000-...csv C:\Users\Lenovo\Documents\species_clusters.csv
```

> **Catatan:** Gunakan `docker exec -it spark-master ls /tmp/species_clusters` untuk melihat nama pasti file `.csv`.

---

## Visualisasi di QGIS
1. Buka QGIS dan tambahkan shapefile wilayah administratif (`shp`) untuk Sumatera.
2. Tambahkan layer `species_clusters.csv` sebagai point layer.
3. Gabungkan (join) shapefile dengan layer CSV berdasarkan kolom `level3Name`.
4. Gunakan symbologi kategorikal untuk menampilkan warna berdasarkan kolom `cluster`.
5. Ubah warna layer `.shp` di bagian Properties → Symbology → Fill color.

---

## Selesai ✅

Pipeline berhasil melakukan klasifikasi wilayah berdasarkan spesies kelelawar dominan dan dapat divisualisasikan dengan mudah di QGIS.

