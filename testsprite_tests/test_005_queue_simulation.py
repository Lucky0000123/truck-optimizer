import sys
import os
import pytest
import pandas as pd

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core_calculations import generate_timeline_data
from data_handlers import load_config

@pytest.fixture
def sample_config():
    """Load sample truck configuration for testing."""
    return load_config()

def test_queue_simulation_logic(sample_config):
    """
    Test the core logic of generate_timeline_data directly.
    This bypasses the need for a live Streamlit server and API endpoints.
    """
    loaded_speed = 40
    empty_speed = 60

    gantt_df, wait_df = generate_timeline_data(
        sample_config, loaded_speed, empty_speed
    )

    # Validate the structure of the returned dataframes
    assert isinstance(gantt_df, pd.DataFrame), "gantt_df should be a pandas DataFrame"
    assert isinstance(wait_df, pd.DataFrame), "wait_df should be a pandas DataFrame"
    
    # Check that the gantt_df is not empty
    assert not gantt_df.empty, "Gantt DataFrame should not be empty"
    
    # Check for required columns in gantt_df
    required_gantt_columns = ['Fleet', 'Start', 'Finish', 'Activity']
    for col in required_gantt_columns:
        assert col in gantt_df.columns, f"Gantt DataFrame missing required column: {col}"
        
    # Check for required columns in wait_df
    required_wait_columns = ['Hour', 'Site', 'Wait Time (Minutes)']
    for col in required_wait_columns:
        assert col in wait_df.columns, f"Wait DataFrame missing required column: {col}"

    # Add a basic sanity check for non-negative wait times
    assert (wait_df['Wait Time (Minutes)'] >= 0).all(), "Wait times should be non-negative" 