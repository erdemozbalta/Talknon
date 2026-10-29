from app.utils.helpers import haversine, is_within_radius
from app.models.cafe import Cafe

def verify_user_location(user_lat, user_lon, cafe_id):
\
\
\
\
\

    cafe = Cafe.query.get(cafe_id)
    if not cafe:
        return False, None, None

    distance = haversine(user_lat, user_lon, float(cafe.latitude), float(cafe.longitude))
    is_valid = distance <= cafe.radius_meters

    return is_valid, round(distance, 1), cafe

def find_nearby_cafes(user_lat, user_lon, max_distance=500):
\
\
\
\
\
\
\
\
\
\

    cafes = Cafe.query.filter_by(is_active=True).all()
    nearby = []

    for cafe in cafes:
        distance = haversine(user_lat, user_lon, float(cafe.latitude), float(cafe.longitude))
        if distance <= max_distance:
            nearby.append((cafe, round(distance, 1)))

    nearby.sort(key=lambda x: x[1])
    return nearby

def check_cafe_proximity(user_lat, user_lon, cafe):
\
\
\
\
\

    return is_within_radius(
        user_lat, user_lon,
        float(cafe.latitude), float(cafe.longitude),
        cafe.radius_meters
    )
