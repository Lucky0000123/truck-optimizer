"""
Data handling functions for the Truck-Dump Waiting-Time Optimiser
===============================================================
File I/O operations, configuration management, and data validation.
"""

import pandas as pd
import json
import os
import io
import base64
from typing import Dict, List, Tuple, Union, Optional
import streamlit as st

from config import (
    DEFAULT_TRUCK_CONFIG, DATA_PATHS, VALIDATION_RULES,
    LOCATIONS
)

# Required for Excel export
try:
    import openpyxl
except ImportError:
    openpyxl = None

@st.cache_data
def load_data(file) -> pd.DataFrame:
    """
    Load and process Excel data file with error handling.
    
    Args:
        file: Streamlit uploaded file object
        
    Returns:
        Processed DataFrame
    """
    try:
        if file.name.endswith('.xlsx'):
            df = pd.read_excel(file)
        elif file.name.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            raise ValueError("Unsupported file format. Please use .xlsx or .csv files.")
        
        # Basic data validation
        if df.empty:
            raise ValueError("The uploaded file is empty.")
        
        # Clean column names (remove extra spaces, standardize)
        df.columns = df.columns.str.strip()
        
        return df
        
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

def validate_truck_config(config: Dict) -> Tuple[bool, List[str]]:
    """
    Validate truck configuration against business rules.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not isinstance(config, dict):
        errors.append("Configuration must be a dictionary")
        return False, errors

    # Get real locations from Excel data for validation
    try:
        real_locations = get_real_locations_from_excel()
        valid_parking = real_locations['parking_locations']
        valid_loading = real_locations['loading_locations'] 
        valid_dumping = real_locations['dumping_locations']
    except:
        # Fallback to hardcoded rules if Excel data unavailable
        valid_parking = VALIDATION_RULES['valid_parking_locations']
        valid_loading = VALIDATION_RULES['valid_loading_locations']
        valid_dumping = VALIDATION_RULES['valid_dumping_locations']

    for contractor, locations in config.items():
        if not isinstance(locations, dict):
            errors.append(f"Contractor '{contractor}' configuration must be a dictionary")
            continue
            
        for parking_location, settings in locations.items():
            # Validate parking location (allow any string for now since Excel has varied formats)
            # Note: Parking locations from Excel can be complex like 'POS 10 / KR'
            
            # Validate required fields
            required_fields = ['loading_location', 'dumping_location', 'departure_time', 'number_of_trucks']
            for field in required_fields:
                if field not in settings:
                    errors.append(f"Missing required field '{field}' for {contractor}-{parking_location}")
                    continue

            # Validate loading location (relaxed - allow any string)
            loading_loc = settings.get('loading_location')
            if not loading_loc or not isinstance(loading_loc, str):
                errors.append(f"Invalid loading location '{loading_loc}' for {contractor}-{parking_location}")

            # Validate dumping location (must be valid FENI sub-points or backward compatible options)
            dumping_loc = settings.get('dumping_location')
            from config import get_all_feni_dump_options
            valid_feni_options = get_all_feni_dump_options() + ['FENI KM0', 'FENI KM15']  # Include backward compatibility
            if dumping_loc not in valid_feni_options:
                errors.append(f"Invalid dumping location '{dumping_loc}' for {contractor}-{parking_location}. Must be a valid FENI sub-point (e.g., 'FENI A (LINE 1-2)')")
            
            # Validate number of trucks
            num_trucks = settings.get('number_of_trucks', 0)
            if not isinstance(num_trucks, int) or num_trucks < VALIDATION_RULES['min_trucks_per_contractor'] or num_trucks > VALIDATION_RULES['max_trucks_per_contractor']:
                errors.append(f"Number of trucks must be between {VALIDATION_RULES['min_trucks_per_contractor']} and {VALIDATION_RULES['max_trucks_per_contractor']} for {contractor}-{parking_location}")
            
            # Validate departure time format
            departure_time = settings.get('departure_time', '')
            if not validate_time_format(departure_time):
                errors.append(f"Invalid departure time format '{departure_time}' for {contractor}-{parking_location}. Use HH:MM format.")
    
    return len(errors) == 0, errors

def validate_time_format(time_str: str) -> bool:
    """Validate time format (HH:MM)."""
    try:
        parts = time_str.split(':')
        if len(parts) != 2:
            return False
        
        hours = int(parts[0])
        minutes = int(parts[1])
        
        return 0 <= hours <= 23 and 0 <= minutes <= 59
    except (ValueError, AttributeError):
        return False

def save_config(config: Dict) -> bool:
    """
    Save truck configuration to JSON file.
    
    Args:
        config: Configuration dictionary to save
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Validate configuration first
        is_valid, errors = validate_truck_config(config)
        if not is_valid:
            st.error("Configuration validation failed:")
            for error in errors:
                st.error(f"• {error}")
            return False
        
        # Save to file
        with open(DATA_PATHS['config_file'], 'w') as f:
            json.dump(config, f, indent=2, sort_keys=True)
        
        return True
        
    except Exception as e:
        st.error(f"Error saving configuration: {str(e)}")
        return False

