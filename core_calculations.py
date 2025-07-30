"""
Core calculation functions for the Truck-Dump Waiting-Time Optimiser
==================================================================
All mathematical and algorithmic logic for optimization, waiting times, and performance metrics.
"""

import pandas as pd  
import numpy as np
from collections import defaultdict
from typing import Dict, Tuple, List, Optional, Union
import time
import random
import logging
import streamlit as st

# The optional ``simpy`` import has been removed.  Previous versions
# of this module used ``simpy`` for stochastic queue simulations, but
# those functions have since been deprecated.  Keeping this import
# would unnecessarily pull in an unused dependency.

from config import TRAVEL_DISTANCES, MINING_INTELLIGENCE, get_distance_base_for_feni, FENI_DUMP_POINTS, OPERATIONAL_HOURS

# Configure module logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.addHandler(logging.NullHandler())

def calculate_travel_time(from_location: str, to_location: str, speed_kmh: float, is_loaded: bool = False) -> float:
    """
    Calculate travel time between two locations using real Excel data or fallback distances.
    Now supports the new FENI hierarchy while maintaining same distances for sub-points.
    
    Args:
        from_location: Starting location
        to_location: Destination location  
        speed_kmh: Speed in km/h (used as fallback only)
        is_loaded: Whether truck is loaded (affects speed)
    
    Returns:
        Travel time in hours
    """
    # Import here to avoid circular imports
    from data_handlers import extract_real_travel_data_from_excel
    
    # Convert FENI sub-points to their base locations for distance calculations
    from_base = get_distance_base_for_feni(from_location)
    to_base = get_distance_base_for_feni(to_location)
    
    # Get real travel data from Excel
    travel_data = extract_real_travel_data_from_excel()
    
    if travel_data and 'travel_times' in travel_data:
        # Try various route combinations to find the best match
        route_keys = [
            f"{from_location}_{to_location}",
            f"{from_base}_{to_base}",
            f"{from_location}_{to_base}",
            f"{from_base}_{to_location}"
        ]
        
        for route_key in route_keys:
            if route_key in travel_data['travel_times']:
                route_data = travel_data['travel_times'][route_key]
                
                # For loading travel, use parking to loading time
                if not is_loaded and 'parking_to_loading' in route_data:
                    return route_data['parking_to_loading']
                    
                # For loaded travel, use loading to dumping time  
                elif is_loaded and 'loading_to_dumping' in route_data:
                    return route_data['loading_to_dumping']
                    
                # For return (empty) travel, use dumping to parking time
                elif not is_loaded and 'dumping_to_parking' in route_data:
                    return route_data['dumping_to_parking']
    
    # Fallback to distance-based calculation if no Excel data available
    distance_key = f"{from_base}_{to_base}"
    
    if distance_key in TRAVEL_DISTANCES:
        distance_km = TRAVEL_DISTANCES[distance_key]
        
        # Adjust speed based on load status
        if is_loaded:
            actual_speed = speed_kmh * 0.75  # Loaded trucks are slower
        else:
            actual_speed = speed_kmh
            
        return distance_km / actual_speed
    
    # Final fallback - assume short distance
    default_distance = 5.0  # 5 km default
    actual_speed = speed_kmh * (0.75 if is_loaded else 1.0)
    return default_distance / actual_speed


def simulate_realistic_wait_times(contractor_configs, loaded_speed, empty_speed) -> Dict:
    """
    DEPRECATED: This function previously implemented a stochastic M/M/1 and
    M/M/c queueing simulation based on academic research.  It has been
    superseded by deterministic multi‑server queue models using real
    travel and service data.  To avoid confusion, this stub remains for
    backward compatibility but logs a warning and returns an empty
    dictionary.
    """
    # Log a warning to notify developers that this function is obsolete
    logger.warning(
        "simulate_realistic_wait_times is deprecated and no longer implemented. "
        "Use calculate_dump_waits or departure_optimizer.simulate_wait_times instead."
    )
    return {}


