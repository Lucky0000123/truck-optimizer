import sys
import os
import pytest

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core_calculations import optimize_departure_times
from data_handlers import load_config

@pytest.fixture
def sample_config():
    """Load sample truck configuration for testing."""
    return load_config()

def test_optimize_offsets_logic(sample_config):
    """
    Test the core logic of optimize_departure_times directly.
    This bypasses the need for a live Streamlit server and API endpoints.
    """
    loaded_speed = 40
    empty_speed = 60

    optimization_results = optimize_departure_times(
        sample_config, loaded_speed, empty_speed
    )

    # Validate the structure of the returned results
    assert isinstance(optimization_results, dict), "Optimization results should be a dictionary"
    assert 'schedule' in optimization_results, "Results should contain a 'schedule' key"
    assert 'stats' in optimization_results, "Results should contain a 'stats' key"
    
    # Validate the schedule format
    schedule = optimization_results['schedule']
    assert isinstance(schedule, dict), "Schedule should be a dictionary"
    
    # Validate the stats format
    stats = optimization_results['stats']
    assert isinstance(stats, dict), "Stats should be a dictionary"
    assert 'baseline_wait' in stats, "Stats should contain 'baseline_wait'"
    assert 'optimized_wait' in stats, "Stats should contain 'optimized_wait'"
    
    # Add a basic sanity check for non-negative wait times
    assert stats['baseline_wait'] >= 0, "Baseline wait time should be non-negative"
    assert stats['optimized_wait'] >= 0, "Optimized wait time should be non-negative"
    
    # Check that optimization improves or maintains the wait time
    assert stats['optimized_wait'] <= stats['baseline_wait'], "Optimized wait time should be less than or equal to baseline"