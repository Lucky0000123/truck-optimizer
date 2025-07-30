import requests

BASE_URL = "http://localhost:8501"
TIMEOUT = 30
HEADERS = {"Content-Type": "application/json"}


def test_optimize_shifts_api_should_perform_automatic_shift_start_optimization():
    url = f"{BASE_URL}/optimize_shifts"

    # Valid payload example
    valid_payload = {
        "weights": {
            "dump_wait": 0.7,
            "load_wait": 0.3
        },
        "current_offsets": {
            "contractor_1": 5,
            "contractor_2": 10,
            "contractor_3": 0
        }
    }

    # Invalid payload example (missing weights)
    invalid_payload = {
        "current_offsets": {
            "contractor_1": 5,
            "contractor_2": 10
        }
    }

    # Test valid request
    try:
        response = requests.post(url, json=valid_payload, headers=HEADERS, timeout=TIMEOUT)
        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
        json_data = response.json()
        assert isinstance(json_data, dict), "Response JSON should be a dictionary"
        # Check that recommended offsets are returned and are dict with numeric values
        assert "recommended_offsets" in json_data, "Response missing 'recommended_offsets'"
        recommended_offsets = json_data["recommended_offsets"]
        assert isinstance(recommended_offsets, dict), "'recommended_offsets' should be a dictionary"
        for k, v in recommended_offsets.items():
            assert isinstance(v, (int, float)), f"Offset value for {k} should be numeric"
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"

    # Test invalid request
    try:
        response = requests.post(url, json=invalid_payload, headers=HEADERS, timeout=TIMEOUT)
        assert response.status_code == 400, f"Expected 400 Bad Request, got {response.status_code}"
        # Optionally check error message in response
        try:
            error_json = response.json()
            assert "error" in error_json or "message" in error_json, "Error response should contain 'error' or 'message'"
        except Exception:
            # If response is not JSON, pass as long as status code is 400
            pass
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"


test_optimize_shifts_api_should_perform_automatic_shift_start_optimization()