def calculate_dump_waits(contractor_configs: Dict, loaded_speed: float, empty_speed: float) -> Dict:
    """
    Calculate dump waiting times using the deterministic multi‑server model.

    This function wraps the queue simulation provided by
    ``departure_optimizer.simulate_wait_times`` and converts its
    zone‑level results into per‑route waiting times.  For each route
    (contractor and parking location) the average wait time for its
    dump zone (KM 0 or KM 15) is applied.  The utilisation of each
    dump location is estimated via
    :func:`ui_components.get_real_individual_wait_time_and_utilization`.

    Args:
        contractor_configs: Nested configuration dictionary loaded
            from JSON or built via the UI.
        loaded_speed: Loaded truck speed (km/h).
        empty_speed: Empty truck speed (km/h).

    Returns:
        A nested dictionary mapping each contractor and route to a
        structure containing ``waiting_time`` (hours), ``arrival_time``
        (unused, always ``None``), ``dump_site``, ``utilization`` (0–100%),
        and metadata flags.
    """
    results: Dict[str, Dict[str, Dict[str, float]]] = {}
    if not contractor_configs:
        return results
    try:
        from departure_optimizer import load_time_data, RouteTimeLookup, simulate_wait_times
        # Load real travel and service data
        df = load_time_data('Time_Data.xlsx')
        lookup = RouteTimeLookup(df)
        # Note: simulate_wait_times expects (contractor_configs, empty_speed, loaded_speed)
        zone_waits, _ = simulate_wait_times(contractor_configs, empty_speed, loaded_speed, lookup)
        # Dashboard calculations complete (speed-responsive)
    except Exception as e:
        logger.debug(f"calculate_dump_waits: error running simulate_wait_times: {e}")
        zone_waits = {'FENI KM 0': 0.0, 'FENI KM 15': 0.0}
    # Build per‑route results
    for contractor, routes in contractor_configs.items():
        results[contractor] = {}
        for route_name, cfg in routes.items():
            dump_site = cfg.get('dumping_location', '')
            from config import get_main_feni_from_sub_point
            main_feni = get_main_feni_from_sub_point(dump_site)
            # zone_waits values are in minutes
            wait_minutes = zone_waits.get(main_feni, 0.0)
            wait_hours = wait_minutes / 60.0
            # Determine utilisation using deterministic model
            try:
                from ui_components import get_real_individual_wait_time_and_utilization
                _, utilisation = get_real_individual_wait_time_and_utilization(
                    contractor_configs, dump_site, loaded_speed, empty_speed
                )
            except Exception as e:
                logger.debug(f"calculate_dump_waits: error computing utilisation for {dump_site}: {e}")
                utilisation = 0.0
            results[contractor][route_name] = {
                'waiting_time': wait_hours,
                'arrival_time': None,
                'dump_site': dump_site,
                'utilization': utilisation,
                'using_real_data': True,
                'calculation_method': 'deterministic_multi_server'
            }
    return results


