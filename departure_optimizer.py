"""
Departure Time Optimization Module
=================================

This module implements a new, realistic approach to optimize truck departure
times for the Weda Bay Nickel Truck‑Dump waiting time optimiser.  The focus
is on using real timing data from the provided Excel file (``Time_Data.xlsx``)
to estimate the time it takes a truck to travel from its parking location
to the dumping site, and the time required to service (dump) each truck.

The optimisation works in two stages:

1. **Baseline Arrival Simulation** – Given the current configuration of
   contractors, parking locations, departure times and number of trucks,
   the module simulates when each truck arrives at its dump site and
   calculates the resulting queueing delays.  A simple first‑in/first‑out
   queue model is used with deterministic service times for each truck.
   Waiting times are averaged per truck and reported for the KM0 and KM15
   dump zones.

2. **Departure Time Optimisation** – For each route (contractor + parking
   location), a set of candidate departure times is tested.  The rest of
   the fleet remains unchanged.  For each candidate time the module
   reruns the arrival simulation and records the total waiting time across
   all trucks.  The candidate that yields the lowest total waiting time
   is selected as the recommended departure time for that route.  This
   greedy per‑route optimisation strikes a balance between computational
   simplicity and meaningful improvements.

The key design decisions behind this implementation are:

- **Real Data Usage** – Whenever possible, travel and service times are
  extracted from ``Time_Data.xlsx``.  Travel times are converted to
  distances using a reference speed of 25 km/h and then recalculated
  based on the speeds selected by the user in the sidebar.  Service
  times are taken from the ``Dumping (h)`` and ``Dumping Spoting (h)``
  columns.  If no matching row exists, reasonable fallbacks are used.

- **Individual Truck Arrivals** – Each truck is simulated separately.
  Trucks from the same parking location depart in a procession with a
  small spacing (default 0.02 hours, roughly 1.2 minutes) to avoid all
  trucks arriving at the dump simultaneously.

- **Deterministic Queue Model** – At each dump zone the arriving trucks
  are served one at a time using their individual service times.  A truck
  that arrives while the dump is busy waits until the previous truck
  finishes.  This creates realistic waiting times without resorting to
  stochastic queuing theory.

This module has no external dependencies beyond ``pandas`` and can be
imported by the Streamlit app to power the new optimisation tab.
"""

from __future__ import annotations

import pandas as pd
from typing import Dict, List, Tuple, Optional
import os
import logging

# Reference speed used in the Excel data to convert travel times (hours)
# into distances (kilometres).  Core calculations use this constant as
# well.  If ``REFERENCE_SPEED`` changes in other parts of the code,
# consider updating it here for consistency.
REFERENCE_SPEED = 25.0  # km/h

# Configure a logger for this module
logger = logging.getLogger(__name__)
if not logger.handlers:
    # Add a null handler by default to avoid "No handler" warnings
    logger.addHandler(logging.NullHandler())


def load_time_data(filepath: str = "Time_Data.xlsx") -> Optional[pd.DataFrame]:
    """Load the mining time data from the provided Excel file.

    The optimiser reads the ``Time-Data`` sheet from the workbook.  If the
    file cannot be read, ``None`` is returned.

    Args:
        filepath: Path to the Excel file (defaults to ``Time_Data.xlsx``).

    Returns:
        A pandas DataFrame with the timing data or ``None`` on failure.
    """
    if not os.path.exists(filepath):
        return None
    try:
        return pd.read_excel(filepath, sheet_name="Time-Data")
    except Exception:
        return None


