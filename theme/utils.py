from math import radians, cos, sin, sqrt, atan2

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two points (latitude, longitude) in kilometers using the Haversine formula.
    """
    R = 6371.0  # Radius of Earth in kilometers

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


def knn_search(parking_spaces, user_lat, user_lon, k=5):
    """
    K-Nearest Neighbors (KNN) search to find the nearest parking spaces.
    
    """
    distances = []
    for space in parking_spaces:
        distance = calculate_distance(user_lat, user_lon, space.latitude, space.longitude)
        distances.append((space, distance))

    # Sort by distance and return the top k results
    distances.sort(key=lambda x: x[1])
    return distances[:k]


