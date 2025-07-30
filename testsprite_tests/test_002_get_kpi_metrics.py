import sys
import os
import pytest

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import get_standardized_dump_site_metrics
from data_handlers import load_config

@pytest.fixture
def sample_config():
    """Load sample truck configuration for testing."""
    return load_config()

def test_get_kpi_metrics_logic(sample_config):
    """
    Test the core logic of get_standardized_dump_site_metrics directly.
    This bypasses the need for a live Streamlit server and API endpoints.
    """
    loaded_speed = 40
    empty_speed = 60

    main_feni_metrics, avg_main_feni_waits = get_standardized_dump_site_metrics(
        sample_config, loaded_speed, empty_speed
    )

    # Validate the structure of the returned metrics
    assert isinstance(main_feni_metrics, dict), "main_feni_metrics should be a dictionary"
    assert isinstance(avg_main_feni_waits, dict), "avg_main_feni_waits should be a dictionary"
    
    # Ensure both FENI sites are present
    assert 'FENI KM 0' in main_feni_metrics
    assert 'FENI KM 15' in main_feni_metrics
    assert 'FENI KM 0' in avg_main_feni_waits
    assert 'FENI KM 15' in avg_main_feni_waits

    # Validate that the calculated values are numeric
    for site, metrics in main_feni_metrics.items():
        assert isinstance(metrics['total_wait_time'], (int, float))
        assert isinstance(metrics['route_count'], int)
        assert isinstance(metrics['trucks_affected'], int)

    for site, avg_wait in avg_main_feni_waits.items():
        assert isinstance(avg_wait, (int, float))

    # Add a basic sanity check for non-negative wait times
    for site, avg_wait in avg_main_feni_waits.items():
        assert avg_wait >= 0, f"Average wait time for {site} should be non-negative"