class RouteTimeLookup:
    """Utility for looking up travel and service times from Excel data.

    The Excel file contains rows for specific combinations of parking,
    loading and dump locations per contractor.  This class builds a
    dictionary keyed by uppercase strings to allow case‑insensitive
    retrievals.  If no exact match is found for a route, a fallback is
    used during lookup.
    """

    def __init__(self, df: Optional[pd.DataFrame]):
        # internal mapping from (parking, loading, dump) to row index
        self.lookup: Dict[Tuple[str, str, str], int] = {}
        if df is None or df.empty:
            self.df = None
            return
        self.df = df.copy()
        # normalise strings and build the mapping
        for idx, row in self.df.iterrows():
            try:
                p = str(row['Parking Origin']).strip().upper()
                l = str(row['Loading Origin']).strip().upper()
                d = str(row['Dumping Destination']).strip().upper()
                self.lookup[(p, l, d)] = idx
            except Exception:
                continue

    def get_row(self, parking: str, loading: str, dump: str) -> Optional[pd.Series]:
        """Retrieve a matching row from the Excel data.

        The lookup uses uppercase keys for case‑insensitive matching.  If
        an exact match is not available, ``None`` is returned and the
        calling code should fall back to default values.

        Args:
            parking: Parking location string.
            loading: Loading location string.
            dump: Dump destination string.

        Returns:
            A pandas Series containing the matching row or ``None`` if
            no exact match is found.
        """
        if self.df is None:
            return None
        key = (parking.strip().upper(), loading.strip().upper(), dump.strip().upper())
        idx = self.lookup.get(key)
        if idx is not None:
            return self.df.loc[idx]
        return None


def compute_route_times(
    parking: str,
    loading: str,
    dump: str,
    empty_speed: float,
    loaded_speed: float,
    lookup: RouteTimeLookup,
) -> Tuple[float, float]:
    """Compute travel time to dump and service time for a route.

    Travel time consists of the time from the parking location to the
    loading site (empty), waiting and spotting at the loader, loading
    itself, and the loaded travel to the dump.  Each component is either
    read from the Excel data (scaled to the user‑selected speeds) or
    approximated via sensible defaults if the route is not present.

    Service time is the time spent at the dump location to unload the
    material and includes the spotting time at the dump.  This time is
    also read from the Excel data when available.

    Args:
        parking: Parking location name.
        loading: Loading location name.
        dump: Dump destination name.
        empty_speed: Speed in km/h when the truck is empty.
        loaded_speed: Speed in km/h when the truck is loaded.
        lookup: An instance of :class:`RouteTimeLookup` for Excel lookup.

    Returns:
        A tuple ``(travel_time_hours, service_time_hours)``.
    """
    # Attempt to get a matching row from the Excel data
    row = lookup.get_row(parking, loading, dump) if lookup else None
    # Defaults used when no row is available
    # Default wait and service components are set to realistic values based
    # on the Excel data statistics.  If updated in the future, ensure
    # consistency across modules.
    default_wait_loading = 0.10  # hours (6 minutes)
    default_spot_loading = 0.02  # hours (1.2 minutes)
    default_loading_time = 0.25  # hours (15 minutes)
    default_loaded_travel_distance = 40.0  # km, approximate distance
    default_empty_travel_distance = 40.0  # km
    # Default service time (dumping + spotting) when Excel data is unavailable.
    # Real data shows dumping plus spotting averages around 0.1 hours (6 minutes),
    # so the fallback is set accordingly.
    default_service_time = 0.10  # hours (6 minutes)
    if row is not None:
        try:
            # Travel from parking to loading
            t_parking_loading_h = row['Travel Parking-Loading (h)']
            if pd.notna(t_parking_loading_h):
                distance_pl = float(t_parking_loading_h) * REFERENCE_SPEED
                travel_parking_loading = distance_pl / empty_speed
            else:
                travel_parking_loading = default_empty_travel_distance / empty_speed
        except Exception:
            travel_parking_loading = default_empty_travel_distance / empty_speed
        # Waiting and spotting before loading
        wait_loading = row.get('Waiting for loading (h)', default_wait_loading)
        wait_loading = float(wait_loading) if pd.notna(wait_loading) else default_wait_loading
        spot_loading = row.get('Spoting-Loading', default_spot_loading)
        spot_loading = float(spot_loading) if pd.notna(spot_loading) else default_spot_loading
        loading_time = row.get('Loading (h)', default_loading_time)
        loading_time = float(loading_time) if pd.notna(loading_time) else default_loading_time
        # Loaded travel from loading to dump
        t_loaded_travel_h = row['Loaded Travel (h)']
        if pd.notna(t_loaded_travel_h):
            distance_ld = float(t_loaded_travel_h) * REFERENCE_SPEED
            loaded_travel = distance_ld / loaded_speed
        else:
            loaded_travel = default_loaded_travel_distance / loaded_speed
        # Dump service time
        dumping = row.get('Dumping (h)', default_service_time)
        dumping = float(dumping) if pd.notna(dumping) else default_service_time
        dump_spot = row.get('Dumping Spoting (h)', 0.0)
        dump_spot = float(dump_spot) if pd.notna(dump_spot) else 0.0
        service_time = dumping + dump_spot
    else:
        # Fallback: approximate travel using generic distances
        travel_parking_loading = default_empty_travel_distance / empty_speed
        wait_loading = default_wait_loading
        spot_loading = default_spot_loading
        loading_time = default_loading_time
        loaded_travel = default_loaded_travel_distance / loaded_speed
        service_time = default_service_time
    travel_time = travel_parking_loading + wait_loading + spot_loading + loading_time + loaded_travel
    return travel_time, service_time


