"""
Configuration settings and constants for the Truck-Dump Waiting-Time Optimiser
============================================================================
"""

# Mining Operation Constants
OPERATIONAL_HOURS = {
    'start': 5.0,  # 5:00 AM
    'end': 9.5,    # 9:30 AM
}

# FENI Dump Point Hierarchy - New Hierarchical Structure
FENI_DUMP_POINTS = {
    'FENI KM 0': {
        'location_code': 'FENI KM0',  # Keep backward compatibility with Excel data
        'distance_base': 'FENI KM0',  # Use this for distance calculations
        'sub_points': {
            'FENI A (LINE 1-2)': {'lines': '1-2', 'priority': 1},
            'FENI A (LINE 3-4)': {'lines': '3-4', 'priority': 1},
            'FENI B (LINE 5-6)': {'lines': '5-6', 'priority': 2},
            'FENI B (LINE 7-8)': {'lines': '7-8', 'priority': 2},
            'FENI C (LINE 9-10)': {'lines': '9-10', 'priority': 3},
            'FENI C (LINE 11-12)': {'lines': '11-12', 'priority': 3},
            'FENI D (LINE 13-14)': {'lines': '13-14', 'priority': 4},
            'FENI D (LINE 15-16)': {'lines': '15-16', 'priority': 4},
            'FENI E (LINE 17-18)': {'lines': '17-18', 'priority': 5},
            'FENI E (LINE 19-20)': {'lines': '19-20', 'priority': 5},
            'FENI F1 (LINE 21-22)': {'lines': '21-22', 'priority': 6},
            'FENI F2 (LINE 23-24)': {'lines': '23-24', 'priority': 6},
            'FENI G (LINE 25-26)': {'lines': '25-26', 'priority': 7},
            'FENI G (LINE 27-28)': {'lines': '27-28', 'priority': 7},
            'FENI H (LINE 29-30)': {'lines': '29-30', 'priority': 8},
            'FENI H (LINE 31-32)': {'lines': '31-32', 'priority': 8},
            'FENI K (LINE 33-34)': {'lines': '33-34', 'priority': 9},
            'FENI K (LINE 35-36)': {'lines': '35-36', 'priority': 9},
            'FENI L1 (LINE 37-38)': {'lines': '37-38', 'priority': 10},
            'FENI L2 (LINE 39-40)': {'lines': '39-40', 'priority': 10},
            'FENI L3 (LINE 41-42)': {'lines': '41-42', 'priority': 10},
            'FENI M (LINE 43-44)': {'lines': '43-44', 'priority': 11},
            'FENI M (LINE 45-46)': {'lines': '45-46', 'priority': 11},
            'FENI O1 (LINE 47-48)': {'lines': '47-48', 'priority': 12},
            'FENI O2 (LINE 49-50)': {'lines': '49-50', 'priority': 12},
            'FENI Q (LINE 51-52)': {'lines': '51-52', 'priority': 13},
            'FENI Q (LINE 53-54)': {'lines': '53-54', 'priority': 13},
            'FENI R (LINE 55-56)': {'lines': '55-56', 'priority': 14},
            'FENI S (LINE 57-58)': {'lines': '57-58', 'priority': 15},
            'FENI S (LINE 59-60)': {'lines': '59-60', 'priority': 15},
        }
    },
    'FENI KM 15': {
        'location_code': 'FENI KM15',  # Keep backward compatibility with Excel data
        'distance_base': 'FENI KM15',  # Use this for distance calculations
        'sub_points': {
            'FENI U1 (LINE 65-66)': {'lines': '65-66', 'priority': 1},
            'FENI U2 (LINE 67-68)': {'lines': '67-68', 'priority': 2},
            'FENI W (LINE 69-70)': {'lines': '69-70', 'priority': 3},
            'FENI W (LINE 71-72)': {'lines': '71-72', 'priority': 4},
        }
    }
}

# Helper functions for FENI management
def get_main_feni_from_sub_point(sub_point_name):
    """Get the main FENI location from a sub-point name."""
    for main_feni, config in FENI_DUMP_POINTS.items():
        if sub_point_name in config['sub_points']:
            return main_feni
    return None

