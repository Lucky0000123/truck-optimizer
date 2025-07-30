"""
Queue Simulation Utilities
==========================

This module centralises the logic for multi‑server queue simulation
within the Truck‑Dump waiting‑time optimiser.  It provides helpers to
determine how many service lines exist at a given dump sub‑point and
functions to simulate deterministic queues for an arbitrary set of
arrival and service time events.  Both the optimiser and the UI
components rely on these utilities to ensure consistent calculations.

Functions
---------

``get_server_count(subpoint_name)``
    Return the number of parallel service lines (servers) available
    at the specified sub‑point or aggregated dump location.

``multi_server_queue(arrivals, num_servers)``
    Simulate a queue with a fixed number of servers given a sequence
    of arrival and service time pairs.  Returns the average waiting
    time in minutes and the final time when the last server becomes
    free.

``simulate_subpoint_queues(events)``
    Apply ``multi_server_queue`` to each sub‑point in a mapping of
    arrival events.  Returns a dictionary of average wait times in
    minutes keyed by sub‑point.
"""

from typing import Dict, List, Tuple
import logging

from config import FENI_DUMP_POINTS, get_main_feni_from_sub_point

logger = logging.getLogger(__name__)


def get_server_count(subpoint_name: str) -> int:
    """Determine the number of service lines for a given sub‑point.

    If the sub‑point is defined explicitly in ``FENI_DUMP_POINTS``,
    the ``lines`` field is parsed to compute the count (e.g. "65-66"
    implies two lines).  For aggregated names like "FENI KM 0" or
    "FENI KM15" the server count is the sum of lines across all
    sub‑points in the corresponding zone.  If the name cannot be
    resolved, a fallback of 2 servers is returned.

    Args:
        subpoint_name: The dump location string.

    Returns:
        The number of parallel servers (>=1).
    """
    if not subpoint_name:
        return 2
    # Check explicit sub‑point definitions
    for main_feni, cfg in FENI_DUMP_POINTS.items():
        if subpoint_name in cfg['sub_points']:
            line_str = cfg['sub_points'][subpoint_name].get('lines', '')
            try:
                parts = line_str.split('-')
                if len(parts) == 2:
                    start = int(parts[0])
                    end = int(parts[1])
                    return max(1, end - start + 1)
            except Exception:
                logger.debug(f"Failed to parse line count for {subpoint_name}: {line_str}")
            return 1
    # Handle aggregated names by summing across sub‑points
    main_feni = get_main_feni_from_sub_point(subpoint_name)
    if main_feni and main_feni in FENI_DUMP_POINTS:
        total = 0
        for sp, sp_cfg in FENI_DUMP_POINTS[main_feni]['sub_points'].items():
            line_str = sp_cfg.get('lines', '')
            try:
                parts = line_str.split('-')
                if len(parts) == 2:
                    start = int(parts[0])
                    end = int(parts[1])
                    total += max(1, end - start + 1)
                else:
                    total += 1
            except Exception:
                total += 1
        return max(1, total)
    # Fallback if unresolved
    return 2


def multi_server_queue(arrivals: List[Tuple[float, float]], num_servers: int) -> Tuple[float, float]:
    """Simulate a deterministic multi‑server queue.

    Each server can process one truck at a time.  Trucks are
    assigned to the earliest free server in order of arrival.  Waiting
    time is accrued when all servers are busy at the time a truck
    arrives.  The average waiting time (in minutes) and the time
    when the last server finishes are returned.

    Args:
        arrivals: A list of ``(arrival_time, service_time)`` pairs,
            sorted by arrival time.
        num_servers: The number of parallel service servers.

    Returns:
        A tuple ``(avg_wait_minutes, end_time)`` where ``avg_wait_minutes``
        is the average waiting time in minutes per truck and
        ``end_time`` is the time (in hours) when the last service
        finishes.
    """
    if not arrivals:
        return 0.0, 0.0
    server_free_times = [0.0] * max(1, num_servers)
    total_wait = 0.0
    for arrival_time, service_time in arrivals:
        # Find earliest available server
        idx = min(range(len(server_free_times)), key=lambda i: server_free_times[i])
        wait = max(0.0, server_free_times[idx] - arrival_time)
        total_wait += wait
        start_service = arrival_time + wait
        server_free_times[idx] = start_service + service_time
    avg_wait_minutes = (total_wait / len(arrivals)) * 60.0
    end_time = max(server_free_times)
    return avg_wait_minutes, end_time


def simulate_subpoint_queues(events: Dict[str, List[Tuple[float, float]]]) -> Dict[str, float]:
    """Simulate queues for each sub‑point and return average waits.

    Args:
        events: A mapping from sub‑point to list of ``(arrival_time,
            service_time)`` pairs.  The lists should be sorted by
            arrival time.

    Returns:
        A dictionary mapping each sub‑point to the average waiting time
        (in minutes).
    """
    results: Dict[str, float] = {}
    for subpoint, arrivals in events.items():
        if not arrivals:
            results[subpoint] = 0.0
            continue
        servers = get_server_count(subpoint)
        avg_wait, _ = multi_server_queue(arrivals, servers)
        results[subpoint] = avg_wait
        logger.debug(
            f"Simulated {len(arrivals)} arrivals at {subpoint} with {servers} servers: avg wait = {avg_wait:.2f} min"
        )
    return results
