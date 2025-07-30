import sys
import os
import pytest
import base64
import io

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_handlers import export_schedule_to_excel, load_config
from core_calculations import optimize_departure_times

@pytest.fixture
def sample_optimized_schedule():
    """Generate a sample optimized schedule for testing."""
    config = load_config()
    loaded_speed = 40
    empty_speed = 60
    optimization_results = optimize_departure_times(config, loaded_speed, empty_speed)
    return optimization_results['schedule']

def test_export_schedule_logic(sample_optimized_schedule):
    """
    Test the core logic of export_schedule_to_excel directly.
    This bypasses the need for a live Streamlit server and API endpoints.
    """
    filename = "test_schedule.xlsx"
    
    # The function returns a base64 encoded string
    b64_excel = export_schedule_to_excel(sample_optimized_schedule, filename)

    # Validate that the output is a valid base64 string
    assert isinstance(b64_excel, str), "Function should return a base64 string"
    
    # Decode the base64 string to check if it's a valid Excel file
    try:
        decoded_excel = base64.b64decode(b64_excel)
        # Check for the magic number for XLSX files (PK\x03\x04)
        assert decoded_excel.startswith(b'PK\x03\x04'), "Decoded file is not a valid XLSX file"
    except Exception as e:
        pytest.fail(f"Failed to decode or validate the exported Excel file: {e}")

    # Further validation could involve using a library like openpyxl to read the in-memory file
    # and check its contents, but for now, we'll just check the file signature.