def get_distance_base_for_feni(dump_location):
    """Get the base location code for distance calculations."""
    # Direct match for backward compatibility
    if dump_location in ['FENI KM0', 'FENI KM15']:
        return dump_location
    
    # Check if it's a sub-point
    for main_feni, config in FENI_DUMP_POINTS.items():
        if dump_location in config['sub_points']:
            return config['distance_base']
    
    return dump_location  # Fallback

def get_all_feni_dump_options():
    """Get all available FENI dump point options for UI selection."""
    options = []
    for main_feni, config in FENI_DUMP_POINTS.items():
        # Only add sub-points, NOT the main FENI location codes
        # Users must select specific sub-FENI lines, not general locations
        options.extend(list(config['sub_points'].keys()))
    return sorted(options)

def get_active_sub_fenis_for_main(main_feni, contractor_configs):
    """Get list of active sub-FENI points being used for a main FENI location."""
    if not contractor_configs or main_feni not in FENI_DUMP_POINTS:
        return []
    
    main_feni_config = FENI_DUMP_POINTS[main_feni]
    active_sub_fenis = []
    
    for contractor, locations in contractor_configs.items():
        for parking_location, config in locations.items():
            dump_location = config.get('dumping_location', '')
            
            # Check if this is a sub-point of the main FENI
            if dump_location in main_feni_config['sub_points']:
                truck_count = config.get('number_of_trucks', 0)
                if truck_count > 0:
                    active_sub_fenis.append({
                        'name': dump_location,
                        'contractor': contractor,
                        'parking': parking_location,
                        'trucks': truck_count,
                        'lines': main_feni_config['sub_points'][dump_location]['lines']
                    })
            # Also check backward compatibility names
            elif dump_location == main_feni_config['location_code']:
                truck_count = config.get('number_of_trucks', 0)
                if truck_count > 0:
                    active_sub_fenis.append({
                        'name': f"{main_feni} (General)",
                        'contractor': contractor,
                        'parking': parking_location,
                        'trucks': truck_count,
                        'lines': 'General'
                    })
    
    return active_sub_fenis

# Location coordinates and travel matrices
LOCATIONS = {
    'TF': {'name': 'Tonggah Ferry', 'type': 'parking'},
    'KR': {'name': 'Kris Road', 'type': 'parking'},
    'BLB': {'name': 'Bottom Loop Back', 'type': 'parking'},
    'CBB': {'name': 'Center Bottom Back', 'type': 'parking'},
    # Keep backward compatibility for main FENI locations
    'FENI km 0': {'name': 'FENI km 0', 'type': 'dump'},
    'FENI km 15': {'name': 'FENI km 15', 'type': 'dump'},
    'CP4': {'name': 'CP4', 'type': 'loading'},
    'CP2': {'name': 'CP2', 'type': 'loading'},
    'CP4-SOUTH': {'name': 'CP4-SOUTH', 'type': 'loading'},
    'CP2-NORTH': {'name': 'CP2-NORTH', 'type': 'loading'},
}

# Travel distance matrix (LEGACY - Now using real Excel data)
# Note: This is kept as fallback only when Excel data is not available
TRAVEL_DISTANCES_FALLBACK = {
    # Real locations from Excel data
    ('TF', 'FENI KM0'): 45,
    ('TF', 'FENI KM15'): 30,
    ('KR', 'FENI KM0'): 25,
    ('KR', 'FENI KM15'): 40,
    ('BLB', 'FENI KM0'): 35,
    ('BLB', 'FENI KM15'): 20,
}

# Use real Excel data primarily, fallback to above if needed
TRAVEL_DISTANCES = TRAVEL_DISTANCES_FALLBACK

# Mining Intelligence Parameters (Based on 2024-2025 Research)
MINING_INTELLIGENCE = {
    'arrival_time_window': 30,  # minutes - collision avoidance research
    'service_time_per_truck': 0.25,  # 15 minutes in hours
    'max_queue_wait': 35,  # minutes - operational constraint
    'energy_efficiency_weight': 0.3,  # from hybrid truck studies
    'queue_penalty_factor': 0.7,  # from multi-objective optimization
    'conflict_threshold': 0.5,  # hours for arrival conflict detection
    'optimization_iterations': 100,  # maximum optimization attempts
}

