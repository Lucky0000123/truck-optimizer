import requests

def test_get_kpis_api_should_return_real_time_kpi_metrics():
    base_url = "http://localhost:8501"
    endpoint = "/get_kpis"
    url = base_url + endpoint
    headers = {
        "Accept": "application/json"
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        assert False, f"Request to {url} failed: {e}"

    assert response.status_code == 200, f"Expected status code 200 but got {response.status_code}"

    content_type = response.headers.get('Content-Type', '')
    assert 'application/json' in content_type.lower(), f"Expected 'application/json' content type but got '{content_type}'"

    try:
        data = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"

    # Validate presence of expected KPI fields
    expected_fields = [
        "average_dump_wait",
        "average_load_wait",
        "trips_per_shift",
        "utilization_metrics"
    ]
    for field in expected_fields:
        assert field in data, f"Missing expected KPI field '{field}' in response JSON"

test_get_kpis_api_should_return_real_time_kpi_metrics()
