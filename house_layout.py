ROOMS = {
    "kitchen": {"x_range": (1, 10), "y_range": (1, 10), "label": "Kitchen"},
    "living": {"x_range": (11, 20), "y_range": (1, 10), "label": "Living Room"},
    "dining": {"x_range": (21, 30), "y_range": (1, 10), "label": "Dining Room"},
    "bedroom1": {"x_range": (1, 10), "y_range": (11, 20), "label": "Bedroom 1"},
    "bedroom2": {"x_range": (11, 20), "y_range": (11, 20), "label": "Bedroom 2"},
    "bathroom": {"x_range": (21, 30), "y_range": (11, 20), "label": "Bathroom"},
    "hall": {"x_range": (1, 30), "y_range": (21, 30), "label": "Hall"}
}

DOORS = [
    {"pos": (10, 5), "connects": "kitchen-living"},
    {"pos": (20, 5), "connects": "living-dining"},
    {"pos": (5, 10), "connects": "kitchen-bedroom1"},
    {"pos": (15, 10), "connects": "bedroom1-bedroom2"},
    {"pos": (25, 10), "connects": "bedroom2-bathroom"},
    {"pos": (5, 20), "connects": "bedroom1-hall"},
    {"pos": (25, 20), "connects": "bathroom-hall"}
]