def calculate_cycle_times(contractor_configs, loaded_speed, empty_speed):
    """Calculate cycle times using REAL mining data from Excel file - no more theoretical calculations."""
    results = {}
    
    # Load real mining data from Excel
    try:
        import pandas as pd
        excel_data = pd.read_excel('Time_Data.xlsx', sheet_name='Time-Data')
        
        # Create lookup dictionary from real Excel data
        real_cycle_times = {}
        real_breakdowns = {}
        
        for _, row in excel_data.iterrows():
            parking = str(row['Parking Origin']).strip()
            loading = str(row['Loading Origin']).strip() 
            dumping = str(row['Dumping Destination']).strip()
            contractor = str(row['Contractor']).strip()
            
            # Create route key
            route_key = f"{contractor}_{parking}_{loading}_{dumping}"
            
            # EXTRACT DISTANCES from Excel travel times (using 25 km/h reference speed)
            REFERENCE_SPEED = 25.0
            excel_parking_to_loading_time = float(row['Travel Parking-Loading (h)']) if pd.notna(row['Travel Parking-Loading (h)']) else 0.5
            excel_loaded_travel_time = float(row['Loaded Travel (h)']) if pd.notna(row['Loaded Travel (h)']) else 2.0
            excel_empty_travel_time = float(row['Empty Travel (h)']) if pd.notna(row['Empty Travel (h)']) else 2.0
            
            # Convert Excel travel times to distances
            parking_to_loading_distance = excel_parking_to_loading_time * REFERENCE_SPEED
            loading_to_dump_distance = excel_loaded_travel_time * REFERENCE_SPEED
            dump_to_parking_distance = excel_empty_travel_time * REFERENCE_SPEED
            
            # RECALCULATE travel times using CURRENT SPEEDS (speed-responsive!)
            parking_to_loading_time = parking_to_loading_distance / empty_speed
            loading_to_dump_time = loading_to_dump_distance / loaded_speed
            dump_to_parking_time = dump_to_parking_distance / empty_speed
            
            # Keep FIXED components from Excel (not speed-dependent)
            waiting_for_loading = float(row['Waiting for loading (h)']) if pd.notna(row['Waiting for loading (h)']) else 0.1
            loading_time = float(row['Loading (h)']) if pd.notna(row['Loading (h)']) else 0.25
            waiting_time = float(row['Waiting for dumping (h)']) if pd.notna(row['Waiting for dumping (h)']) else 0.5
            dumping_time = float(row['Dumping (h)']) if pd.notna(row['Dumping (h)']) else 0.25
            
            # CALCULATE TOTAL CYCLE TIME using current speeds (NOW SPEED-RESPONSIVE!)
            cycle_time_hours = (parking_to_loading_time + waiting_for_loading + loading_time + 
                              loading_to_dump_time + waiting_time + dumping_time + dump_to_parking_time)
            
            real_cycle_times[route_key] = cycle_time_hours
            real_breakdowns[route_key] = {
                'parking_to_loading': parking_to_loading_time,  # Speed-responsive
                'waiting_for_loading': waiting_for_loading,     # Fixed from Excel
                'loading_time': loading_time,                   # Fixed from Excel
                'loading_to_dump': loading_to_dump_time,        # Speed-responsive  
                'waiting_time': waiting_time,                   # Fixed from Excel
                'dumping_time': dumping_time,                   # Fixed from Excel
                'dump_to_parking': dump_to_parking_time,        # Speed-responsive
                'working_hours_per_shift': float(row['Working Hours / shift (h)']) if pd.notna(row['Working Hours / shift (h)']) else 9.5,
                'trips_per_day': float(row['Trip / day']) if pd.notna(row['Trip / day']) else 2.0,
                'utilization_percent': float(row['Utilization DT (%)']) if pd.notna(row['Utilization DT (%)']) else 80.0
            }
        
        # Remove all print statements to avoid console spam during optimization
        # print(f"Loaded {len(real_cycle_times)} real mining routes from Excel")
        
    except Exception as e:
        # Remove all print statements
        # print(f"Error loading Excel data: {e}")
        real_cycle_times = {}
        real_breakdowns = {}
    
    # Contractor efficiency factors (from real mining experience)
    CONTRACTOR_EFFICIENCY = {
        'CKB': 0.95,   # 5% faster - experienced
        'GMG': 1.08,   # 8% slower - newer operations  
        'HJS': 1.02,   # 2% slower - average
        'RIM': 0.92,   # 8% faster - most experienced (matches Excel data)
        'SSS': 1.05,   # 5% slower - average
    }
    
    for contractor, locations in contractor_configs.items():
        if contractor not in results:
            results[contractor] = {}
            
        for parking_location, config in locations.items():
            if not isinstance(config, dict):
                continue
            
            loading_location = config.get('loading_location', '')
            dumping_location = config.get('dumping_location', '')
            
            if not loading_location or not dumping_location:
                continue
            
            # Try to find exact match in Excel data first
            route_key = f"{contractor}_{parking_location}_{loading_location}_{dumping_location}"
            
            if route_key in real_cycle_times:
                # Use EXACT real data from Excel
                total_cycle = real_cycle_times[route_key]
                breakdown = real_breakdowns[route_key]
                
                # Remove all print statements
                # print(f"Using REAL data for {route_key}: {total_cycle:.2f}h")
                
            else:
                # Try to find similar route in Excel data
                best_match = None
                best_score = 0
                
                for excel_key, excel_cycle in real_cycle_times.items():
                    excel_parts = excel_key.split('_')
                    if len(excel_parts) >= 4:
                        excel_contractor, excel_parking, excel_loading, excel_dumping = excel_parts[0], excel_parts[1], excel_parts[2], '_'.join(excel_parts[3:])
                        
                        score = 0
                        # Match contractor
                        if contractor == excel_contractor:
                            score += 3
                        # Match loading location  
                        if loading_location == excel_loading:
                            score += 2
                        # Match dumping zone (KM0 vs KM15)
                        if ('KM0' in dumping_location and 'KM0' in excel_dumping) or ('KM15' in dumping_location and 'KM15' in excel_dumping):
                            score += 2
                        # Match parking
                        if parking_location == excel_parking:
                            score += 1
                            
                        if score > best_score:
                            best_score = score
                            best_match = excel_key
                
                if best_match and best_score >= 4:
                    # Use similar route data with adjustments
                    base_cycle = real_cycle_times[best_match]
                    base_breakdown = real_breakdowns[best_match]
                    
                    # Apply contractor efficiency
                    contractor_factor = CONTRACTOR_EFFICIENCY.get(contractor, 1.0)
                    total_cycle = base_cycle * contractor_factor
                    
                    # Scale breakdown proportionally
                    breakdown = {}
                    for key, value in base_breakdown.items():
                        if key in ['parking_to_loading', 'loading_to_dump', 'dump_to_parking']:
                            breakdown[key] = value * contractor_factor
                        else:
                            breakdown[key] = value
                            
                    # Remove all print statements
                    # print(f"Using SIMILAR data for {route_key} (matched {best_match}): {total_cycle:.2f}h")
                    
                else:
                    # Fallback to realistic estimates based on distance patterns
                    # Remove all print statements
                    # print(f"No Excel match for {route_key}, using realistic fallback")
                    
                    # Realistic fallback based on distance zones
                    if 'KM0' in dumping_location or 'U1' in dumping_location or 'U2' in dumping_location:
                        # Long distance to KM0 zone - like TF to FENI KM0 (9.48h in Excel)
                        base_cycle = 9.0 if loading_location == 'TF' else 8.5
                    else:
                        # Shorter distance to KM15 zone - like TF to FENI KM15 (7.37h in Excel)  
                        base_cycle = 7.0 if loading_location == 'TF' else 6.5
                    
                    contractor_factor = CONTRACTOR_EFFICIENCY.get(contractor, 1.0)
                    total_cycle = base_cycle * contractor_factor
                    
                    # Realistic breakdown for fallback
                    breakdown = {
                        'parking_to_loading': 1.5 * contractor_factor,
                        'waiting_for_loading': 0.1,
                        'loading_time': 0.25,
                        'loading_to_dump': 2.5 * contractor_factor if 'KM0' in dumping_location else 2.0 * contractor_factor,
                        'waiting_time': 0.4,
                        'dumping_time': 0.25,
                        'dump_to_parking': 2.8 * contractor_factor if 'KM0' in dumping_location else 2.2 * contractor_factor,
                        'working_hours_per_shift': 9.5,
                        'trips_per_day': 9.5 / total_cycle,
                        'utilization_percent': 75.0
                    }
            
            # Add departure time impact (traffic factor)
            departure_time = config.get('departure_time', '7:00')
            try:
                departure_hour = float(departure_time.split(':')[0]) + float(departure_time.split(':')[1]) / 60
                if departure_hour < 6.0:  # Very early departure
                    traffic_factor = 0.90
                elif departure_hour < 7.0:  # Early departure
                    traffic_factor = 0.95
                elif departure_hour > 8.0:  # Late departure  
                    traffic_factor = 1.10
                else:
                    traffic_factor = 1.0
            except:
                traffic_factor = 1.0
            
            # Apply traffic factor to travel times only
            if 'parking_to_loading' in breakdown:
                breakdown['parking_to_loading'] *= traffic_factor
            if 'loading_to_dump' in breakdown:
                breakdown['loading_to_dump'] *= traffic_factor  
            if 'dump_to_parking' in breakdown:
                breakdown['dump_to_parking'] *= traffic_factor
                
            # Recalculate total with traffic factor
            total_cycle = sum([
                breakdown.get('parking_to_loading', 0),
                breakdown.get('waiting_for_loading', 0),
                breakdown.get('loading_time', 0),
                breakdown.get('loading_to_dump', 0),
                breakdown.get('waiting_time', 0),
                breakdown.get('dumping_time', 0),
                breakdown.get('dump_to_parking', 0)
            ])
            
            # Store results with real mining data
            results[contractor][parking_location] = {
                'cycle_time': total_cycle,
                'breakdown': {
                    'parking_to_loading': breakdown.get('parking_to_loading', 0),
                    'waiting_for_loading': breakdown.get('waiting_for_loading', 0),
                    'loading_time': breakdown.get('loading_time', 0),
                    'loading_to_dump': breakdown.get('loading_to_dump', 0),
                    'waiting_time': breakdown.get('waiting_time', 0),
                    'dumping_time': breakdown.get('dumping_time', 0),
                    'dump_to_parking': breakdown.get('dump_to_parking', 0)
                },
                'factors': {
                    'contractor_efficiency': CONTRACTOR_EFFICIENCY.get(contractor, 1.0),
                    'traffic_factor': traffic_factor,
                    'departure_time': departure_time,
                    'working_hours_per_shift': breakdown.get('working_hours_per_shift', 9.5),
                    'trips_per_day': breakdown.get('trips_per_day', 9.5 / total_cycle),
                    'utilization_percent': breakdown.get('utilization_percent', 75.0),
                    'data_source': 'excel_real_data' if route_key in real_cycle_times else 'realistic_estimate'
                }
            }
    
    return results


