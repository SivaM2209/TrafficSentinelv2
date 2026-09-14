from database.database import (
    create_tables,
    add_vehicle,
    get_all_vehicles
)


# Create database and tables
create_tables()


# Add some test vehicles
add_vehicle(
    vehicle_id="V-1001",
    vehicle_type="Car",
    camera_id="Camera01",
    timestamp="10:21:03"
)

add_vehicle(
    vehicle_id="V-1002",
    vehicle_type="Bus",
    camera_id="Camera01",
    timestamp="10:21:05"
)

add_vehicle(
    vehicle_id="V-1003",
    vehicle_type="Motorcycle",
    camera_id="Camera01",
    timestamp="10:21:07"
)


# Read everything from the database
vehicles = get_all_vehicles()


print("\nTrafficSentinel Database")
print("------------------------")

for vehicle in vehicles:

    print(
        f"ID: {vehicle['vehicle_id']} | "
        f"Type: {vehicle['vehicle_type']} | "
        f"Camera: {vehicle['camera_id']} | "
        f"Time: {vehicle['timestamp']}"
    )