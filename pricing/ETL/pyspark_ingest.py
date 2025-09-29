# etl/pyspark_ingest.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import to_date, col, lit, monotonically_increasing_id, row_number
from pyspark.sql.window import Window
import sys
from datetime import datetime


def main(input_dir):
    # PostgreSQL configuration from your Django settings
    DB_CONFIG = {
        'url': 'jdbc:postgresql://localhost:5432/mydatabase',
        'properties': {
            "user": "myuser",
            "password": "mypassword", 
            "driver": "org.postgresql.Driver"
        }
    }

    spark = SparkSession.builder \
        .appName("HotelPricingIngest") \
        .config("spark.jars", "./pricing/ETL/postgresql-42.6.0.jar") \
        .getOrCreate()

    # PRODUCTS - Direct to PostgreSQL with Django table name and auto-increment ID
    products_df = spark.read.csv(f"{input_dir}/products.csv", header=True, inferSchema=True)
    products_df = products_df.withColumnRenamed('Id','product_id') \
                             .withColumnRenamed('Room Name','room_name') \
                             .withColumnRenamed('Arrival Date','arrival_date') \
                             .withColumnRenamed('No. of Beds','beds') \
                             .withColumnRenamed('Room Type','room_type') \
                             .withColumnRenamed('Grade','grade') \
                             .withColumnRenamed('Private Pool','private_pool') \
                             .withColumn('arrival_date', to_date(col('arrival_date'), 'yyyy-MM-dd'))

    # Add auto-incrementing id column for Django compatibility
    window = Window.orderBy(col('product_id'))
    products_df = products_df.withColumn('id', row_number().over(window))
    
    # Reorder columns to put id first (Django convention)
    products_df = products_df.select('id', 'product_id', 'room_name', 'arrival_date', 
                                   'beds', 'room_type', 'grade', 'private_pool')

    # Write to Django table name
    products_df.write.mode('overwrite').jdbc(
        DB_CONFIG['url'], 
        "pricing_product",  # Django table naming convention: app_modelname
        properties=DB_CONFIG['properties']
    )

    # BOOKINGS - Append mode for incremental data with auto-increment ID
    bookings_df = spark.read.csv(f"{input_dir}/bookings.csv", header=True, inferSchema=True)
    bookings_df = bookings_df.withColumnRenamed('Id','booking_id') \
                             .withColumnRenamed('Product Id','product_id') \
                             .withColumnRenamed('Creation Date','creation_date') \
                             .withColumnRenamed('Confirmation Status','confirmation_status') \
                             .withColumnRenamed('Arrival Date','arrival_date') \
                             .withColumn('arrival_date', to_date(col('arrival_date'), 'yyyy-MM-dd'))
    
    # Add auto-incrementing id column
    window = Window.orderBy(col('booking_id'))
    bookings_df = bookings_df.withColumn('id', row_number().over(window))
    
    # Reorder columns
    bookings_df = bookings_df.select('id', 'booking_id', 'product_id', 'creation_date', 
                                   'confirmation_status', 'arrival_date')
    
    bookings_df.write.mode('append').jdbc(
        DB_CONFIG['url'], 
        "pricing_booking",  # Django table name
        properties=DB_CONFIG['properties']
    )

    # BUILDINGS with auto-increment ID
    buildings_df = spark.read.csv(f"{input_dir}/buildings.csv", header=True, inferSchema=True)
    buildings_df = buildings_df.withColumnRenamed('Building','name')  # Match Django model field
    
    # Add auto-incrementing id column
    window = Window.orderBy(col('name'))
    buildings_df = buildings_df.withColumn('id', row_number().over(window))
    
    # Select only the fields that exist in Django model (Building only has id and name)
    buildings_df = buildings_df.select('id', 'name').distinct()
    
    buildings_df.write.mode('overwrite').jdbc(
        DB_CONFIG['url'], 
        "pricing_building",  # Django table name
        properties=DB_CONFIG['properties']
    )

    # PRICES with auto-increment ID
    prices_df = spark.read.csv(f"{input_dir}/prices.csv", header=True, inferSchema=True)
    prices_df = prices_df.withColumnRenamed('Product Id','product_id') \
                         .withColumnRenamed('Price','value') \
                         .withColumnRenamed('Currency','currency') \
                         .withColumn('updated_at', lit(datetime.now()))
    
    # Add auto-incrementing id column
    window = Window.orderBy(col('product_id'), col('currency'))
    prices_df = prices_df.withColumn('id', row_number().over(window))
    
    # Reorder columns
    prices_df = prices_df.select('id', 'product_id', 'currency', 'value', 'updated_at')
    
    prices_df.write.mode('overwrite').jdbc(
        DB_CONFIG['url'], 
        "pricing_price",  # Django table name
        properties=DB_CONFIG['properties']
    )

    spark.stop()
    print("Data ingestion completed with Django-compatible schema!")

if __name__ == '__main__':
    input_dir = "./pricing/ETL/Data/" # s3://bucket/input or /local/path
    main(input_dir)
    