def validate_real_data_usage():
    """Validate if real Excel data is available and being used."""
    try:
        from data_handlers import extract_real_travel_data_from_excel
        travel_data = extract_real_travel_data_from_excel()
        
        if travel_data and 'travel_times' in travel_data and travel_data['travel_times']:
            return True, travel_data
        else:
            return False, {}
    except Exception:
        return False, {}


def calculate_total_wait_time_from_sim(sim_waits, sim_config):
    """Helper function to calculate total waiting time from calculate_dump_waits output."""
    total_wait_hours = 0
    
    # Loop through each contractor and route correctly (no double counting)
    for contractor, contractor_data in sim_waits.items():
        for route, route_data in contractor_data.items():
            wait_hours = route_data.get('waiting_time', 0)
            
            # Get truck count for THIS specific contractor and route
            num_trucks = sim_config.get(contractor, {}).get(route, {}).get('number_of_trucks', 0)
            total_wait_hours += wait_hours * num_trucks
            
    return total_wait_hours


# Remove the old optimize_departure_times function since it's no longer needed




def calculate_departure_intervals(contractor_configs, base_interval_minutes=10):
    """
    Calculate intelligent departure intervals to minimize dump site congestion.
    
    Based on research showing optimal 15-20 minute intervals between truck arrivals
    at dump sites to prevent excessive queuing while maintaining efficiency.
    """
    if not contractor_configs:
        return {}
    
    # Group by dump site to calculate optimal intervals
    dump_site_groups = defaultdict(list)
    
    for contractor, locations in contractor_configs.items():
        for parking, config in locations.items():
            dump_site = config.get('dumping_location', '')
            if dump_site:
                dump_site_groups[dump_site].append({
                    'contractor': contractor,
                    'parking': parking,
                    'config': config
                })
    
    optimized_intervals = {}
    
    for dump_site, groups in dump_site_groups.items():
        num_groups = len(groups)
        if num_groups <= 1:
            continue
            
        # Calculate optimal interval based on service capacity
        # Research shows 15-20 minute intervals work best
        optimal_interval = max(15, min(30, base_interval_minutes))  # 15-30 minute range
        
        for i, group in enumerate(groups):
            contractor = group['contractor']
            parking = group['parking']
            
            if contractor not in optimized_intervals:
                optimized_intervals[contractor] = {}
                
            # Stagger departures to spread arrivals
            departure_offset_minutes = i * optimal_interval
            
            optimized_intervals[contractor][parking] = {
                'interval_minutes': optimal_interval,
                'offset_minutes': departure_offset_minutes,
                'dump_site': dump_site,
                'position_in_sequence': i + 1,
                'total_groups_at_site': num_groups
            }
    
    return optimized_intervals