# Default truck configurations (updated to use real location codes and new FENI sub-points)
DEFAULT_TRUCK_CONFIG = {
    'RIM': {
        'TF': {
            'loading_location': 'TF',
            'dumping_location': 'FENI U1 (LINE 65-66)',  # Using new FENI KM15 sub-point
            'departure_time': '7:00',
            'number_of_trucks': 25
        },
        'KR': {
            'loading_location': 'KR',
            'dumping_location': 'FENI U2 (LINE 67-68)',  # Using new FENI KM15 sub-point
            'departure_time': '7:00',
            'number_of_trucks': 20
        },
        'BLB': {
            'loading_location': 'BLB',
            'dumping_location': 'FENI A (LINE 1-2)',     # Using new FENI KM0 sub-point
            'departure_time': '7:00',
            'number_of_trucks': 30
        }
    },
    'GMG': {
        'TF': {
            'loading_location': 'TF',
            'dumping_location': 'FENI W (LINE 69-70)',   # Using new FENI KM15 sub-point
            'departure_time': '6:00',
            'number_of_trucks': 30
        }
    },
    'CKB': {
        'TF': {
            'loading_location': 'TF',
            'dumping_location': 'FENI W (LINE 71-72)',   # Using new FENI KM15 sub-point
            'departure_time': '5:00',
            'number_of_trucks': 23
        },
        'KR': {
            'loading_location': 'KR',
            'dumping_location': 'FENI B (LINE 5-6)',     # Using new FENI KM0 sub-point
            'departure_time': '6:00',
            'number_of_trucks': 25
        }
    },
    'SSS': {
        'KR': {
            'loading_location': 'KR',
            'dumping_location': 'FENI C (LINE 9-10)',    # Using new FENI KM0 sub-point
            'departure_time': '6:00',
            'number_of_trucks': 20
        }
    },
    'HJS': {
        'CBB': {
            'loading_location': 'CBB',
            'dumping_location': 'FENI D (LINE 13-14)',   # Using new FENI KM0 sub-point
            'departure_time': '7:00',
            'number_of_trucks': 25
        }
    }
}

# UI Configuration
UI_CONFIG = {
    'page_title': 'Truck Scheduler',
    'page_icon': '🚛',
    'layout': 'wide',
    'sidebar_state': 'expanded',
    'theme': 'dark',
    'colors': {
        'primary': '#1a1a1a',
        'background': '#0d1117',
        'success': '#28a745',
        'warning': '#ffc107',
        'danger': '#dc3545',
        'info': '#17a2b8'
    }
}

# Data file paths
DATA_PATHS = {
    'excel_data': 'Time_Data.xlsx',
    'config_file': 'truck_config.json',
    'temp_dir': 'temp/',
    'exports_dir': 'exports/'
}

# Optimization settings
OPTIMIZATION_CONFIG = {
    'confidence_level': 0.95,
    'base_interval_minutes': 30,
    'max_optimization_time': 120,  # seconds
    'convergence_threshold': 0.01,  # improvement threshold
    'parallel_workers': 4,
}

# Validation rules
VALIDATION_RULES = {
    'min_trucks_per_contractor': 1,
    'max_trucks_per_contractor': 200,
    'min_speed': 15,  # km/h
    'max_speed': 60,  # km/h
    'valid_parking_locations': ['TF', 'KR', 'BLB', 'CBB'],  # Will be updated from Excel
    'valid_loading_locations': ['TF', 'KR', 'BLB', 'CBB'],  # Will be updated from Excel
    'valid_dumping_locations': get_all_feni_dump_options(),  # Now includes all FENI sub-points
}

# Performance thresholds
PERFORMANCE_THRESHOLDS = {
    'excellent_wait_time': 5,  # minutes
    'good_wait_time': 15,  # minutes
    'poor_wait_time': 30,  # minutes
    'critical_wait_time': 45,  # minutes
    'efficiency_target': 0.85,  # 85% efficiency target
} 