# etl/pyspark_clustering.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import (month, year, col, avg, count, min, max, round, lit, 
                                  current_timestamp, when, row_number)
from pyspark.sql.window import Window
import sys

def cluster_and_get_bookings():  
    # PostgreSQL configuration
    DB_CONFIG = {
        'url': 'jdbc:postgresql://localhost:5432/mydatabase',
        'properties': {
            "user": "myuser",
            "password": "mypassword", 
            "driver": "org.postgresql.Driver"
        }
    }

    spark = SparkSession.builder \
        .appName("ProductClustering") \
        .config("spark.jars", "./pricing/ETL/postgresql-42.6.0.jar") \
        .getOrCreate()

    # Read from Django table names (created by updated ingest script)
    products = spark.read.jdbc(DB_CONFIG['url'], "pricing_product", properties=DB_CONFIG['properties'])
    bookings = spark.read.jdbc(DB_CONFIG['url'], "pricing_booking", properties=DB_CONFIG['properties'])
    prices = spark.read.jdbc(DB_CONFIG['url'], "pricing_price", properties=DB_CONFIG['properties'])

    # Create aliases for all DataFrames to avoid ambiguity
    products_df = products.alias('p')
    bookings_df = bookings.alias('b')
    prices_df = prices.alias('pr')

    # Derive cluster keys
    products_with_cluster = products_df.withColumn('arrival_month', month(col('p.arrival_date'))) \
                                      .withColumn('arrival_year', year(col('p.arrival_date')))

    # Select cluster columns
    products_clustered = products_with_cluster.select(
        col('p.product_id'),
        'arrival_year', 'arrival_month', 
        col('p.room_type'), col('p.beds'), col('p.grade'), col('p.private_pool')
    )

    # Join with bookings - match on product_id from the CSV data, not Django's auto id
    joined_with_bookings = products_clustered.join(
        bookings_df, 
        col('p.product_id') == col('b.product_id'), 
        how='left'
    )

    # Join with prices - match on product_id from the CSV data
    joined_with_prices = joined_with_bookings.join(
        prices_df,
        col('p.product_id') == col('pr.product_id'),
        how='left'
    )

    # Calculate cluster statistics
    cluster_stats = joined_with_prices.groupBy(
        'arrival_year', 'arrival_month', 'room_type', 'beds', 'grade', 'private_pool'
    ).agg(
        count('p.product_id').alias('product_count'),
        count('b.booking_id').alias('booking_count'),
        avg('pr.value').alias('avg_price'),
        min('pr.value').alias('min_price'),
        max('pr.value').alias('max_price'),
        round(avg('pr.value'), 2).alias('avg_price_rounded')
    ).withColumn(
        'occupancy_rate', 
        round((col('booking_count') / col('product_count')) * 100, 2)
    )

    # Create price recommendations
    price_recommendations = products_clustered.join(
        cluster_stats,
        ['arrival_year', 'arrival_month', 'room_type', 'beds', 'grade', 'private_pool'],
        how='inner'
    ).select(
        col('p.product_id'),
        col('avg_price_rounded').alias('recommended_price'),
        lit('USD').alias('currency'),
        current_timestamp().alias('created_at'),
        when(col('occupancy_rate') > 80, 'High occupancy cluster - premium pricing')
        .when(col('occupancy_rate') < 30, 'Low occupancy cluster - competitive pricing')
        .otherwise('Average occupancy cluster - market pricing').alias('reason')
    ).distinct()

    # Add auto-incrementing id column for Django compatibility
    window = Window.orderBy(col('product_id'))
    price_recommendations = price_recommendations.withColumn('id', row_number().over(window))
    
    # Reorder columns to put id first (Django convention)
    price_recommendations = price_recommendations.select(
        'id', 'product_id', 'recommended_price', 'currency', 'created_at', 'reason'
    )

    # Show results
    print("Price recommendations sample:")
    price_recommendations.show(10)

    # Write to Django table name with proper schema
    price_recommendations.write.mode('overwrite').jdbc(
        DB_CONFIG['url'], 
        "pricing_pricerecommendation",  # Django table naming convention
        properties=DB_CONFIG['properties']
    )
    
    print("Price recommendations written to: pricing_pricerecommendation")
    spark.stop()


    
def create_product_building_relationships():
    """
    Create proper foreign key relationships if you have building-product mapping data
    """
    DB_CONFIG = {
        'url': 'jdbc:postgresql://localhost:5432/mydatabase',
        'properties': {
            "user": "myuser",
            "password": "mypassword", 
            "driver": "org.postgresql.Driver"
        }
    }

    spark = SparkSession.builder \
        .appName("CreateFKRelationships") \
        .config("spark.jars", "./pricing/ETL/postgresql-42.6.0.jar") \
        .getOrCreate()

    # If you have building-product relationships in your CSV files
    # Read the building-product mapping
    try:
        building_product_df = spark.read.csv("./pricing/ETL/Data/buildings.csv", header=True, inferSchema=True)
        building_product_df = building_product_df.withColumnRenamed('Building','building_name') \
                                               .withColumnRenamed('Product Id','product_id')

        # Get building IDs from the buildings table
        buildings_df = spark.read.jdbc(DB_CONFIG['url'], "pricing_building", properties=DB_CONFIG['properties'])
        
        # Join to get building_id for each product
        product_building_mapping = building_product_df.join(
            buildings_df.select('id', 'name'), 
            building_product_df.building_name == buildings_df.name
        ).select(
            col('product_id'), 
            col('id').alias('building_id')
        )

        # Update products table with building_id if you want to add this relationship
        # This would require modifying your Django model to include building as ForeignKey
        print("Building-Product relationships identified:")
        product_building_mapping.show(10)
        
        # Uncomment if you want to store this mapping in a separate table
        # window = Window.orderBy(col('product_id'))
        # product_building_mapping = product_building_mapping.withColumn('id', row_number().over(window))
        # product_building_mapping.write.mode('overwrite').jdbc(
        #     DB_CONFIG['url'], 
        #     "pricing_productbuilding",  
        #     properties=DB_CONFIG['properties']
        # )

    except Exception as e:
        print(f"No building-product relationship file found or error: {e}")

    spark.stop()


if __name__ == '__main__':
    create_product_building_relationships()
    cluster_and_get_bookings()