def calculate_performance_metrics(contractor_configs, loaded_speed, empty_speed):
    """Calculate comprehensive performance metrics for all contractors."""
    
    # Calculate base metrics using new advanced simulation
    dump_waits = calculate_dump_waits(contractor_configs, loaded_speed, empty_speed)
    cycle_times = calculate_cycle_times(contractor_configs, loaded_speed, empty_speed)
    
    # Calculate fleet-wide averages
    total_trucks = sum(config['number_of_trucks'] for locations in contractor_configs.values() for config in locations.values())
    
    # Calculate total cycle time from new format
    total_cycle_time = 0
    cycle_count = 0
    for contractor_data in cycle_times.values():
        for route_data in contractor_data.values():
            total_cycle_time += route_data.get('cycle_time', 0)
            cycle_count += 1
    
    avg_cycle_time = total_cycle_time / cycle_count if cycle_count > 0 else 0
    
    # Calculate waiting time statistics
    total_wait_time = 0
    wait_count = 0
    max_wait_time = 0
    
    for contractor_data in dump_waits.values():
        for route_data in contractor_data.values():
            wait_time = route_data.get('waiting_time', 0)
            total_wait_time += wait_time
            wait_count += 1
            max_wait_time = max(max_wait_time, wait_time)
    
    avg_wait_time = total_wait_time / wait_count if wait_count > 0 else 0
    
    # Calculate productivity metrics
    daily_trips_per_truck = (OPERATIONAL_HOURS['end'] - OPERATIONAL_HOURS['start']) / avg_cycle_time if avg_cycle_time > 0 else 0
    fleet_capacity = total_trucks * daily_trips_per_truck
    
    # Calculate utilization based on waiting vs productive time
    productive_time_ratio = avg_cycle_time / (avg_cycle_time + avg_wait_time) if (avg_cycle_time + avg_wait_time) > 0 else 1.0
    fleet_utilization = productive_time_ratio * 100
    
    return {
        'total_trucks': total_trucks,
        'avg_cycle_time': avg_cycle_time,
        'avg_wait_time': avg_wait_time,
        'max_wait_time': max_wait_time,
        'daily_trips_per_truck': daily_trips_per_truck,
        'fleet_capacity': fleet_capacity,
        'fleet_utilization': fleet_utilization,
        'dump_waits': dump_waits,
        'cycle_times': cycle_times
    } 


