# Databricks notebook source
# Strings preserve SAP identifiers and source precision; typed conversion belongs in Silver.
import hashlib
import json
import re
from pyspark.sql import functions as F

dbutils.widgets.text('landing_path','')
dbutils.widgets.text('bronze_path','')
source=dbutils.widgets.get('landing_path').rstrip('/')
target=dbutils.widgets.get('bronze_path').rstrip('/')
if not source or not target or source==target:raise ValueError('Provide distinct source and target')
raw=dbutils.fs.head(source+'/manifest.json',1048576)
if dbutils.fs.head(source+'/_SUCCESS').strip()!=hashlib.sha256(raw.encode()).hexdigest():
    raise ValueError('Incomplete batch')
manifest=json.loads(raw)
batch_date=manifest['batch_date']
if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',batch_date):raise ValueError('Invalid batch date')
source_id=manifest['source']
if not re.fullmatch('[A-Z0-9_]+',source_id):raise ValueError('Invalid source')
# Validate every file before writing any table. Individual Delta table commits are atomic;
# the final receipt marks completion across all tables and a retry replaces each partition.
frames=[]
for filename,meta in manifest['files'].items():
    if not re.fullmatch('[a-z_]+\\.csv',filename):raise ValueError('Unsafe filename')
    path=source+'/'+filename
    digest=spark.read.format('binaryFile').load(path).select(F.sha2('content',256).alias('sha')).first()['sha']
    if digest!=meta['sha256']:raise ValueError('Checksum mismatch: '+filename)
    frame=spark.read.option('header',True).option('inferSchema',False).option('mode','FAILFAST').csv(path)
    if frame.count()!=meta['rows']:raise ValueError('Row count mismatch: '+filename)
    frames.append((filename[:-4],frame))
for table,frame in frames:
    (frame.withColumn('_source',F.lit(source_id)).withColumn('_batch_date',F.lit(batch_date))
     .write.format('delta').mode('overwrite').partitionBy('_source','_batch_date')
     .option('replaceWhere',f"_source = '{source_id}' AND _batch_date = '{batch_date}'")
     .save(target+'/'+table))
dbutils.fs.put(target+f'/_receipts/{source_id}/{batch_date}.json',raw,True)
