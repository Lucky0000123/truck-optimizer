"""
UI Components for the Truck-Dump Waiting-Time Optimiser
======================================================
All Streamlit interface elements, layouts, and interactive components.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Tuple, Union, Optional
import base64
import io
import random

from config import (
    UI_CONFIG, VALIDATION_RULES, LOCATIONS, PERFORMANCE_THRESHOLDS, FENI_DUMP_POINTS
)
from core_calculations import calculate_dump_waits, calculate_cycle_times
from mining_intelligence import get_mining_intelligence_insights
from config import get_main_feni_from_sub_point

def get_sidebar_wait_times(contractor_configs, loaded_speed, empty_speed):
    """
    Centralized function to calculate sidebar wait times.
    This ensures all parts of the app can use the exact same logic.
    """
    if not contractor_configs:
        return {main_feni: 0 for main_feni in FENI_DUMP_POINTS}

    dump_waits = calculate_dump_waits(contractor_configs, loaded_speed, empty_speed)
    
    main_feni_metrics = {
        main_feni: {'total_wait_minutes': 0, 'trucks_affected': 0} 
        for main_feni in FENI_DUMP_POINTS
    }
    
    for contractor, routes in dump_waits.items():
        for route, data in routes.items():
            dump_site = data.get('dump_site')
            if not dump_site:
                continue
            
            main_feni = get_main_feni_from_sub_point(dump_site)
            if main_feni:
                wait_minutes = data.get('waiting_time', 0) * 60
                trucks = contractor_configs.get(contractor, {}).get(route, {}).get('number_of_trucks', 0)
                
                main_feni_metrics[main_feni]['total_wait_minutes'] += wait_minutes * trucks
                main_feni_metrics[main_feni]['trucks_affected'] += trucks

    sidebar_wait_times = {}
    for main_feni, metrics in main_feni_metrics.items():
        if metrics['trucks_affected'] > 0:
            avg_wait_min = metrics['total_wait_minutes'] / metrics['trucks_affected']
            sidebar_wait_times[main_feni] = avg_wait_min
        else:
            sidebar_wait_times[main_feni] = 0
            
    return sidebar_wait_times

def setup_page_config():
    """Configure Streamlit page settings and styling."""
    st.set_page_config(
        page_title=UI_CONFIG['page_title'],
        page_icon=UI_CONFIG['page_icon'],
        layout=UI_CONFIG['layout'],
        initial_sidebar_state=UI_CONFIG['sidebar_state']
    )

def apply_custom_styling():
    """Apply custom CSS styling for the application, including bigger, bolder navigation tabs."""
    st.markdown("""
    <style>
        /* Dark theme with minimalist grays */
        .main > div { 
            padding: 0.5rem; 
            background: #1a1a1a; 
        }
        .stApp { background: #0d1117; }
        
        /* Compact spacing */
        .block-container { 
            padding-top: 1rem !important; 
            padding-bottom: 1rem !important; 
        }
        
        /* Enhanced metric styling */
        .metric-container {
            background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
            padding: 1rem;
            border-radius: 10px;
            border-left: 4px solid #4299e1;
            margin: 0.5rem 0;
        }
        
        /* KPI card styling */
        .kpi-card {
            background: linear-gradient(45deg, #2d3748, #4a5568);
            padding: 1.2rem;
            border-radius: 12px;
            border: 2px solid #4299e1;
            margin: 0.5rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        /* Status indicators */
        .status-excellent { border-left: 5px solid #48bb78; }
        .status-good { border-left: 5px solid #4299e1; }
        .status-warning { border-left: 5px solid #ed8936; }
        .status-critical { border-left: 5px solid #f56565; }
        
        /* Mining intelligence styling */
        .mining-insight {
            background: linear-gradient(135deg, #1a365d 0%, #2a4365 100%);
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #63b3ed;
            margin: 1rem 0;
        }
        
        /* Optimization result styling */
        .optimization-result {
            background: linear-gradient(135deg, #22543d 0%, #2f855a 100%);
            padding: 1.5rem;
            border-radius: 10px;
            border: 2px solid #48bb78;
            margin: 1rem 0;
        }

        /* Make navigation tabs bigger, bolder, and more professional */
        .stTabs [data-baseweb="tab"] {
            font-size: 1.35rem !important;
            font-weight: 800 !important;
            letter-spacing: 0.01em;
            padding: 0.7rem 2.2rem 0.7rem 0.7rem !important;
            margin-right: 1.2rem !important;
            color: #e2e8f0 !important;
            border-radius: 8px 8px 0 0;
            background: transparent;
            transition: background 0.2s, color 0.2s;
        }
        .stTabs [aria-selected="true"] {
            color: #e53e3e !important;
            background: #181c22 !important;
            border-bottom: 3px solid #e53e3e !important;
            font-size: 1.5rem !important;
            font-weight: 900 !important;
        }
        .stTabs [data-baseweb="tab"]:hover {
            color: #e53e3e !important;
            background: #23272f !important;
        }
    </style>
    """, unsafe_allow_html=True)

def render_header():
    """Render the application header."""
    st.markdown("# 🚛 **Truck-Dump Waiting-Time Optimiser**")

def render_sidebar_controls(contractor_configs=None):
    """Render sidebar controls and return configuration."""
    with st.sidebar:
        # Real-time KPI section - use passed contractor_configs if available
        if contractor_configs:
            st.markdown("### ⚡ **Real-time Fleet Performance**")
            
            # Get current speed values first
            loaded_speed = st.slider("Average Loaded Speed (km/h)", 15, 50, 30, 5, help="Speed when carrying load")
            empty_speed = st.slider("Average Empty Speed (km/h)", 20, 60, 40, 5, help="Speed when empty")
            
            # Display live KPIs based on current settings using passed data
            render_kpi_cards_sidebar(contractor_configs, loaded_speed, empty_speed)
            
            st.markdown("---")
        else:
            st.markdown("### 🚗 Haul Speed")
            loaded_speed = st.slider("Average Loaded Speed (km/h)", 15, 50, 30, 5, help="Speed when carrying load")
            empty_speed = st.slider("Average Empty Speed (km/h)", 20, 60, 40, 5, help="Speed when empty")
        
        st.markdown("---")
        
        # Additional controls
        st.markdown("### ⚙️ System Settings")
        show_advanced = st.checkbox("Show Advanced Analytics", value=True)
        auto_refresh = st.checkbox("Auto-refresh Data", value=False)
        
        if auto_refresh:
            refresh_interval = st.selectbox("Refresh Interval", [30, 60, 120, 300], index=1)
        else:
            refresh_interval = None
        
        return {
            'loaded_speed': loaded_speed,
            'empty_speed': empty_speed,
            'show_advanced': show_advanced,
            'auto_refresh': auto_refresh,
            'refresh_interval': refresh_interval
        }

def render_kpi_cards(contractor_configs, loaded_speed, empty_speed):
    """Render key performance indicator cards with dump-site-specific metrics."""
    if not contractor_configs:
        st.info("Add contractor configurations to see KPIs")
        return
    
    # Calculate current metrics
    dump_waits = calculate_dump_waits(contractor_configs, loaded_speed, empty_speed)
    cycle_times = calculate_cycle_times(contractor_configs, loaded_speed, empty_speed)
    
    # Calculate totals
    total_trucks = sum(
        config['number_of_trucks'] 
        for locations in contractor_configs.values() 
        for config in locations.values()
    )
    
    # Group by dump sites to get real waiting times per dump site - FENI ONLY
    dump_site_metrics = {}
    for contractor, routes in dump_waits.items():
        for route, data in routes.items():
            dump_site = data.get('dump_site', 'Unknown')
            
            # 🎯 CRITICAL FILTER: Only process FENI sites
            if dump_site not in ['FENI KM0', 'FENI KM15']:
                continue  # Skip all non-FENI sites
            
            if dump_site not in dump_site_metrics:
                dump_site_metrics[dump_site] = {
                    'total_wait_time': 0,
                    'route_count': 0,
                    'trucks_affected': 0
                }
            
            dump_site_metrics[dump_site]['total_wait_time'] += data.get('waiting_time', 0)
            dump_site_metrics[dump_site]['route_count'] += 1
            
            # Count trucks using this dump site - get from contractor_configs
            if contractor in contractor_configs and route in contractor_configs[contractor]:
                trucks_count = contractor_configs[contractor][route].get('number_of_trucks', 0)
                dump_site_metrics[dump_site]['trucks_affected'] += trucks_count
    
    # Calculate average cycle time
    total_cycle_time = 0
    cycle_routes = 0
    if cycle_times:
        for contractor_data in cycle_times.values():
            for route_data in contractor_data.values():
                total_cycle_time += route_data.get('cycle_time', 0)
                cycle_routes += 1
    
    avg_cycle_hours = total_cycle_time / cycle_routes if cycle_routes > 0 else 0
    
    # Display KPI cards with dump-site-specific metrics
    if len(dump_site_metrics) >= 2:
        # Show separate metrics for each dump site
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "🚛 Total Fleet",
                f"{total_trucks} trucks",
                f"{len(contractor_configs)} contractors"
            )
        
        # FENI KM0 metrics (Fix key mismatch - use correct keys)
        feni_km0_data = dump_site_metrics.get('FENI KM0', {})
        feni_km0_trucks = feni_km0_data.get('trucks_affected', 1)
        feni_km0_wait = feni_km0_data.get('total_wait_time', 0) / max(feni_km0_trucks, 1)  # Average per truck
        feni_km0_wait_min = feni_km0_wait * 60
        # Handle NaN values
        if pd.isna(feni_km0_wait_min) or feni_km0_wait_min < 0:
            feni_km0_wait_min = 0.0
        feni_km0_trucks = feni_km0_data.get('trucks_affected', 0)
        
        with col2:
            st.metric(
                "🏭 FENI km 0 Wait",
                f"{feni_km0_wait_min:.1f} min",
                f"{feni_km0_trucks} trucks affected"
            )
        
        # FENI KM15 metrics (Fix key mismatch - use correct keys)  
        feni_km15_data = dump_site_metrics.get('FENI KM15', {})
        feni_km15_trucks = feni_km15_data.get('trucks_affected', 1)
        feni_km15_wait = feni_km15_data.get('total_wait_time', 0) / max(feni_km15_trucks, 1)  # Average per truck
        feni_km15_wait_min = feni_km15_wait * 60
        # Handle NaN values
        if pd.isna(feni_km15_wait_min) or feni_km15_wait_min < 0:
            feni_km15_wait_min = 0.0
        feni_km15_trucks = feni_km15_data.get('trucks_affected', 0)
        
        with col3:
            st.metric(
                "🏭 FENI km 15 Wait", 
                f"{feni_km15_wait_min:.1f} min",
                f"{feni_km15_trucks} trucks affected"
            )
        
        # Overall efficiency based on worst dump site performance
        max_wait_min = max(feni_km0_wait_min, feni_km15_wait_min)
        efficiency = max(0, 100 - (max_wait_min * 1.5))  # More realistic efficiency calculation
        
        with col4:
            st.metric(
                "⚡ System Efficiency",
                f"{efficiency:.1f}%",
                f"Avg cycle: {avg_cycle_hours:.2f}h"
            )
    else:
        # Fallback for single dump site or no data
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "🚛 Total Fleet",
                f"{total_trucks} trucks",
                f"{len(contractor_configs)} contractors"
            )
        
        # Calculate overall average for fallback
        total_wait_time = sum(data['total_wait_time'] for data in dump_site_metrics.values())
        total_trucks = sum(data['trucks_affected'] for data in dump_site_metrics.values())
        avg_wait_hours = total_wait_time / total_trucks if total_trucks > 0 else 0
        avg_wait_minutes = avg_wait_hours * 60
        
        with col2:
            st.metric(
                "⏱️ Avg Wait Time", 
                f"{avg_wait_minutes:.1f} min",
                f"Across all dump sites"
            )
        
        with col3: 
            st.metric(
                "🔄 Avg Cycle Time",
                f"{avg_cycle_hours:.2f} hrs",
                f"All routes average"
            )
        
        efficiency = max(0, 100 - (avg_wait_minutes * 2))
        
        with col4:
            st.metric(
                "⚡ Efficiency Score",
                f"{efficiency:.1f}%",
                f"System performance"
            )
    
    # Add detailed dump site breakdown
    st.markdown("---")
    st.markdown("#### 🏭 **Dump Site Performance Details**")
    
    # Debug information (HIDDEN FROM FRONTEND - Available in backend only)
    # with st.expander("🔍 Debug: Dump Site Detection", expanded=False):
    #     st.write("**Detected dump sites from calculations:**")
    #     for site, metrics in dump_site_metrics.items():
    #         st.write(f"• **{site}**: {metrics['route_count']} routes, {metrics['trucks_affected']} trucks, {metrics['total_wait_time']:.3f}h total wait")
    #     
    #     st.write("**Raw dump_waits structure:**")
    #     for contractor, routes in dump_waits.items():
    #         for route, data in routes.items():
    #             dump_site = data.get('dump_site', 'Unknown')
    #             wait_time = data.get('waiting_time', 0)
    #             st.write(f"• {contractor}-{route} → {dump_site}: {wait_time:.3f}h wait")
    
    if dump_site_metrics:
        cols = st.columns(len(dump_site_metrics))
        
        for i, (dump_site, metrics) in enumerate(dump_site_metrics.items()):
            with cols[i]:
                # Fix nan values by proper validation
                total_wait = metrics.get('total_wait_time', 0)
                route_count = max(metrics.get('route_count', 1), 1)
                
                # Handle nan and invalid values
                if total_wait is None or str(total_wait).lower() == 'nan' or not isinstance(total_wait, (int, float)):
                    total_wait = 0
                
                avg_wait_hours = total_wait / route_count
                avg_wait_min = avg_wait_hours * 60
                
                # Ensure no nan in display
                if str(avg_wait_min).lower() == 'nan' or avg_wait_min is None:
                    avg_wait_min = 0
                
                # Calculate efficiency for this dump site
                site_efficiency = max(0, 100 - (avg_wait_min * 2))
                
                st.markdown(f"""
                **🏭 {dump_site}**
                - **Wait Time**: {avg_wait_min:.1f} minutes
                - **Trucks Affected**: {metrics['trucks_affected']} trucks
                - **Routes Using**: {metrics['route_count']} routes
                - **Efficiency**: {site_efficiency:.1f}%
                """)
    else:
        st.info("No dump site data available - check your configuration.")

def render_kpi_cards_sidebar(contractor_configs, loaded_speed, empty_speed):
    """Render KPI cards in the sidebar with real-time performance data."""
    
    # Speed responsiveness active (hidden from UI)
    
    # --- Use the new centralized function for all wait time calculations ---
    # Force recalculation by adding speed values as cache key and unique ID
    import time
    import hashlib
    
    # Create unique hash based on speeds to force recalculation when speeds change
    speed_hash = hashlib.md5(f"{loaded_speed}_{empty_speed}".encode()).hexdigest()[:8]
    cache_key = f"{speed_hash}_{int(time.time()/2)}"  # Update every 2 seconds
    

    
    sidebar_waits = get_sidebar_wait_times(contractor_configs, loaded_speed, empty_speed)

    # --- Enhanced FENI KM 0 Section ---
    st.markdown("""
    <div style="background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%); padding: 1rem; border-radius: 12px; margin: 1rem 0; border: 2px solid #9ca3af;">
        <h2 style="color: white; margin: 0; font-size: 1.8rem; text-align: center;">🏭 FENI KM 0</h2>
    </div>
    """, unsafe_allow_html=True)
    
    km0_wait = sidebar_waits.get('FENI KM 0', 0)
    
    # Enhanced metric with color coding
    wait_color = "#ef4444" if km0_wait > 30 else "#f59e0b" if km0_wait > 20 else "#10b981"
    wait_status = "High" if km0_wait > 30 else "Medium" if km0_wait > 20 else "Low"
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {wait_color} 0%, rgba(0,0,0,0.1) 100%); padding: 1rem; border-radius: 8px; margin: 0.5rem 0; text-align: center;">
        <h3 style="color: white; margin: 0; font-size: 1.1rem;">Average Wait Time</h3>
        <h2 style="color: white; margin: 0.3rem 0; font-size: 2rem;">{km0_wait:.1f}</h2>
        <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 0.9rem;">min/truck ({wait_status})</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show ONLY individual dump locations that are actually being used by trucks
    used_km0_locations = get_used_individual_dump_locations(contractor_configs, 'FENI KM 0')
    if used_km0_locations:
        with st.expander("📍 Individual Dump Locations in Use (KM0)", expanded=False):
            for dump_location, truck_count in used_km0_locations.items():
                # Use the REAL waiting time and utilization from the actual calculations
                real_wait_time, utilization = get_real_individual_wait_time_and_utilization(contractor_configs, dump_location, loaded_speed, empty_speed)
                
                # Color code based on utilization (key metric)
                if utilization < 70:
                    color = "🟢"  # Low utilization = good
                    status = "Efficient"
                elif utilization < 85:
                    color = "🟡"  # Moderate utilization = caution
                    status = "Busy"
                else:
                    color = "🔴"  # High utilization = congested
                    status = "Congested"
                
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.05); padding: 0.8rem; border-radius: 8px; margin: 0.3rem 0; border-left: 4px solid {'#10b981' if utilization < 70 else '#f59e0b' if utilization < 85 else '#ef4444'};">
                    <h4 style="color: #f1f5f9; margin: 0; font-size: 1rem;">{color} {dump_location}</h4>
                    <p style="color: #94a3b8; margin: 0.3rem 0 0 0; font-size: 0.85rem;">
                        Wait: <span style="color: #fbbf24;">{real_wait_time:.1f}min</span> | 
                        Utilization: <span style="color: #60a5fa;">{utilization:.1f}%</span> | 
                        Trucks: <span style="color: #34d399;">{truck_count}</span>
                    </p>
                    <p style="color: #6b7280; margin: 0.2rem 0 0 0; font-size: 0.8rem;">Status: {status}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No individual dump locations configured for KM0")

    # --- Enhanced FENI KM 15 Section ---
    st.markdown("""
    <div style="background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%); padding: 1rem; border-radius: 12px; margin: 1rem 0; border: 2px solid #9ca3af;">
        <h2 style="color: white; margin: 0; font-size: 1.8rem; text-align: center;">🏭 FENI KM 15</h2>
    </div>
    """, unsafe_allow_html=True)
    
    km15_wait = sidebar_waits.get('FENI KM 15', 0)
    
    # Enhanced metric with color coding
    wait_color_15 = "#ef4444" if km15_wait > 30 else "#f59e0b" if km15_wait > 20 else "#10b981"
    wait_status_15 = "High" if km15_wait > 30 else "Medium" if km15_wait > 20 else "Low"
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {wait_color_15} 0%, rgba(0,0,0,0.1) 100%); padding: 1rem; border-radius: 8px; margin: 0.5rem 0; text-align: center;">
        <h3 style="color: white; margin: 0; font-size: 1.1rem;">Average Wait Time</h3>
        <h2 style="color: white; margin: 0.3rem 0; font-size: 2rem;">{km15_wait:.1f}</h2>
        <p style="color: rgba(255,255,255,0.9); margin: 0; font-size: 0.9rem;">min/truck ({wait_status_15})</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show ONLY individual dump locations that are actually being used by trucks
    used_km15_locations = get_used_individual_dump_locations(contractor_configs, 'FENI KM 15')
    if used_km15_locations:
        with st.expander("📍 Individual Dump Locations in Use (KM15)", expanded=False):
            for dump_location, truck_count in used_km15_locations.items():
                # Use the REAL waiting time and utilization from the actual calculations
                real_wait_time, utilization = get_real_individual_wait_time_and_utilization(contractor_configs, dump_location, loaded_speed, empty_speed)
                
                # Color code based on utilization (key metric)
                if utilization < 70:
                    color = "🟢"  # Low utilization = good
                    status = "Efficient"
                elif utilization < 85:
                    color = "🟡"  # Moderate utilization = caution
                    status = "Busy"
                else:
                    color = "🔴"  # High utilization = congested
                    status = "Congested"
                
                st.markdown(f"""
                <div style="background: rgba(255,255,255,0.05); padding: 0.8rem; border-radius: 8px; margin: 0.3rem 0; border-left: 4px solid {'#10b981' if utilization < 70 else '#f59e0b' if utilization < 85 else '#ef4444'};">
                    <h4 style="color: #f1f5f9; margin: 0; font-size: 1rem;">{color} {dump_location}</h4>
                    <p style="color: #94a3b8; margin: 0.3rem 0 0 0; font-size: 0.85rem;">
                        Wait: <span style="color: #fbbf24;">{real_wait_time:.1f}min</span> | 
                        Utilization: <span style="color: #60a5fa;">{utilization:.1f}%</span> | 
                        Trucks: <span style="color: #34d399;">{truck_count}</span>
                    </p>
                    <p style="color: #6b7280; margin: 0.2rem 0 0 0; font-size: 0.8rem;">Status: {status}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No individual dump locations configured for KM15")


def get_used_individual_dump_locations(contractor_configs, main_dump_site):
    """
    Get ONLY the individual dump locations that are actually being used by trucks.
    Returns dict with dump_location -> truck_count
    """
    if not contractor_configs:
        return {}
    
    used_locations = {}
    
    # Check each contractor's routes to see what individual dump locations are actually used
    for contractor, routes in contractor_configs.items():
        for route_name, config in routes.items():
            dumping_location = config.get('dumping_location', '')
            
            # Check if this dumping location belongs to the main dump site we're looking for
            from config import get_main_feni_from_sub_point
            if get_main_feni_from_sub_point(dumping_location) == main_dump_site:
                truck_count = config.get('number_of_trucks', 0)
                if truck_count > 0:  # Only count if trucks are actually assigned
                    if dumping_location in used_locations:
                        used_locations[dumping_location] += truck_count
                    else:
                        used_locations[dumping_location] = truck_count
    
    return used_locations


def get_real_individual_wait_time_and_utilization(contractor_configs, specific_dump_location, loaded_speed, empty_speed):
    """
    Calculate the real waiting time and utilisation for a specific dump sub‑point
    using a deterministic queue simulation with road variability.

    The function filters the configuration to only include trucks assigned to
    ``specific_dump_location``.  For each such truck a travel time and
    service time are computed using the Excel data (via
    :func:`departure_optimizer.compute_route_times`) and the user‑selected
    speeds.  Travel times are perturbed by a random factor in the range
    [0.95, 1.05] to represent road conditions.  All trucks depart from the
    same parking location in a procession with a 0.02‑hour spacing.  The
    queue is simulated deterministically: trucks arriving while the dump is
    busy wait until it is free, otherwise they are serviced immediately.

    Utilisation is calculated as the fraction of time the dump is busy
    between the arrival of the first truck and the completion of the last.

    Args:
        contractor_configs: Full configuration of contractors and routes.
        specific_dump_location: Exact sub‑point string, e.g. ``'FENI A (LINE 1-2)'``.
        loaded_speed: Loaded truck speed in km/h.
        empty_speed: Empty truck speed in km/h.

    Returns:
        A tuple ``(avg_wait_minutes, utilisation_percentage)``.
    """
    if not contractor_configs:
        return 0.0, 0.0

    # Filter configuration to only routes dumping at the specific subpoint
    filtered: Dict[str, Dict[str, Dict]] = {}
    total_trucks = 0
    for contractor, routes in contractor_configs.items():
        sub_routes = {}
        for route_name, cfg in routes.items():
            if cfg.get('dumping_location') == specific_dump_location:
                sub_routes[route_name] = cfg
                total_trucks += cfg.get('number_of_trucks', 0)
        if sub_routes:
            filtered[contractor] = sub_routes
    if not filtered or total_trucks == 0:
        return 0.0, 0.0

    # Import helper functions locally to avoid circular imports
    from departure_optimizer import load_time_data, RouteTimeLookup, compute_route_times
    spacing = 0.02
    df = load_time_data("Time_Data.xlsx")
    lookup = RouteTimeLookup(df)

    # Build list of (arrival_time, service_time)
    arrivals: List[Tuple[float, float]] = []
    # Determine first arrival time for utilisation calculation
    first_arrival = None
    for contractor, routes in filtered.items():
        for route_name, cfg in routes.items():
            depart_str = cfg.get('departure_time', '7:00')
            try:
                parts = depart_str.split(':')
                depart_hour = int(parts[0]) + int(parts[1]) / 60.0 if len(parts) == 2 else 7.0
            except Exception:
                depart_hour = 7.0
            num_trucks = cfg.get('number_of_trucks', 0)
            loading_loc = cfg.get('loading_location', '')
            # Compute base travel and service time
            travel_time_base, service_time = compute_route_times(
                route_name,  # parking location equals route key
                loading_loc,
                specific_dump_location,
                empty_speed,
                loaded_speed,
                lookup,
            )
            for i in range(num_trucks):
                variability = random.uniform(0.95, 1.05)
                travel_time = travel_time_base * variability
                arrival_time = depart_hour + travel_time + i * spacing
                arrivals.append((arrival_time, service_time))
                if first_arrival is None or arrival_time < first_arrival:
                    first_arrival = arrival_time

    # No arrivals - return zero
    if not arrivals:
        return 0.0, 0.0

    # Sort by arrival time
    arrivals.sort(key=lambda x: x[0])

    # Multi-server queue simulation per sub-point
    from config import FENI_DUMP_POINTS, get_main_feni_from_sub_point

    def _num_servers_for(sub_point: str) -> int:
        main = get_main_feni_from_sub_point(sub_point)
        if not main or main not in FENI_DUMP_POINTS:
            return 1
        cfg = FENI_DUMP_POINTS[main]
        if sub_point in cfg['sub_points']:
            lo, hi = map(int, cfg['sub_points'][sub_point]['lines'].split('-'))
            return max(1, hi - lo + 1)
        total = sum(int(h) - int(l) + 1
                    for sp in cfg['sub_points'].values()
                    for l, h in [sp['lines'].split('-')])
        return max(1, total)

    # then, inside the function, after you've built `arrivals`:
    servers = _num_servers_for(specific_dump_location)
    free_times = [0.0] * servers
    total_wait = 0.0
    for arrival_time, service_time in arrivals:
        idx = min(range(servers), key=lambda i: free_times[i])
        start = max(arrival_time, free_times[idx])
        total_wait += (start - arrival_time)
        free_times[idx] = start + service_time
    avg_wait_minutes = (total_wait / len(arrivals)) * 60  # minutes
    
    # Calculate end time and utilization
    end_time = max(free_times)
    total_service_time = sum(service_time for _, service_time in arrivals)
    start_time = first_arrival
    total_time_window = end_time - start_time if end_time > start_time else total_service_time
    utilisation = (total_service_time / (servers * total_time_window)) * 100.0 if total_time_window > 0 else 0.0
    utilisation = min(utilisation, 100.0)
    return avg_wait_minutes, utilisation


def get_status_class(wait_time):
    """Get CSS status class based on wait time."""
    if wait_time <= PERFORMANCE_THRESHOLDS['excellent_wait_time']:
        return "status-excellent"
    elif wait_time <= PERFORMANCE_THRESHOLDS['good_wait_time']:
        return "status-good"
    elif wait_time <= PERFORMANCE_THRESHOLDS['poor_wait_time']:
        return "status-warning"
    else:
        return "status-critical"

def calculate_efficiency(dump_waits):
    """Calculate overall fleet efficiency percentage."""
    if not dump_waits:
        return 100
    
    # Extract wait times from nested structure
    all_wait_times = []
    for contractor, routes in dump_waits.items():
        for route, data in routes.items():
            wait_time = data.get('waiting_time', 0) * 60  # Convert to minutes
            all_wait_times.append(wait_time)
    
    avg_wait = sum(all_wait_times) / len(all_wait_times) if all_wait_times else 0
    return max(0, 100 - (avg_wait * 2))  # 2% penalty per minute of waiting

def render_fleet_configuration_panel(contractor_configs, save_callback):
    """Render the fleet configuration panel with Excel-like table appearance and real data."""
    st.markdown("#### ⚙️ Fleet Configuration")
    
    # Get real locations from Excel data
    from data_handlers import get_real_locations_from_excel
    real_locations = get_real_locations_from_excel()
    
    # Session-aware save function that updates both file and session state
    def session_save_callback(updated_configs):
        # Save to file
        success = save_callback(updated_configs)
        if success:
            # Update session state with the new configuration
            st.session_state.contractor_configs = updated_configs
        return success
    
    # Display available locations
    with st.expander("📍 Available Locations (from Excel data)", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("**Loading Locations:**")
            for loc in real_locations['loading_locations']:
                st.write(f"• {loc}")
        with col2:
            st.write("**Parking Locations:**")
            for loc in real_locations['parking_locations']:
                st.write(f"• {loc}")
        with col3:
            st.write("**Dumping Locations:**")
            for loc in real_locations['dumping_locations']:
                st.write(f"• {loc}")
    
    if not contractor_configs:
        st.info("No fleet configurations found.")
        render_add_configuration_form({}, save_callback, real_locations)
        return
    
    # Convert configuration to tabular format for Excel-like display
    config_data = []
    for contractor, locations in contractor_configs.items():
        for parking_location, config in locations.items():
            config_data.append({
                'Contractor': contractor,
                'Parking Location': parking_location,
                'Loading Site': config['loading_location'],
                'Dumping Site': config['dumping_location'],
                'Departure Time': config['departure_time'],
                'Number of Trucks': config['number_of_trucks'],
                'Route': f"{parking_location} → {config['loading_location']} → {config['dumping_location']}"
            })
    
    if config_data:
        st.markdown("**✏️ Edit Configuration** (Click to modify individual entries)")
        
        # Initialize session state for tracking last saved contractor
        if 'last_saved_contractor' not in st.session_state:
            st.session_state.last_saved_contractor = None
        
        # Expandable edit sections organized by contractor
        for contractor, locations in contractor_configs.items():
            total_trucks = sum(config['number_of_trucks'] for config in locations.values())
            
            # Keep expander open if this contractor was just saved
            is_expanded = (contractor == st.session_state.last_saved_contractor)
            
            with st.expander(f"🏢 **{contractor}** ({total_trucks} trucks)", expanded=is_expanded):
                
                # Header row for Excel-like editing
                st.markdown("| Parking | Loading | Dumping | Time | Trucks | Actions |")
                st.markdown("|---------|---------|---------|------|--------|---------|")
                
                for parking_location, config in locations.items():
                    col1, col2, col3, col4, col5, col6, col7 = st.columns([1.2, 1.2, 1.5, 1.0, 1.0, 0.5, 0.5])
                    row_key = f"{contractor}_{parking_location}"
                    
                    with col1:
                        st.text(parking_location)
                    
                    with col2:
                        # Use real loading locations from Excel
                        loading_options = real_locations['loading_locations']
                        current_loading_idx = 0
                        if config['loading_location'] in loading_options:
                            current_loading_idx = loading_options.index(config['loading_location'])
                        
                        new_loading = st.selectbox(
                            "Loading", 
                            loading_options,
                            index=current_loading_idx,
                            key=f"loading_{row_key}",
                            label_visibility="collapsed"
                        )
                    
                    with col3:
                        # Use all available FENI sub-points as dumping options
                        from config import get_all_feni_dump_options
                        dumping_options = get_all_feni_dump_options()
                        
                        current_dumping_idx = 0
                        if config['dumping_location'] in dumping_options:
                            current_dumping_idx = dumping_options.index(config['dumping_location'])
                        
                        new_dumping = st.selectbox(
                            "Dumping", 
                            dumping_options,
                            index=current_dumping_idx,
                            key=f"dumping_{row_key}",
                            label_visibility="collapsed"
                        )
                    
                    with col4:
                        time_options = [f"{h:02d}:{m:02d}" for h in range(5, 10) for m in [0, 30]]
                        current_time_idx = time_options.index(config['departure_time']) if config['departure_time'] in time_options else 0
                        
                        new_time = st.selectbox(
                            "Time", 
                            time_options,
                            index=current_time_idx,
                            key=f"time_{row_key}",
                            label_visibility="collapsed"
                        )
                    
                    with col5:
                        new_trucks = st.number_input(
                            "Trucks", 
                            min_value=1, 
                            max_value=200, 
                            value=config['number_of_trucks'],
                            key=f"trucks_{row_key}",
                            label_visibility="collapsed"
                        )
                    
                    with col6:
                        if st.button("💾", key=f"save_{row_key}", help="Save Changes"):
                            contractor_configs[contractor][parking_location] = {
                                'loading_location': new_loading,
                                'dumping_location': new_dumping,
                                'departure_time': new_time,
                                'number_of_trucks': new_trucks
                            }
                            st.session_state.last_saved_contractor = contractor # Mark this contractor as saved
                            if session_save_callback(contractor_configs):
                                st.rerun()
                            # If not successful, error will be shown and UI will NOT rerun, so you can see the error.
                    
                    with col7:
                        if st.button("🗑️", key=f"remove_{row_key}", help="Remove Route"):
                            del contractor_configs[contractor][parking_location]
                            if not contractor_configs[contractor]:  # Remove contractor if no routes left
                                del contractor_configs[contractor]
                                st.session_state.last_saved_contractor = None  # No contractor to keep open
                            else:
                                st.session_state.last_saved_contractor = contractor  # Keep this contractor's expander open
                            session_save_callback(contractor_configs)
                            st.rerun()
                
                # Add new route button for this contractor - hidden by default
                st.markdown("---")
                show_add_form = st.checkbox(f"➕ Add New Route for {contractor}", key=f"show_add_{contractor}")
                if show_add_form:
                    render_add_route_form(contractor, contractor_configs, session_save_callback, real_locations)
        
        st.markdown("---")
        
        # Create DataFrame for Excel-like display
        df_config = pd.DataFrame(config_data)
        
        st.markdown("**📊 Current Fleet Configuration** (Excel-like view)")
        
        # Display as formatted table
        st.dataframe(
            df_config,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Contractor": st.column_config.TextColumn("🏢 Contractor", width="medium"),
                "Parking Location": st.column_config.TextColumn("📍 Parking", width="small"),
                "Loading Site": st.column_config.TextColumn("⛏️ Loading", width="small"),
                "Dumping Site": st.column_config.TextColumn("🏭 Dumping", width="medium"),
                "Departure Time": st.column_config.TextColumn("⏰ Time", width="small"),
                "Number of Trucks": st.column_config.NumberColumn("🚛 Trucks", width="small"),
                "Route": st.column_config.TextColumn("🛣️ Full Route", width="large")
            }
        )
        
        # Summary statistics
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        
        total_contractors = len(contractor_configs)
        total_routes = sum(len(locations) for locations in contractor_configs.values())
        total_trucks = sum(
            config['number_of_trucks'] 
            for locations in contractor_configs.values() 
            for config in locations.values()
        )
        
        # Calculate dump site distribution
        dump_distribution = {}
        for locations in contractor_configs.values():
            for config in locations.values():
                site = config['dumping_location']
                dump_distribution[site] = dump_distribution.get(site, 0) + config['number_of_trucks']
        
        # Remove dashboard summary cards (image 2)
        # st.metric("🏢 Total Contractors", total_contractors)
        # st.metric("🛣️ Total Routes", total_routes)
        # st.metric("🚛 Total Trucks", total_trucks)
        # st.metric("🏭 Primary Dump Site", f"{primary_site} ({dump_distribution[primary_site]} trucks)")
    
    # Add new contractor form
    st.markdown("---")
    render_add_configuration_form(contractor_configs, session_save_callback, real_locations)

def render_add_route_form(contractor, contractor_configs, save_callback, real_locations):
    """Render form to add new route for existing contractor."""
    with st.form(f"add_route_{contractor}"):
        col1, col2, col3, col4, col5 = st.columns([1.5, 1.5, 1.5, 1, 1])
        
        with col1:
            new_parking = st.selectbox("Parking Location", real_locations['parking_locations'])
        
        with col2:
            new_loading = st.selectbox("Loading Site", real_locations['loading_locations'])
        
        with col3:
            new_dumping = st.selectbox("Dumping Site", real_locations['dumping_locations'])
        
        with col4:
            time_options = [f"{h:02d}:{m:02d}" for h in range(5, 10) for m in [0, 30]]
            new_time = st.selectbox("Time", time_options, index=4)  # Default to 7:00
        
        with col5:
            new_trucks = st.number_input("Trucks", min_value=1, value=25)
        
        add_route_clicked = st.form_submit_button(f"➕ Add Route")
        
        if add_route_clicked:
            # Check if this parking location already exists for this contractor
            if new_parking in contractor_configs[contractor]:
                st.error(f"⚠️ {contractor} already has a route from {new_parking}. Please choose a different parking location or edit the existing route.")
            else:
                contractor_configs[contractor][new_parking] = {
                    'loading_location': new_loading,
                    'dumping_location': new_dumping,
                    'departure_time': new_time,
                    'number_of_trucks': new_trucks
                }
                st.session_state.last_saved_contractor = contractor  # Keep this contractor's expander open
                if save_callback(contractor_configs):
                    st.rerun()

def render_add_configuration_form(contractor_configs, save_callback, real_locations):
    """Render form to add new contractor configuration."""
    with st.expander("➕ Add New Contractor", expanded=False):
        with st.form("add_new_contractor"):
            col_name, col_park, col_load, col_dump, col_time, col_trucks, col_add = st.columns([1.5, 1, 1, 1.2, 0.8, 0.8, 0.7])
            
            with col_name:
                new_contractor = st.text_input("Contractor Name", placeholder="Enter contractor name")
            
            with col_park:
                new_parking = st.selectbox("Parking", real_locations['parking_locations'])
            
            with col_load:
                new_loading = st.selectbox("Loading", real_locations['loading_locations'])
            
            with col_dump:
                new_dumping = st.selectbox("Dumping", real_locations['dumping_locations'])
            
            with col_time:
                time_options = [f"{h:02d}:{m:02d}" for h in range(5, 10) for m in [0, 30]]
                new_time = st.selectbox("Time", time_options, index=4)  # Default to 7:00
            
            with col_trucks:
                new_truck_count = st.number_input("Trucks", min_value=1, value=25)
            
            with col_add:
                st.markdown("<br>", unsafe_allow_html=True)
                add_clicked = st.form_submit_button("➕ Add")
            
            if add_clicked and new_contractor:
                if new_contractor not in contractor_configs:
                    contractor_configs[new_contractor] = {}
                
                # Check if this parking location already exists for this contractor
                if new_parking in contractor_configs[new_contractor]:
                    st.error(f"⚠️ {new_contractor} already has a route from {new_parking}. Please choose a different parking location.")
                else:
                    contractor_configs[new_contractor][new_parking] = {
                        'loading_location': new_loading,
                        'dumping_location': new_dumping,
                        'departure_time': new_time,
                        'number_of_trucks': new_truck_count
                    }
                    
                    st.session_state.last_saved_contractor = new_contractor  # Keep this new contractor's expander open
                    if save_callback(contractor_configs):
                        st.rerun()

def render_performance_analytics(contractor_configs, loaded_speed, empty_speed):
    """Render performance analytics and insights."""
    st.markdown("#### 📈 Performance Analytics")
    
    if not contractor_configs:
        st.info("Configure contractors to see performance analytics")
        return
    
    # Calculate metrics
    dump_waits = calculate_dump_waits(contractor_configs, loaded_speed, empty_speed)
    cycle_times = calculate_cycle_times(contractor_configs, loaded_speed, empty_speed)
    
    # Use EXACT same logic as sidebar KPIs (which work correctly)
    dump_site_metrics = {}
    for contractor, routes in dump_waits.items():
        for route, data in routes.items():
            dump_site = data.get('dump_site', 'Unknown')
            
            if dump_site not in ['FENI KM0', 'FENI KM15']:
                continue
            
            if dump_site not in dump_site_metrics:
                dump_site_metrics[dump_site] = {
                    'total_wait_time': 0,
                    'route_count': 0,
                    'trucks_affected': 0
                }
            
            # CORRECT: Add waiting time per route (not multiplied by truck count)
            dump_site_metrics[dump_site]['total_wait_time'] += data.get('waiting_time', 0)
            dump_site_metrics[dump_site]['route_count'] += 1
            
            if contractor in contractor_configs and route in contractor_configs[contractor]:
                trucks_count = contractor_configs[contractor][route].get('number_of_trucks', 0)
                dump_site_metrics[dump_site]['trucks_affected'] += trucks_count
    
    # Show dump site performance
    st.markdown("##### 🏭 Dump Site Performance (Average per Truck)")
    
    if dump_site_metrics:
        col1, col2 = st.columns(2)
        
        with col1:
            feni_km0_data = dump_site_metrics.get('FENI KM0', {})
            if feni_km0_data and feni_km0_data['trucks_affected'] > 0:
                avg_wait_km0 = (feni_km0_data['total_wait_time'] / feni_km0_data['trucks_affected']) * 60
                st.metric(
                    "🏭 FENI KM0",
                    f"{avg_wait_km0:.1f} min/truck",
                    f"{feni_km0_data['trucks_affected']} trucks"
                )
        
        with col2:
            feni_km15_data = dump_site_metrics.get('FENI KM15', {})
            if feni_km15_data and feni_km15_data['trucks_affected'] > 0:
                avg_wait_km15 = (feni_km15_data['total_wait_time'] / feni_km15_data['trucks_affected']) * 60
                st.metric(
                    "🏭 FENI KM15",
                    f"{avg_wait_km15:.1f} min/truck",
                    f"{feni_km15_data['trucks_affected']} trucks"
                )
    
    # Performance by contractor
    st.markdown("##### 🏢 Contractor Performance")
    
    contractor_performance = {}
    for contractor, routes in cycle_times.items():
        contractor_performance[contractor] = []
        for route_data in routes.values():
            contractor_performance[contractor].append(route_data.get('cycle_time', 0))
    
    # Create performance chart
    chart_data = []
    for contractor, times in contractor_performance.items():
        if times:
            avg_time = sum(times) / len(times)
            chart_data.append({
                'Contractor': contractor,
                'Avg Cycle Time (hrs)': avg_time,
                'Routes': len(times)
            })
    
    if chart_data:
        chart_df = pd.DataFrame(chart_data)
        st.bar_chart(chart_df.set_index('Contractor')['Avg Cycle Time (hrs)'])
        st.dataframe(chart_df, hide_index=True)

def render_data_analysis_tables(contractor_configs, loaded_speed, empty_speed):
    """Render detailed data analysis tables."""
    if not contractor_configs:
        st.info("Configure contractors to see data analysis")
        return
    
    # Calculate metrics
    dump_waits = calculate_dump_waits(contractor_configs, loaded_speed, empty_speed)
    cycle_times = calculate_cycle_times(contractor_configs, loaded_speed, empty_speed)
    
    st.markdown("#### 📊 Detailed Analysis")
    
    # Create comprehensive table
    analysis_data = []
    for contractor, locations in contractor_configs.items():
        for parking_location, config in locations.items():
            # Get cycle time data
            cycle_data = cycle_times.get(contractor, {}).get(parking_location, {})
            wait_data = dump_waits.get(contractor, {}).get(parking_location, {})
            
            analysis_data.append({
                'Contractor': contractor,
                'Parking': parking_location,
                'Loading': config['loading_location'],
                'Dumping': config['dumping_location'],
                'Departure': config['departure_time'],
                'Trucks': config['number_of_trucks'],
                'Cycle Time (h)': cycle_data.get('cycle_time', 0),
                'Avg Wait Time per Truck (h)': wait_data.get('waiting_time', 0),
                'Status': '🟢 Optimal' if cycle_data.get('cycle_time', 0) < 3.5 else '🟡 Review'
            })
    
    if analysis_data:
        analysis_df = pd.DataFrame(analysis_data)
        st.dataframe(analysis_df, hide_index=True, use_container_width=True)

def render_travel_time_matrix(loaded_speed, empty_speed):
    """Render REAL travel time matrix from Excel data - FIXED LOGIC."""
    from data_handlers import extract_real_travel_data_from_excel, get_real_travel_time_matrix
    
    # Get real travel data from Excel
    travel_data = extract_real_travel_data_from_excel()
    
    if not travel_data or not travel_data.get('locations'):
        st.warning("⚠️ No real travel data available from Excel")
        return
    
    locations = travel_data['locations']
    avg_speed = (loaded_speed + empty_speed) / 2
    
    # STEP 1: Calculate FIXED distances from Excel data (using standard speed)
    STANDARD_SPEED = 25.0  # km/h reference speed used in Excel
    fixed_distances = {}
    
    all_locations = sorted(list(set(
        locations['loading'] + locations['parking'] + ['FENI KM0', 'FENI KM15']  # Only FENI dumps
    )))
    
    for origin in all_locations:
        fixed_distances[origin] = {}
        for destination in all_locations:
            if origin == destination:
                fixed_distances[origin][destination] = 0
            else:
                # Calculate FIXED distance from Excel time data
                found_distance = None
                
                for route_key, times in travel_data['travel_times'].items():
                    parts = route_key.split('_')
                    if len(parts) >= 3:
                        parking, loading, dumping = parts[0], parts[1], parts[2]
                        
                        # Check for matching route segments and calculate FIXED distance
                        if origin == parking and destination == loading:
                            found_distance = times['parking_to_loading'] * STANDARD_SPEED  # FIXED distance
                            break
                        elif origin == loading and destination == dumping:
                            found_distance = times['loading_to_dumping'] * STANDARD_SPEED  # FIXED distance
                            break
                        elif origin == dumping and destination == parking:
                            found_distance = times['dumping_to_parking'] * STANDARD_SPEED  # FIXED distance
                            break
                
                # Use found distance or estimate
                if found_distance is not None:
                    fixed_distances[origin][destination] = found_distance
                else:
                    # Default distance estimate
                    fixed_distances[origin][destination] = 25.0  # 25 km default
    
    # STEP 2: Generate TRAVEL TIME matrix using current speed (distance ÷ speed)
    st.markdown(f"#### 🗺️ **FENI Travel Time Matrix** (hours @ {avg_speed:.1f} km/h)")
    st.markdown("*🎯 Focused on FENI KM0 and FENI KM15 routes only*")
    
    matrix_data = []
    for origin in all_locations:
        row_data = {'site': origin}
        for destination in all_locations:
            if origin == destination:
                row_data[destination] = 0
            else:
                # CORRECT: Travel time = distance ÷ current_speed
                distance_km = fixed_distances[origin][destination]
                travel_time_hours = distance_km / avg_speed
                row_data[destination] = round(travel_time_hours, 1)
        matrix_data.append(row_data)
    
    if matrix_data:
        df_matrix = pd.DataFrame(matrix_data)
        # Fix data types to prevent Arrow conversion errors
        for col in df_matrix.columns:
            if col != 'site':
                df_matrix[col] = pd.to_numeric(df_matrix[col], errors='coerce').fillna(0)
        st.dataframe(df_matrix, use_container_width=True)
        
    # STEP 3: Generate FIXED DISTANCE matrix (never changes)
    st.markdown("#### 📏 **FENI Distance Matrix** (km)")
    st.markdown("*🎯 Calculated from real FENI travel times*")
    
    distance_matrix_data = []
    for origin in all_locations:
        row_data = {'site': origin}
        for destination in all_locations:
            if origin == destination:
                row_data[destination] = 0
            else:
                # CORRECT: Use FIXED distance (never changes)
                distance_km = fixed_distances[origin][destination]
                row_data[destination] = round(distance_km, 1)
        distance_matrix_data.append(row_data)
    
    if distance_matrix_data:
        df_distance = pd.DataFrame(distance_matrix_data)
        # Fix data types to prevent Arrow conversion errors  
        for col in df_distance.columns:
            if col != 'site':
                df_distance[col] = pd.to_numeric(df_distance[col], errors='coerce').fillna(0)
        st.dataframe(df_distance, use_container_width=True)
        


def render_optimization_results(optimization_results, original_config):
    """
    Renders the optimization results with a clear before-and-after comparison.
    This function now correctly uses the optimized configuration to show real savings.
    """
    st.markdown("### 📊 **Optimization Results**")

    if not optimization_results or 'optimized_config' not in optimization_results:
        st.warning("Optimization did not produce a valid result.")
        return

    optimized_config = optimization_results['optimized_config']
    results_summary = optimization_results['results_summary']
    
    # --- Use the centralized, consistent wait time calculation for both scenarios ---
    from .ui_components import get_sidebar_wait_times
    
    # 1. Calculate "Before" wait times (Current Plan)
    current_waits = get_sidebar_wait_times(original_config, st.session_state.get('loaded_speed', 30), st.session_state.get('empty_speed', 40))
    current_km0 = current_waits.get('FENI KM 0', 0)
    current_km15 = current_waits.get('FENI KM 15', 0)

    # 2. Calculate "After" wait times (Optimized Plan)
    optimized_waits = get_sidebar_wait_times(optimized_config, st.session_state.get('loaded_speed', 30), st.session_state.get('empty_speed', 40))
    optimized_km0 = optimized_waits.get('FENI KM 0', 0)
    optimized_km15 = optimized_waits.get('FENI KM 15', 0)

    # 3. Calculate Savings
    total_current = current_km0 + current_km15
    total_optimized = optimized_km0 + optimized_km15
    time_saved = total_current - total_optimized
    improvement_pct = (time_saved / total_current * 100) if total_current > 0 else 0
    
    # Use a realistic cost per hour for savings calculation
    COST_PER_HOUR_WAITING = 75 # Standard industry cost for idle heavy machinery
    daily_savings = (time_saved / 60) * COST_PER_HOUR_WAITING * 24 # Approximate daily savings
    monthly_savings = daily_savings * 30

    st.info(f"Current schedule is already well optimized. Minor adjustments shown below." if improvement_pct < 1 else f"Optimization found a potential **{improvement_pct:.1f}%** improvement in fleet efficiency.")

    st.markdown("#### **Waiting Time Comparison**")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("🔴 **Current Plan (Dashboard)**")
        st.metric("FENI KM 0", f"{current_km0:.1f} min")
        st.metric("FENI KM 15", f"{current_km15:.1f} min")
        st.metric("Total Current", f"{total_current:.1f} min")
        
    with col2:
        st.markdown("🟢 **Optimized Plan**")
        st.metric("FENI KM 0", f"{optimized_km0:.1f} min")
        st.metric("FENI KM 15", f"{optimized_km15:.1f} min")
        st.metric("Total Optimized", f"{total_optimized:.1f} min")

    with col3:
        st.markdown("💰 **Potential Savings**")
        st.metric("Time Saved", f"{time_saved:.1f} min", f"↑ {improvement_pct:.1f}%")
        st.metric("Daily Savings", f"${daily_savings:,.0f}")
        st.metric("Monthly Savings", f"${monthly_savings:,.0f}")

    st.markdown("---")
    # ... (rest of the function for the schedule table)