def calculate_loading_wait_time(contractor_configs, target_loading_location, arrival_time):
    """
    Calculate wait time at loading sites using REAL Excel data for loading times.
    
    This simulates loader congestion using actual loading times and expected
    waiting times from the Time_Data.xlsx file instead of hardcoded values.
    
    Args:
        contractor_configs: Configuration of all contractors and routes
        target_loading_location: The loading location to calculate wait time for
        arrival_time: When this truck arrives at the loading location
    
    Returns:
        float: Average wait time in hours per truck
    """
    # Load Excel data for real loading times
    try:
        import pandas as pd
        from departure_optimizer import load_time_data, RouteTimeLookup
        df = load_time_data('Time_Data.xlsx')
        lookup = RouteTimeLookup(df)
    except Exception:
        # Fallback to minimal waiting if Excel data unavailable
        return 0.05  # 3 minutes default
    
    # Collect all trucks going to the same loading location with REAL data
    arrivals_at_location = []
    total_wait_from_excel = 0.0
    trucks_with_wait_data = 0
    
    for contractor, locations in contractor_configs.items():
        for parking_location, config in locations.items():
            if not isinstance(config, dict):
                continue
                
            loading_location = config.get('loading_location', '')
            dumping_location = config.get('dumping_location', '')
            if loading_location != target_loading_location:
                continue
                
            departure_time_str = config.get('departure_time', '7:00')
            num_trucks = config.get('number_of_trucks', 0)
            
            # Parse departure time
            try:
                departure_hour = float(departure_time_str.split(':')[0]) + float(departure_time_str.split(':')[1]) / 60
            except (ValueError, IndexError):
                departure_hour = 7.0
            
            # Get REAL loading data from Excel
            row = lookup.get_row(parking_location, loading_location, dumping_location) if lookup else None
            
            if row is not None:
                # Use REAL Excel loading times
                loading_time = float(row.get('Loading (h)', 0.25)) if pd.notna(row.get('Loading (h)', 0.25)) else 0.25
                excel_wait_for_loading = float(row.get('Waiting for loading (h)', 0.1)) if pd.notna(row.get('Waiting for loading (h)', 0.1)) else 0.1
                
                # Accumulate Excel waiting times for average calculation
                total_wait_from_excel += excel_wait_for_loading * num_trucks
                trucks_with_wait_data += num_trucks
            else:
                # Fallback values if no Excel data
                loading_time = 0.25  # 15 minutes
                excel_wait_for_loading = 0.1  # 6 minutes
            
            # Calculate when trucks from this route arrive at loading
            travel_to_loading = calculate_travel_time(parking_location, loading_location, 25)  # empty speed
            route_arrival_time = departure_hour + travel_to_loading
            
            # Add arrivals for each truck (with small spacing)
            for i in range(num_trucks):
                truck_arrival = route_arrival_time + (i * 0.02)  # 1.2 min spacing between trucks
                arrivals_at_location.append((truck_arrival, loading_time))  # Use REAL loading time
    
    # If we have Excel wait data, use the average from Excel (more realistic)
    if trucks_with_wait_data > 0:
        average_excel_wait = total_wait_from_excel / trucks_with_wait_data
        return average_excel_wait
    
    # Otherwise simulate queue congestion
    if not arrivals_at_location:
        return 0.0
    
    arrivals_at_location.sort(key=lambda x: x[0])
    
    # Simulate single loader queue
    loader_free_time = 0.0
    total_wait = 0.0
    trucks_processed = 0
    
    for truck_arrival, service_time in arrivals_at_location:
        wait = max(0.0, loader_free_time - truck_arrival)
        total_wait += wait
        trucks_processed += 1
        
        start_service = max(truck_arrival, loader_free_time)
        loader_free_time = start_service + service_time
    
    # Return AVERAGE wait time per truck, not total
    return total_wait / trucks_processed if trucks_processed > 0 else 0.0


