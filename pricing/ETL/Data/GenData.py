import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

def generate_products_data(n_records=500):
    """Generate Products CSV data"""
    
    room_types = ['Single', 'Double Room', 'Suite', 'Deluxe', 'Presidential']
    room_grades = [1, 2, 3, 4, 5, 6, 7]  # Star ratings
    
    # Generate base data
    products = []
    base_date = datetime(2024, 1, 1)
    
    for i in range(1, n_records + 1):
        # Generate arrival dates spread across the year
        arrival_date = base_date + timedelta(days=random.randint(0, 365))
        
        room_type = random.choice(room_types)
        
        # Number of beds based on room type logic
        if room_type == 'Single':
            beds = 1
        elif room_type == 'Double Room':
            beds = 2
        elif room_type == 'Suite':
            beds = random.choice([2, 3, 4])
        elif room_type == 'Deluxe':
            beds = random.choice([2, 3])
        else:  # Presidential
            beds = random.choice([3, 4, 5])
        
        grade = random.choice(room_grades)
        private_pool = random.choice([True, False])
        
        # Generate room names
        room_name = f"{room_type} {i:03d}"
        
        products.append({
            'Id': i,
            'Room Name': room_name,
            'Arrival Date': arrival_date.strftime('%Y-%m-%d'),
            'No. of Beds': beds,
            'Room Type': room_type,
            'Grade': grade,
            'Private Pool': private_pool
        })
    
    return pd.DataFrame(products)

def generate_bookings_data(product_ids, n_records=800):
    """Generate Bookings CSV data"""
    
    confirmation_statuses = ['Confirmed', 'Pending', 'Cancelled', 'Checked-in', 'Checked-out']
    
    bookings = []
    base_creation_date = datetime(2023, 6, 1)
    
    for i in range(1, n_records + 1):
        product_id = random.choice(product_ids)
        
        # Creation date should be before arrival date
        creation_date = base_creation_date + timedelta(days=random.randint(0, 300))
        
        # Arrival date should be after creation date
        arrival_date = creation_date + timedelta(days=random.randint(1, 90))
        
        confirmation_status = random.choice(confirmation_statuses)
        
        bookings.append({
            'Id': i,
            'Product Id': product_id,
            'Creation Date': creation_date.strftime('%Y-%m-%d'),
            'Confirmation Status': confirmation_status,
            'Arrival Date': arrival_date.strftime('%Y-%m-%d')
        })
    
    return pd.DataFrame(bookings)

def generate_buildings_data(product_ids, n_buildings=15):
    """Generate Buildings CSV data"""
    
    building_names = [f"Building {chr(65 + i)}" for i in range(26)]  # Building A, B, C, etc.
    
    buildings = []
    
    # Assign each product to a building
    for product_id in product_ids:
        building = random.choice(building_names[:n_buildings])
        buildings.append({
            'Building': building,
            'Product Id': product_id
        })
    
    return pd.DataFrame(buildings)

def generate_prices_data(product_ids, n_records=600):
    """Generate Prices CSV data"""
    
    currencies = ['USD', 'EUR', 'GBP', 'EGP', 'JPY']
    
    # Base price ranges by currency
    price_ranges = {
        'USD': (50, 500),
        'EUR': (45, 450),
        'GBP': (40, 400),
        'EGP': (800, 8000),
        'JPY': (5000, 50000)
    }
    
    prices = []
    
    # Generate multiple currency entries for some products
    selected_products = random.sample(product_ids, min(n_records, len(product_ids)))
    
    for product_id in selected_products:
        # Each product might have 1-3 different currency prices
        num_currencies = random.randint(1, min(3, len(currencies)))
        product_currencies = random.sample(currencies, num_currencies)
        
        for currency in product_currencies:
            min_price, max_price = price_ranges[currency]
            price = round(random.uniform(min_price, max_price), 2)
            
            prices.append({
                'Product Id': product_id,
                'Price': price,
                'Currency': currency
            })
    
    return pd.DataFrame(prices)

def main():
    """Generate all CSV files"""
    
    print("Generating hotel sample data...")
    
    # Create output directory
    output_dir = "./pricing/ETL/Data/"
    
    # Generate Products data
    print("Generating Products data...")
    products_df = generate_products_data(500)
    products_df.to_csv(f"{output_dir}/products.csv", index=False)
    product_ids = products_df['Id'].tolist()
    
    # Generate Bookings data
    print("Generating Bookings data...")
    bookings_df = generate_bookings_data(product_ids, 800)
    bookings_df.to_csv(f"{output_dir}/bookings.csv", index=False)
    
    # Generate Buildings data
    print("Generating Buildings data...")
    buildings_df = generate_buildings_data(product_ids, 15)
    buildings_df.to_csv(f"{output_dir}/buildings.csv", index=False)
    
    # Generate Prices data
    print("Generating Prices data...")
    prices_df = generate_prices_data(product_ids, 600)
    prices_df.to_csv(f"{output_dir}/prices.csv", index=False)
    
    # Print summary statistics
    print("\n=== Data Generation Summary ===")
    print(f"Products: {len(products_df)} records")
    print(f"Bookings: {len(bookings_df)} records")
    print(f"Buildings: {len(buildings_df)} records")
    print(f"Prices: {len(prices_df)} records")
    
    # Show sample data
    print("\n=== Sample Data Preview ===")
    print("\nProducts Sample:")
    print(products_df.head(3).to_string(index=False))
    
    print("\nBookings Sample:")
    print(bookings_df.head(3).to_string(index=False))
    
    print("\nBuildings Sample:")
    print(buildings_df.head(3).to_string(index=False))
    
    print("\nPrices Sample:")
    print(prices_df.head(3).to_string(index=False))
    
    # Data type information
    print("\n=== Data Types ===")
    print("\nProducts Data Types:")
    print(products_df.dtypes)
    
    print(f"\nAll CSV files saved to '{output_dir}/' directory")

if __name__ == "__main__":
    main()