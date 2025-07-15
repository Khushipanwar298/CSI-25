import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import json

def generate_nyc_taxi_data(num_rows=1000, filename="nyc_taxi_sample.csv"):

    data = []
    start_date = datetime(2024, 1, 1, 0, 0, 0)

    vendor_ids = [1, 2, 3, 4]
    payment_types = [1, 2, 3, 4, 5, 6] 
    location_ids = list(range(1, 266)) 

    for i in range(num_rows):
        pickup_time = start_date + timedelta(seconds=random.randint(0, 3600 * 24 * 30)) # Within 30 days
        dropoff_time = pickup_time + timedelta(seconds=random.randint(300, 3600)) # 5 min to 1 hour trip

        fare_amount = round(random.uniform(2.5, 50.0), 2)
        extra = round(random.choice([0.0, 0.5, 1.0, 1.5]), 2)
        mta_tax = 0.50
        improvement_surcharge = 0.30
        tip_amount = round(random.uniform(0.0, fare_amount * 0.2), 2)
        tolls_amount = round(random.choice([0.0, 0.0, 0.0, 0.0, 6.55, 12.0]), 2)
        congestion_surcharge = round(random.choice([0.0, 2.5, 2.75]), 2)
        airport_fee = round(random.choice([0.0, 0.0, 1.25, 1.75]), 2)

        total_amount = round(fare_amount + extra + mta_tax + improvement_surcharge + tip_amount + tolls_amount + congestion_surcharge + airport_fee, 2)

        mock_json_data = {
            "details": {
                "trip_id": f"trip_{i}",
                "driver_rating": round(random.uniform(3.0, 5.0), 1),
                "vehicle_type": random.choice(["Sedan", "SUV", "Van"])
            },
            "promo_code_used": random.choice([True, False]),
            "notes": random.choice(["", "Quick trip", "Rush hour", "No issues"])
        }

        data.append({
            'VendorID': random.choice(vendor_ids),
            'tpep_pickup_datetime': pickup_time.strftime('%Y-%m-%d %H:%M:%S'),
            'tpep_dropoff_datetime': dropoff_time.strftime('%Y-%m-%d %H:%M:%S'),
            'passenger_count': random.randint(1, 6),
            'trip_distance': round(random.uniform(0.5, 20.0), 2),
            'RatecodeID': random.choice([1, 2, 3, 4, 5, 6]),
            'store_and_fwd_flag': random.choice(['Y', 'N']),
            'PULocationID': random.choice(location_ids),
            'DOLocationID': random.choice(location_ids),
            'payment_type': random.choice(payment_types),
            'Fare_amount': fare_amount,
            'Extra': extra,
            'MTA_tax': mta_tax,
            'Improvement_surcharge': improvement_surcharge,
            'Tip_amount': tip_amount,
            'Tolls_amount': tolls_amount,
            'Total_amount': total_amount,
            'congestion_surcharge': congestion_surcharge,
            'airport_fee': airport_fee,
            'json_data': json.dumps(mock_json_data) 
        })

    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"Generated {num_rows} rows and saved to {filename}")

if __name__ == "__main__":
    generate_nyc_taxi_data(num_rows=10000) 