def build_arrival_events(
    contractor_configs: Dict,
    empty_speed: float,
    loaded_speed: float,
    lookup: RouteTimeLookup,
    spacing: float = 0.02,
) -> Tuple[Dict[str, List[Tuple[float, float]]], Dict[str, List[Tuple[str, float, float, str]]]]:
    """Construct arrival and service events for all trucks keyed by sub‑point.

    Each truck is represented as a tuple ``(arrival_time, service_time)``.
    The events are grouped by the exact FENI sub‑point specified in the
    configuration (e.g., ``'FENI A (LINE 1-2)'``).  ``detailed_events``
    includes contractor metadata and also records the main FENI zone for
    downstream aggregation.

    Args:
        contractor_configs: The nested configuration dict loaded from
            ``truck_config.json`` (or Excel fallback).
        empty_speed: Speed when trucks are empty (km/h).
        loaded_speed: Speed when trucks are loaded (km/h).
        lookup: Excel lookup helper.  If ``None``, all travel and
            service times will use defaults.
        spacing: Time (in hours) between consecutive trucks from the
            same parking location.  A positive value spreads arrival
            times and reduces unrealistic clustering.

    Returns:
        A tuple ``(events, detailed_events)`` where ``events`` maps
        each sub‑point to a list of ``(arrival_time, service_time)``
        tuples.  ``detailed_events`` maps each sub‑point to a list of
        tuples ``(contractor, arrival_time, service_time, main_feni)``.
    """
    from config import get_main_feni_from_sub_point

    events: Dict[str, List[Tuple[float, float]]] = {}
    detailed_events: Dict[str, List[Tuple[str, float, float, str]]] = {}
    if not contractor_configs:
        return events, detailed_events
    for contractor, routes in contractor_configs.items():
        for parking_location, cfg in routes.items():
            try:
                dump_location = cfg.get('dumping_location')
                loading_location = cfg.get('loading_location')
                departure_time_str = cfg.get('departure_time', '7:00')
                num_trucks = cfg.get('number_of_trucks', 0)
                if not dump_location or not loading_location or num_trucks <= 0:
                    continue
                # Determine main FENI zone from sub‑point
                main_feni = get_main_feni_from_sub_point(dump_location)
                if main_feni is None:
                    continue
                # Parse departure time into fractional hours
                parts = departure_time_str.split(':')
                depart_hour = int(parts[0]) + int(parts[1]) / 60.0 if len(parts) == 2 else 7.0
                # Compute travel and service times for this route
                travel_time, service_time = compute_route_times(
                    parking_location,
                    loading_location,
                    dump_location,
                    empty_speed,
                    loaded_speed,
                    lookup
                )
                # Prepare lists
                if dump_location not in events:
                    events[dump_location] = []
                if dump_location not in detailed_events:
                    detailed_events[dump_location] = []
                # Generate arrival events for each truck
                for i in range(num_trucks):
                    arrival_time = depart_hour + travel_time + i * spacing
                    events[dump_location].append((arrival_time, service_time))
                    detailed_events[dump_location].append((contractor, arrival_time, service_time, main_feni))
            except Exception:
                continue
    # Sort events by arrival time for each sub‑point
    for key in events:
        events[key].sort(key=lambda x: x[0])
        detailed_events[key].sort(key=lambda x: x[1])
    return events, detailed_events