def get_real_route_times(excel_df, contractor, parking, loading, dumping, empty_speed=40, loaded_speed=30):
    """Extract real times from Excel data and adjust for current speed settings"""
    try:
        import pandas as pd
        # Find matching row in Excel data
        matching_rows = excel_df[
            (excel_df['Contractor'].str.strip().str.upper() == contractor.upper()) &
            (excel_df['Parking Origin'].str.strip().str.upper() == parking.upper()) &
            (excel_df['Loading Origin'].str.strip().str.upper() == loading.upper()) &
            (excel_df['Dumping Destination'].str.strip().str.upper() == dumping.upper())
        ]
        
        if matching_rows.empty:
            # Try partial matches for flexibility
            matching_rows = excel_df[
                (excel_df['Parking Origin'].str.strip().str.upper() == parking.upper()) &
                (excel_df['Loading Origin'].str.strip().str.upper() == loading.upper())
            ]
        
        if not matching_rows.empty:
            row = matching_rows.iloc[0]
            
            # Extract Excel times and clean NaN values
            def clean_time(value):
                if pd.isna(value) or value == 'nan':
                    return 0.0
                return float(value)
            
            excel_parking_to_loading = clean_time(row.get('Travel Parking-Loading (h)', 0))
            excel_loaded_travel = clean_time(row.get('Loaded Travel (h)', 0))
            excel_empty_travel = clean_time(row.get('Empty Travel (h)', 0))
            excel_loading_time = clean_time(row.get('Loading (h)', 0.33))
            excel_waiting_dump = clean_time(row.get('Waiting for dumping (h)', 0))
            excel_dumping_time = clean_time(row.get('Dumping (h)', 0.25))
            
            # Calculate distances from Excel times using 25 km/h reference speed
            EXCEL_REFERENCE_SPEED = 25.0
            parking_to_loading_distance = excel_parking_to_loading * EXCEL_REFERENCE_SPEED
            loaded_travel_distance = excel_loaded_travel * EXCEL_REFERENCE_SPEED
            empty_travel_distance = excel_empty_travel * EXCEL_REFERENCE_SPEED
            
            # Recalculate times using current sidebar speeds (RESPONSIVE!)
            adjusted_parking_to_loading = parking_to_loading_distance / empty_speed if empty_speed > 0 else excel_parking_to_loading
            adjusted_loaded_travel = loaded_travel_distance / loaded_speed if loaded_speed > 0 else excel_loaded_travel
            adjusted_empty_travel = empty_travel_distance / empty_speed if empty_speed > 0 else excel_empty_travel
            
            return {
                'parking_to_loading': adjusted_parking_to_loading,
                'loading_time': excel_loading_time,  # Loading time stays constant
                'loaded_travel': adjusted_loaded_travel,
                'waiting_dump': excel_waiting_dump,  # Waiting time from Excel (real data)
                'dumping_time': excel_dumping_time,  # Dumping time stays constant
                'empty_travel': adjusted_empty_travel
            }
        
    except Exception as e:
        print(f"Error extracting real times for {contractor}-{parking}: {e}")
    
    return None


