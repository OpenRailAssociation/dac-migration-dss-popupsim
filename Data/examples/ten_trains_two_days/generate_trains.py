"""Generate train schedule with 10 trains over 2 days."""
import csv
import random
from datetime import datetime, timedelta

random.seed(123)

output_file = "trains.csv"
start_date = datetime(2025, 12, 1, 6, 0, 0)

trains = []
train_times = []

# Generate 10 train arrival times over 2 days
for i in range(10):
    hours_offset = i * 4.8  # Spread trains over 48 hours
    arrival_time = start_date + timedelta(hours=hours_offset)
    train_times.append(arrival_time)

wagon_id = 1

for train_idx, arrival_time in enumerate(train_times):
    train_id = f"T{train_idx + 1}"

    # Random train length between 75 and 700 meters
    target_length = random.uniform(75, 700)
    current_length = 0

    while current_length < target_length:
        wagon_length = random.uniform(15, 25)
        is_loaded = random.choice([True, False])
        needs_retrofit = random.choice([True, True, True, False])  # 75% need retrofit

        trains.append({
            'train_id': train_id,
            'wagon_id': f'W{wagon_id:04d}',
            'arrival_time': arrival_time.strftime('%Y-%m-%dT%H:%M:%S+00:00'),
            'length': f'{wagon_length:.1f}',
            'is_loaded': str(is_loaded),
            'needs_retrofit': str(needs_retrofit),
            'Track': 'collection'
        })

        current_length += wagon_length
        wagon_id += 1

# Write to CSV
with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['train_id', 'wagon_id', 'arrival_time', 'length', 'is_loaded', 'needs_retrofit', 'Track'], delimiter=';')
    writer.writeheader()
    writer.writerows(trains)

print(f"Generated {len(trains)} wagons in {len(train_times)} trains")
print(f"Output: {output_file}")