def simulate_queues(events: Dict[str, List[Tuple[float, float]]]) -> Dict[str, float]:
    """
    Simulate deterministic multi‑server queues for each sub‑point.

    This function is retained for backward compatibility but now
    delegates the actual simulation to the ``queue_simulation`` module.

    Args:
        events: Dictionary mapping each FENI sub‑point to a list of
            ``(arrival_time, service_time)`` tuples.  The list must
            already be sorted by arrival time.

    Returns:
        A dictionary mapping the sub‑point to the average waiting time
        (in minutes) per truck.
    """
    # Lazy import to avoid circular dependencies
    from queue_simulation import simulate_subpoint_queues
    return simulate_subpoint_queues(events)


def simulate_wait_times(
    contractor_configs: Dict,
    empty_speed: float,
    loaded_speed: float,
    lookup: RouteTimeLookup,
    spacing: float = 0.02,
) -> Tuple[Dict[str, float], Dict[str, List[Tuple[str, float, float, str]]]]:
    """Simulate queues and calculate average waiting times per main FENI zone.

    The function first builds arrival events grouped by sub‑point, runs a
    deterministic queue simulation for each sub‑point, and then
    aggregates the waiting times to the main FENI zones by weighting
    each sub‑point's average wait by the number of trucks assigned to
    that sub‑point.

    Args:
        contractor_configs: Current configuration of contractors and routes.
        empty_speed: Empty truck speed in km/h.
        loaded_speed: Loaded truck speed in km/h.
        lookup: Instance of :class:`RouteTimeLookup` for Excel lookups.
        spacing: Time between consecutive trucks from the same parking.

    Returns:
        A tuple ``(wait_times, detailed_events)`` where ``wait_times``
        contains average waiting times per main FENI zone (minutes) and
        ``detailed_events`` maps each sub‑point to a list of
        ``(contractor, arrival_time, service_time, main_feni)`` tuples.
    """
    from config import get_main_feni_from_sub_point

    events, detailed = build_arrival_events(
        contractor_configs,
        empty_speed,
        loaded_speed,
        lookup,
        spacing
    )
    # Multi-server queue simulation per sub-point (treats KM zones as 1 area)
    from config import FENI_DUMP_POINTS, get_main_feni_from_sub_point

    def _num_servers_for(sub_point: str) -> int:
        main = get_main_feni_from_sub_point(sub_point)
        if not main or main not in FENI_DUMP_POINTS:
            return 1
        cfg = FENI_DUMP_POINTS[main]
        # exact sub-point: parse "lo-hi"
        if sub_point in cfg['sub_points']:
            lo, hi = map(int, cfg['sub_points'][sub_point]['lines'].split('-'))
            return max(1, hi - lo + 1)
        # aggregated zone: sum lines of all sub-points
        total = 0
        for sp_cfg in cfg['sub_points'].values():
            lo, hi = map(int, sp_cfg['lines'].split('-'))
            total += max(1, hi - lo + 1)
        return max(1, total)

    subpoint_waits: Dict[str, float] = {}
    for subpoint, arrivals in events.items():
        servers = _num_servers_for(subpoint)
        free_times = [0.0] * servers
        total_wait = 0.0
        if not arrivals:
            subpoint_waits[subpoint] = 0.0
            continue
        for arrival_time, service_time in arrivals:
            # assign to earliest-free server
            idx = min(range(servers), key=lambda i: free_times[i])
            start = max(arrival_time, free_times[idx])
            total_wait += (start - arrival_time)
            free_times[idx] = start + service_time
        subpoint_waits[subpoint] = (total_wait / len(arrivals)) * 60.0
    # Compute number of trucks per sub‑point
    trucks_per_subpoint: Dict[str, int] = {}
    for contractor, routes in contractor_configs.items():
        for parking_location, cfg in routes.items():
            dump_location = cfg.get('dumping_location', '')
            num_trucks = cfg.get('number_of_trucks', 0)
            if not dump_location:
                continue
            trucks_per_subpoint[dump_location] = trucks_per_subpoint.get(dump_location, 0) + num_trucks
    # Aggregate to main FENI zones
    zone_wait_totals: Dict[str, float] = {'FENI KM 0': 0.0, 'FENI KM 15': 0.0}
    zone_truck_totals: Dict[str, int] = {'FENI KM 0': 0, 'FENI KM 15': 0}
    for subpoint, avg_wait in subpoint_waits.items():
        main_feni = get_main_feni_from_sub_point(subpoint)
        if main_feni is None:
            continue
        trucks = trucks_per_subpoint.get(subpoint, 0)
        zone_wait_totals[main_feni] += avg_wait * trucks
        zone_truck_totals[main_feni] += trucks
    zone_waits: Dict[str, float] = {}
    for zone in zone_wait_totals:
        if zone_truck_totals[zone] > 0:
            zone_waits[zone] = zone_wait_totals[zone] / zone_truck_totals[zone]
        else:
            zone_waits[zone] = 0.0
    # Log computed wait times per zone for debugging
    logger.debug(
        f"simulate_wait_times: zone_waits={zone_waits}, subpoint_waits={subpoint_waits}, trucks_per_subpoint={trucks_per_subpoint}"
    )
    return zone_waits, detailed