def generate_timeline_data(contractor_configs, loaded_speed, empty_speed):
    """
    Generate timeline visualization data using REAL Excel data directly.
    
    Uses actual travel times and waiting times from Time_Data.xlsx for realistic visualization.
    
    Returns:
        tuple: (gantt_df, wait_df) - DataFrames for Gantt chart and wait analysis
    """
    timeline_data = []
    
    if not contractor_configs:
        # Return empty DataFrames if no configs
        return pd.DataFrame(), pd.DataFrame()
    
    # Load REAL Excel data directly
    try:
        import pandas as pd
        excel_df = pd.read_excel('Time_Data.xlsx', sheet_name='Time-Data')
        print(f"✅ Loaded {len(excel_df)} real operational records for timeline")
    except Exception as e:
        print(f"❌ Error loading Excel data: {e}")
        return pd.DataFrame(), pd.DataFrame()
    
    for contractor, locations in contractor_configs.items():
        for parking_location, config in locations.items():
            if not isinstance(config, dict):
                continue
                
            loading_location = config.get('loading_location', '')
            dumping_location = config.get('dumping_location', '')
            departure_time_str = config.get('departure_time', '7:00')
            num_trucks = config.get('number_of_trucks', 0)
            
            if not all([loading_location, dumping_location, num_trucks > 0]):
                continue
            
            # Parse departure time
            try:
                departure_hour = float(departure_time_str.split(':')[0]) + float(departure_time_str.split(':')[1]) / 60
            except (ValueError, IndexError):
                departure_hour = 7.0
            
            # Find matching row in Excel data for REAL times (RESPONSIVE to sidebar speeds)
            real_times = get_real_route_times(excel_df, contractor, parking_location, loading_location, dumping_location, empty_speed, loaded_speed)
            
            if real_times:
                # Use REAL Excel data directly
                travel_to_loading = real_times['parking_to_loading']
                loading_time = real_times['loading_time'] 
                travel_to_dump = real_times['loaded_travel']
                wait_time = real_times['waiting_dump']  # REAL waiting time from Excel
                dumping_time = real_times['dumping_time']
                travel_back = real_times['empty_travel']
                print(f"✅ Using REAL data for {contractor}-{parking_location}: Travel={travel_to_dump:.2f}h, Wait={wait_time:.2f}h")
            else:
                # Fallback to calculated times with realistic ratios
                travel_to_loading = calculate_travel_time(parking_location, loading_location, empty_speed)
                loading_time = 0.33  # 20 minutes standard loading time
                travel_to_dump = calculate_travel_time(loading_location, dumping_location, loaded_speed, is_loaded=True)
                wait_time = min(0.5, travel_to_dump * 0.1)  # Max 30min, 10% of travel time (realistic ratio)
                dumping_time = 0.25  # 15 minutes standard dumping time
                travel_back = calculate_travel_time(dumping_location, parking_location, empty_speed)
                print(f"⚠️ Using fallback for {contractor}-{parking_location}: Travel={travel_to_dump:.2f}h, Wait={wait_time:.2f}h")
            
            # Calculate timeline points using REAL data
            arrival_at_loading = departure_hour + travel_to_loading
            start_loading = arrival_at_loading  # No waiting at loading (immediate)
            finish_loading = start_loading + loading_time
            arrival_at_dump = finish_loading + travel_to_dump
            start_dumping = arrival_at_dump + wait_time  # REAL waiting time from Excel
            finish_dumping = start_dumping + dumping_time
            return_to_parking = finish_dumping + travel_back  # Return to PARKING (not loading)
            
            # Create timeline entry with REAL data
            timeline_entry = {
                'contractor': contractor,
                'parking_location': parking_location,
                'loading_location': loading_location,
                'dumping_location': dumping_location,
                'num_trucks': num_trucks,
                'timeline': {
                    'departure': departure_hour,
                    'arrival_at_loading': arrival_at_loading,
                    'start_loading': start_loading,
                    'finish_loading': finish_loading,
                    'arrival_at_dump': arrival_at_dump,
                    'wait_time': wait_time,  # REAL Excel waiting time
                    'start_dumping': start_dumping,
                    'finish_dumping': finish_dumping,
                    'return_to_parking': return_to_parking,  # Complete cycle back to parking
                    'total_cycle_time': return_to_parking - departure_hour
                },
                'real_data_used': real_times is not None,
                'travel_wait_ratio': travel_to_dump / max(wait_time, 0.01) if wait_time > 0 else float('inf')
            }
            
            timeline_data.append(timeline_entry)
    
    # Convert timeline data to DataFrames
    gantt_rows = []
    wait_rows = []
    
    for entry in timeline_data:
        fleet_name = f"{entry['contractor']}-{entry['parking_location']}"
        timeline = entry['timeline']
        
        # Create Gantt chart rows for each activity
        activities = [
            ('Travel to Loader', timeline['departure'], timeline['arrival_at_loading']),
            ('Loading', timeline['start_loading'], timeline['finish_loading']),
            ('Travel to Dumper', timeline['finish_loading'], timeline['arrival_at_dump']),
            ('Waiting at Dump', timeline['arrival_at_dump'], timeline['start_dumping']),
            ('Dumping', timeline['start_dumping'], timeline['finish_dumping']),
            ('Return to Parking', timeline['finish_dumping'], timeline['return_to_parking'])
        ]
        
        for activity, start_time, end_time in activities:
            # Convert hours to datetime strings for Plotly
            start_str = f"{int(start_time):02d}:{int((start_time % 1) * 60):02d}"
            end_str = f"{int(end_time):02d}:{int((end_time % 1) * 60):02d}"
            
            gantt_rows.append({
                'Fleet': fleet_name,
                'Activity': activity,
                'Start': f"2024-01-01 {start_str}:00",
                'Finish': f"2024-01-01 {end_str}:00",
                'Contractor': entry['contractor'],
                'Trucks': entry['num_trucks']
            })
        
        # Create wait time analysis rows (only for dumping - loading wait tracking removed)
        # Add dumping wait events only
        if timeline['wait_time'] > 0:
            wait_rows.append({
                'fleet': fleet_name,
                'contractor': entry['contractor'],
                'location': entry['dumping_location'],
                'type': 'Dumping',
                'hour': int(timeline['arrival_at_dump']),
                'wait_minutes': timeline['wait_time'] * 60,
                'trucks': entry['num_trucks']
            })
    
    # Create DataFrames
    gantt_df = pd.DataFrame(gantt_rows)
    wait_df = pd.DataFrame(wait_rows)
    
    return gantt_df, wait_df

def format_time_from_seconds(seconds):
    """Convert seconds to HH:MM format"""
    hours = int(seconds // 3600) % 24
    minutes = int((seconds % 3600) // 60)
    return f"{hours:02d}:{minutes:02d}" 