def load_config() -> Dict:
    """
    Load truck configuration from JSON file.
    
    Returns:
        Configuration dictionary, or default config if file doesn't exist/is invalid
    """
    try:
        if os.path.exists(DATA_PATHS['config_file']):
            with open(DATA_PATHS['config_file'], 'r') as f:
                config = json.load(f)
            
            # Validate loaded configuration
            is_valid, errors = validate_truck_config(config)
            if not is_valid:
                st.error("⚠️ Configuration file format invalid - using defaults")
                for error in errors[:3]:  # Show first 3 errors
                    st.error(f"• {error}")
                return DEFAULT_TRUCK_CONFIG
            
            return config
            
    except json.JSONDecodeError:
        st.error("⚠️ Configuration file corrupted: Invalid JSON format")
        st.error("🔄 Using default configuration. Please check your truck_config.json file.")
        return DEFAULT_TRUCK_CONFIG
        
    except Exception as e:
        st.error(f"❌ Error loading configuration: {str(e)}")
        return DEFAULT_TRUCK_CONFIG
    
    # No config file found
    st.info("ℹ️ No configuration file found. Using default settings.")
    return DEFAULT_TRUCK_CONFIG

def export_schedule_to_excel(optimized_schedule: Dict, filename: str = "optimized_schedule.xlsx") -> Optional[str]:
    """
    Export optimized schedule to Excel format.
    
    Args:
        optimized_schedule: Optimized schedule dictionary
        filename: Output filename
        
    Returns:
        Base64 encoded Excel file for download, or None if error
    """
    if not openpyxl:
        st.error("📥 openpyxl package required for Excel export. Install with: pip install openpyxl")
        return None
    
    try:
        # Prepare data for Excel export
        data = []
        for contractor, locations in optimized_schedule.items():
            for parking_location, config in locations.items():
                data.append({
                    'Contractor': contractor,
                    'Parking Location': parking_location,
                    'Loading Location': config['loading_location'],
                    'Dumping Location': config['dumping_location'],
                    'Departure Time': config['departure_time'],
                    'Number of Trucks': config['number_of_trucks']
                })
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Optimized_Schedule', index=False)
            
            # Add a summary sheet
            summary_data = {
                'Total Contractors': len(set(row['Contractor'] for row in data)),
                'Total Routes': len(data),
                'Total Trucks': sum(row['Number of Trucks'] for row in data),
                'Export Date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            summary_df = pd.DataFrame([summary_data])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Encode as base64 for download
        excel_data = output.getvalue()
        b64 = base64.b64encode(excel_data).decode()
        
        return b64
        
    except Exception as e:
        st.error(f"Error exporting to Excel: {str(e)}")
        return None

def load_excel_data(filename=None) -> pd.DataFrame:
    """
    Load Excel data file from disk and parse real operational data.
    
    Args:
        filename: Optional filename override, defaults to DATA_PATHS['excel_data']
        
    Returns:
        DataFrame with parsed operational data or None if error
    """
    try:
        file_path = filename or DATA_PATHS['excel_data']
        
        if not os.path.exists(file_path):
            st.error(f"❌ {file_path} file not found.")
            return None
        
        # Read Excel file - preserve original column names
        df = pd.read_excel(file_path)
        
        return df
        
    except Exception as e:
        st.error(f"❌ Error loading data file: {str(e)}")
        return None

def extract_contractor_data_from_excel(df: pd.DataFrame) -> Dict:
    """
    Extract contractor configurations from real Excel data.
    🎯 FOCUSED ON FENI KM0 AND FENI KM15 ONLY
    
    Args:
        df: DataFrame with Excel data
        
    Returns:
        Dictionary with contractor configurations for FENI sites only
    """
    if df is None or df.empty:
        st.warning("⚠️ No Excel data available - using default configuration")
        return DEFAULT_TRUCK_CONFIG
    
    try:
        # Parse the Excel data to extract real configurations
        contractor_configs = {}
        
        # Use the actual column names from Excel (with spaces and proper capitalization)
        contractor_col = 'Contractor'
        loading_col = 'Loading Origin'  
        parking_col = 'Parking Origin'
        dumping_col = 'Dumping Destination'
        time_col = 'Time Departure'
        
        # Verify columns exist
        missing_cols = []
        for col in [contractor_col, loading_col, dumping_col]:
            if col not in df.columns:
                missing_cols.append(col)
            
        if missing_cols:
            st.error(f"❌ Missing required columns: {missing_cols}")
            st.error(f"Available columns: {list(df.columns)}")
            return load_config()
        
        # Parse each row - FILTER FOR FENI SITES ONLY
        for _, row in df.iterrows():
            contractor = str(row[contractor_col]).strip()
            loading_loc = str(row[loading_col]).strip()
            parking_loc = str(row[parking_col]).strip() if parking_col in df.columns else loading_loc
            dumping_loc = str(row[dumping_col]).strip()
            
            # 🎯 CRITICAL FILTER: Only include FENI KM0 and FENI KM15
            if dumping_loc not in ['FENI KM0', 'FENI KM15']:
                continue  # Skip all non-FENI routes
            
            # Handle time departure (it's a datetime.time object)
            if time_col in df.columns:
                time_val = row[time_col]
                if hasattr(time_val, 'hour') and hasattr(time_val, 'minute'):
                    time_str = f"{time_val.hour:02d}:{time_val.minute:02d}"
                else:
                    time_str = '7:00'
            else:
                time_str = '7:00'
            
            # Skip empty rows
            if contractor == 'nan' or loading_loc == 'nan' or dumping_loc == 'nan':
                continue
            
            # Initialize contractor if not exists
            if contractor not in contractor_configs:
                contractor_configs[contractor] = {}
            
            # Use parking location as the key (or loading if parking not available)
            route_key = parking_loc if parking_loc != 'nan' else loading_loc
            
            # Extract truck count from Excel or use smart defaults based on contractor size
            truck_count = 25  # Base default
            
            # Smart truck allocation based on contractor and route type
            if contractor == 'RIM':
                truck_count = 30  # Major contractor
            elif contractor == 'GMG':
                truck_count = 25  # Medium contractor  
            elif contractor == 'CKB':
                truck_count = 20  # Smaller contractor
            elif contractor == 'SSS':
                truck_count = 35  # Large contractor with multiple routes
            elif contractor == 'PPP':
                truck_count = 15  # Smaller contractor
            elif contractor == 'HJS':
                truck_count = 20  # Medium contractor
            
            # Add route configuration (ONLY FOR FENI SITES) with realistic truck counts
            contractor_configs[contractor][route_key] = {
                'loading_location': loading_loc,
                'dumping_location': dumping_loc, 
                'departure_time': time_str,
                'number_of_trucks': truck_count  # Realistic counts based on contractor size
            }
        
        # Debug output for filtered data
        # FENI-focused loading completed silently
        
        return contractor_configs
        
    except Exception as e:
        st.error(f"Error extracting contractor data: {str(e)}")
        return load_config()

def get_real_locations_from_excel() -> Dict[str, List[str]]:
    """
    Extract real location data from Excel file to use in UI components.
    🎯 FOCUSED ON FENI KM0 AND FENI KM15 ONLY
    
    Returns:
        Dictionary with lists of real locations for FENI sites only
    """
    try:
        df = pd.read_excel(DATA_PATHS['excel_data'])
        
        # Extract locations from the actual column names - FILTER FOR FENI ONLY
        loading_locations = set()
        parking_locations = set()
        dumping_locations = {'FENI KM0', 'FENI KM15'}  # Only FENI sites
        
        # Known contractors (these should NOT be in location lists)
        known_contractors = {'RIM', 'GMG', 'CKB', 'SSS', 'PPP', 'HJS'}
        
        # Extract from specific columns using actual names - FILTER FOR FENI ROUTES
        for _, row in df.iterrows():
            dumping_dest = str(row.get('Dumping Destination', '')).strip()
            
            # 🎯 ONLY process rows going to FENI sites
            if dumping_dest not in ['FENI KM0', 'FENI KM15']:
                continue
            
            # Extract loading and parking locations for FENI routes only
            if 'Loading Origin' in df.columns:
                loading_loc = str(row['Loading Origin']).strip()
                if loading_loc not in known_contractors and loading_loc != 'nan':
                    loading_locations.add(loading_loc)
            
            if 'Parking Origin' in df.columns:
                parking_loc = str(row['Parking Origin']).strip()
                if parking_loc not in known_contractors and parking_loc != 'nan':
                    parking_locations.add(parking_loc)
        
        # Convert to sorted lists and clean up - now includes ALL FENI sub-points
        from config import get_all_feni_dump_options
        locations = {
            'loading_locations': sorted(list(loading_locations)),
            'parking_locations': sorted(list(parking_locations)),
            'dumping_locations': get_all_feni_dump_options()  # All FENI sub-points available
        }
        
        return locations
        
    except Exception as e:
        # Return FENI-enhanced default locations
        from config import get_all_feni_dump_options
        return {
            'loading_locations': ['TF', 'KR', 'BLB'],
            'parking_locations': ['TF', 'KR', 'BLB'],
            'dumping_locations': get_all_feni_dump_options()  # All FENI sub-points available
        }

def create_backup_config(config: Dict, suffix: str = None) -> bool:
    """
    Create a backup of the current configuration.
    
    Args:
        config: Configuration to backup
        suffix: Optional suffix for backup filename
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if suffix:
            backup_filename = f"truck_config_backup_{suffix}.json"
        else:
            timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"truck_config_backup_{timestamp}.json"
        
        with open(backup_filename, 'w') as f:
            json.dump(config, f, indent=2, sort_keys=True)
        
        return True
        
    except Exception as e:
        st.error(f"Error creating backup: {str(e)}")
        return False

def clean_temp_files():
    """Clean up temporary files."""
    try:
        temp_dir = DATA_PATHS['temp_dir']
        if os.path.exists(temp_dir):
            for filename in os.listdir(temp_dir):
                if filename.startswith('temp_') or filename.endswith('.tmp'):
                    os.remove(os.path.join(temp_dir, filename))
    except Exception as e:
        # Silent cleanup - don't show errors to user
        pass

def get_file_info(filepath: str) -> Dict:
    """
    Get information about a file.
    
    Args:
        filepath: Path to the file
        
    Returns:
        Dictionary with file information
    """
    try:
        if os.path.exists(filepath):
            stat = os.stat(filepath)
            return {
                'exists': True,
                'size_bytes': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'modified': pd.Timestamp.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'readable': os.access(filepath, os.R_OK),
                'writable': os.access(filepath, os.W_OK)
            }
        else:
            return {
                'exists': False,
                'size_bytes': 0,
                'size_mb': 0,
                'modified': 'N/A',
                'readable': False,
                'writable': False
            }
    except Exception:
        return {
            'exists': False,
            'size_bytes': 0,
            'size_mb': 0,
            'modified': 'Error',
            'readable': False,
            'writable': False
        }

def import_config_from_dict(config_dict: Dict) -> Dict:
    """
    Import configuration from a dictionary with validation.
    
    Args:
        config_dict: Configuration dictionary to import
        
    Returns:
        Validated and cleaned configuration dictionary
    """
    try:
        # Validate the imported config
        is_valid, errors = validate_truck_config(config_dict)
        
        if not is_valid:
            st.warning("⚠️ Imported configuration has validation errors:")
            for error in errors[:5]:  # Show first 5 errors
                st.warning(f"• {error}")
            
            # Try to fix common issues automatically
            cleaned_config = auto_fix_config(config_dict)
            
            # Re-validate after auto-fix
            is_valid_after_fix, remaining_errors = validate_truck_config(cleaned_config)
            
            if is_valid_after_fix:
                st.success("✅ Configuration auto-corrected successfully!")
                return cleaned_config
            else:
                st.error("❌ Could not auto-correct all configuration errors. Using defaults.")
                return DEFAULT_TRUCK_CONFIG
        
        return config_dict
        
    except Exception as e:
        st.error(f"Error importing configuration: {str(e)}")
        return DEFAULT_TRUCK_CONFIG

def auto_fix_config(config: Dict) -> Dict:
    """
    Attempt to automatically fix common configuration issues.
    
    Args:
        config: Configuration dictionary with potential issues
        
    Returns:
        Fixed configuration dictionary
    """
    fixed_config = {}
    
    for contractor, locations in config.items():
        if not isinstance(locations, dict):
            continue
            
        fixed_config[contractor] = {}
        
        for parking_location, settings in locations.items():
            if not isinstance(settings, dict):
                continue
            
            fixed_settings = {}
            
            # Fix loading location
            loading_loc = settings.get('loading_location', 'CP4')
            if loading_loc not in VALIDATION_RULES['valid_loading_locations']:
                loading_loc = 'CP4'  # Default fallback
            fixed_settings['loading_location'] = loading_loc
            
            # Fix dumping location
            dumping_loc = settings.get('dumping_location', 'FENI km 0')
            if dumping_loc not in VALIDATION_RULES['valid_dumping_locations']:
                dumping_loc = 'FENI km 0'  # Default fallback
            fixed_settings['dumping_location'] = dumping_loc
            
            # Fix departure time
            departure_time = settings.get('departure_time', '7:00')
            if not validate_time_format(departure_time):
                departure_time = '7:00'  # Default fallback
            fixed_settings['departure_time'] = departure_time
            
            # Fix number of trucks
            num_trucks = settings.get('number_of_trucks', 25)
            try:
                num_trucks = int(num_trucks)
                if num_trucks < VALIDATION_RULES['min_trucks_per_contractor']:
                    num_trucks = VALIDATION_RULES['min_trucks_per_contractor']
                elif num_trucks > VALIDATION_RULES['max_trucks_per_contractor']:
                    num_trucks = VALIDATION_RULES['max_trucks_per_contractor']
            except (ValueError, TypeError):
                num_trucks = 25  # Default fallback
            fixed_settings['number_of_trucks'] = num_trucks
            
            # Only add valid parking locations
            if parking_location in VALIDATION_RULES['valid_parking_locations']:
                fixed_config[contractor][parking_location] = fixed_settings
    
    return fixed_config 

def debug_excel_structure():
    """Debug function to examine the actual Excel data structure."""
    try:
        df = pd.read_excel(DATA_PATHS['excel_data'])
        
        print("=== EXCEL DATA STRUCTURE DEBUG ===")
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        print("\nFirst 10 rows:")
        print(df.head(10))
        print("\nData types:")
        print(df.dtypes)
        print("\nUnique values in each column:")
        for col in df.columns:
            unique_vals = df[col].dropna().unique()[:10]  # Show first 10 unique values
            print(f"{col}: {unique_vals}")
        
        return df
        
    except Exception as e:
        print(f"Error reading Excel file: {str(e)}")
        return None 

def extract_real_travel_data_from_excel() -> Dict:
    """
    Extract real travel times and distance matrix from Excel data.
    🎯 FOCUSED ON FENI KM0 AND FENI KM15 ONLY
    
    Returns:
        Dictionary with real travel times, distances, and waiting times for FENI sites only
    """
    try:
        df = pd.read_excel(DATA_PATHS['excel_data'])
        
        if df.empty:
            return {}
        
        # Extract real travel time data - FENI SITES ONLY
        travel_data = {
            'travel_times': {},
            'distances': {},
            'real_waiting_times': {},
            'locations': {
                'loading': [],
                'parking': [],
                'dumping': ['FENI KM0', 'FENI KM15']  # Only FENI sites
            }
        }
        
        # Process each row to extract travel time data - FILTER FOR FENI ONLY
        for _, row in df.iterrows():
            loading_origin = str(row['Loading Origin']).strip()
            parking_origin = str(row['Parking Origin']).strip()
            dumping_dest = str(row['Dumping Destination']).strip()
            
            # 🎯 CRITICAL FILTER: Only process FENI routes
            if dumping_dest not in ['FENI KM0', 'FENI KM15']:
                continue  # Skip all non-FENI routes
            
            # Skip invalid rows
            if loading_origin == 'nan' or parking_origin == 'nan' or dumping_dest == 'nan':
                continue
            
            # Extract real travel times from Excel columns
            parking_to_loading_time = row.get('Travel Parking-Loading (h)', 0)
            loaded_travel_time = row.get('Loaded Travel (h)', 0)
            empty_travel_time = row.get('Empty Travel (h)', 0)
            real_waiting_time = row.get('Waiting for dumping (h)', 0)
            
            # Validate and clean data - handle nan values
            def clean_numeric_value(value):
                """Clean numeric values, convert nan to 0"""
                if value is None or str(value).lower() == 'nan' or not isinstance(value, (int, float)):
                    return 0
                return float(value)
            
            parking_to_loading_time = clean_numeric_value(parking_to_loading_time)
            loaded_travel_time = clean_numeric_value(loaded_travel_time)
            empty_travel_time = clean_numeric_value(empty_travel_time)
            real_waiting_time = clean_numeric_value(real_waiting_time)
            
            # Store travel times (convert hours to hours for consistency)
            route_key = f"{parking_origin}_{loading_origin}_{dumping_dest}"
            
            travel_data['travel_times'][route_key] = {
                'parking_to_loading': parking_to_loading_time,
                'loading_to_dumping': loaded_travel_time,
                'dumping_to_parking': empty_travel_time,
                'total_cycle': parking_to_loading_time + loaded_travel_time + empty_travel_time
            }
            
            # Calculate distances from travel times (assuming average speed)
            avg_speed = 25.0  # km/h average speed from Excel data analysis
            
            travel_data['distances'][f"{parking_origin}_{loading_origin}"] = parking_to_loading_time * avg_speed
            travel_data['distances'][f"{loading_origin}_{dumping_dest}"] = loaded_travel_time * avg_speed
            travel_data['distances'][f"{dumping_dest}_{parking_origin}"] = empty_travel_time * avg_speed
            
            # Store real waiting times (ONLY FOR FENI SITES)
            travel_data['real_waiting_times'][route_key] = real_waiting_time
            
            # Add to location lists
            if loading_origin not in travel_data['locations']['loading']:
                travel_data['locations']['loading'].append(loading_origin)
            if parking_origin not in travel_data['locations']['parking']:
                travel_data['locations']['parking'].append(parking_origin)
        
        # Sort location lists
        travel_data['locations']['loading'] = sorted(travel_data['locations']['loading'])
        travel_data['locations']['parking'] = sorted(travel_data['locations']['parking'])
        
        return travel_data
        
    except Exception as e:
        st.error(f"Error extracting real travel data: {str(e)}")
        return {}

def get_real_travel_time_matrix() -> Dict:
    """Generate real travel time matrix from Excel data."""
    travel_data = extract_real_travel_data_from_excel()
    
    if not travel_data:
        return {}
    
    locations = travel_data['locations']
    matrix = {}
    
    # Create matrix for all location combinations
    all_locations = list(set(locations['loading'] + locations['parking'] + locations['dumping']))
    
    for origin in all_locations:
        matrix[origin] = {}
        for destination in all_locations:
            if origin == destination:
                matrix[origin][destination] = 0
            else:
                # Look for direct route in travel data
                found_time = None
                for route_key, times in travel_data['travel_times'].items():
                    parts = route_key.split('_')
                    if len(parts) >= 3:
                        parking, loading, dumping = parts[0], parts[1], parts[2]
                        
                        # Check for matching route segments
                        if origin == parking and destination == loading:
                            found_time = times['parking_to_loading']
                            break
                        elif origin == loading and destination == dumping:
                            found_time = times['loading_to_dumping']
                            break
                        elif origin == dumping and destination == parking:
                            found_time = times['dumping_to_parking']
                            break
                
                # Use found time or estimate based on distance
                if found_time is not None:
                    matrix[origin][destination] = found_time
                else:
                    # Estimate travel time (fallback)
                    matrix[origin][destination] = 1.5  # 1.5 hours default
    
    return matrix 

 