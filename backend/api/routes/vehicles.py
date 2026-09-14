from fastapi import APIRouter

from database.database import get_all_vehicles


router = APIRouter(
    prefix="/vehicles",
    tags=["Vehicles"]
)


@router.get("/")
def get_vehicles():
    """
    Return all vehicles stored in the database.
    """

    vehicles = get_all_vehicles()

    return [
        {
            "id": vehicle["id"],
            "vehicle_id": vehicle["vehicle_id"],
            "vehicle_type": vehicle["vehicle_type"],
            "camera_id": vehicle["camera_id"],
            "timestamp": vehicle["timestamp"]
        }
        for vehicle in vehicles
    ]