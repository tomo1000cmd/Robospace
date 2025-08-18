ROOMS = {
    "kitchen": {"x_range": (2, 15), "y_range": (2, 15), "label": "Kitchen"},
    "living": {"x_range": (16, 30), "y_range": (2, 15), "label": "Living Room"},
    "dining": {"x_range": (31, 45), "y_range": (2, 15), "label": "Dining Room"},
    "bedroom1": {"x_range": (2, 15), "y_range": (16, 30), "label": "Bedroom 1"},
    "bedroom2": {"x_range": (16, 30), "y_range": (16, 30), "label": "Bedroom 2"},
    "bathroom": {"x_range": (31, 45), "y_range": (16, 30), "label": "Bathroom"},
    "hall": {"x_range": (2, 45), "y_range": (31, 41), "label": "Hall"}
}

DOORS = [
    {"pos": (15, 8), "connects": "kitchen-living"},  # Center of kitchen right wall
    {"pos": (30, 8), "connects": "living-dining"},   # Center of living right wall
    {"pos": (8, 15), "connects": "kitchen-bedroom1"}, # Center of kitchen bottom wall
    {"pos": (23, 15), "connects": "bedroom1-bedroom2"}, # Center of bedroom1 bottom wall
    {"pos": (38, 15), "connects": "bedroom2-bathroom"}, # Center of bedroom2 bottom wall
    {"pos": (8, 30), "connects": "bedroom1-hall"},   # Center of bedroom1 bottom wall
    {"pos": (38, 30), "connects": "bathroom-hall"}   # Center of bathroom bottom wall
]