def evaluate_departure_for_route(
    contractor_configs: Dict,
    contractor: str,
    route: str,
    candidate_time: str,
    empty_speed: float,
    loaded_speed: float,
    lookup: RouteTimeLookup,
    baseline_configs: Optional[Dict] = None,
    spacing: float = 0.02,
) -> Tuple[float, Dict[str, float]]:
    """Evaluate total waiting time for a single route at a new departure time.

    The function temporarily modifies a copy of the configuration for
    the specified route and simulates the queueing system.  It returns
    the total waiting time across all trucks (summed over both dump
    zones) as well as the per‑zone averages.

    Args:
        contractor_configs: Base configuration dictionary.
        contractor: Name of the contractor for the route being tested.
        route: Parking location key for the route being tested.
        candidate_time: Proposed departure time (e.g., "6:30").
        empty_speed: Empty truck speed (km/h).
        loaded_speed: Loaded truck speed (km/h).
        lookup: Excel lookup helper.
        baseline_configs: If provided, this configuration is used for
            the rest of the fleet.  Otherwise ``contractor_configs`` is
            copied and modified internally.
        spacing: Spacing between trucks from the same parking location.

    Returns:
        A tuple ``(total_wait_minutes, per_zone_waits)`` where
        ``total_wait_minutes`` sums the average waiting times for KM0
        and KM15 (weighted by truck counts) and ``per_zone_waits`` is
        the dictionary returned by :func:`simulate_wait_times`.
    """
    import copy
    # Clone the configuration so we don't mutate the original
    if baseline_configs is not None:
        config = copy.deepcopy(baseline_configs)
    else:
        config = copy.deepcopy(contractor_configs)
    # Modify only the targeted route
    if contractor in config and route in config[contractor]:
        config[contractor][route]['departure_time'] = candidate_time
    # Simulate
    wait_times, _ = simulate_wait_times(
        config,
        empty_speed,
        loaded_speed,
        lookup,
        spacing
    )
    # Compute weighted total wait: average wait * total number of trucks
    total_wait_minutes = 0.0
    for zone in ['FENI KM 0', 'FENI KM 15']:
        # Count trucks destined for this zone
        trucks_zone = 0
        for c, routes in config.items():
            for r, cfg in routes.items():
                from config import get_main_feni_from_sub_point
                main_feni = get_main_feni_from_sub_point(cfg.get('dumping_location', ''))
                if main_feni == zone:
                    trucks_zone += cfg.get('number_of_trucks', 0)
        total_wait_minutes += wait_times.get(zone, 0.0) * trucks_zone
    # Debug logging
    logger.debug(
        f"evaluate_departure_for_route: contractor={contractor}, route={route}, candidate_time={candidate_time}, "
        f"total_wait={total_wait_minutes:.2f}, per_zone={wait_times}"
    )
    return total_wait_minutes, wait_times


def optimise_departure_times(
    contractor_configs: Dict,
    empty_speed: float,
    loaded_speed: float,
    candidate_times: List[str],
    lookup: RouteTimeLookup,
    spacing: float = 0.02,
) -> Tuple[Dict[str, Dict[str, str]], Dict[str, float], Dict[str, float]]:
    """Find the best departure time for each route given a set of candidates.

    Each route is optimised independently.  The search tests every
    candidate departure time in ``candidate_times`` and selects the
    time that minimises the total queueing delay across the entire
    fleet.  The baseline waiting times and the optimised waiting
    times (averaged per truck) are returned alongside the
    recommended departures.

    Args:
        contractor_configs: Base configuration dictionary.
        empty_speed: Empty truck speed (km/h).
        loaded_speed: Loaded truck speed (km/h).
        candidate_times: List of departure time strings to test.
        lookup: Excel lookup helper.
        spacing: Spacing between trucks from the same parking location.

    Returns:
        A tuple ``(recommended, baseline_waits, optimised_waits)``
        where ``recommended`` is a nested dict keyed by contractor and
        route with ``{'current': current_time, 'optimal': best_time}``.
        ``baseline_waits`` and ``optimised_waits`` are dictionaries
        mapping the main dump zones (``'FENI KM 0'`` and ``'FENI KM 15'``)
        to average waiting times (minutes) before and after
        optimisation.
    """
    import copy
    # Compute baseline waiting times once
    baseline_waits, _ = simulate_wait_times(
        contractor_configs,
        empty_speed,
        loaded_speed,
        lookup,
        spacing
    )
    recommended: Dict[str, Dict[str, Dict[str, str]]] = {}
    
    # FIXED APPROACH: Evaluate each route independently against the original configuration
    # This prevents sequential optimization from creating conflicts between routes
    
    # First pass: Find the best departure time for each route independently
    for contractor, routes in contractor_configs.items():
        if contractor not in recommended:
            recommended[contractor] = {}
        for route, cfg in routes.items():
            current_depart = cfg.get('departure_time', '7:00')
            best_depart = current_depart
            best_total_wait = float('inf')
            
            # Test each candidate time against the ORIGINAL configuration
            for candidate in candidate_times:
                total_wait, _ = evaluate_departure_for_route(
                    contractor_configs=contractor_configs,  # Use original config
                    contractor=contractor,
                    route=route,
                    candidate_time=candidate,
                    empty_speed=empty_speed,
                    loaded_speed=loaded_speed,
                    lookup=lookup,
                    baseline_configs=contractor_configs,  # Use original config as baseline
                    spacing=spacing
                )
                if total_wait < best_total_wait:
                    best_total_wait = total_wait
                    best_depart = candidate
                    
            # Record recommendation
            recommended[contractor][route] = {
                'current': current_depart,
                'optimal': best_depart
            }
            # Log recommendation for debugging
            logger.debug(
                f"optimise_departure_times: contractor={contractor}, route={route}, current={current_depart}, optimal={best_depart}, "
                f"best_total_wait={best_total_wait:.2f}"
            )
    
    # Second pass: Apply all optimized times together
    updated_config = copy.deepcopy(contractor_configs)
    for contractor, routes in recommended.items():
        for route, times in routes.items():
            if contractor in updated_config and route in updated_config[contractor]:
                updated_config[contractor][route]['departure_time'] = times['optimal']
    # Compute optimised waiting times with all recommended departures
    optimised_waits, _ = simulate_wait_times(
        updated_config,
        empty_speed,
        loaded_speed,
        lookup,
        spacing
    )
    # Log final waits
    logger.debug(
        f"optimise_departure_times: baseline_waits={baseline_waits}, optimised_waits={optimised_waits}, recommendations={recommended}"
    )
    return recommended, baseline_waits, optimised_waits