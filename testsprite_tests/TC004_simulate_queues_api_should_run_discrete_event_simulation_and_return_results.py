import requests

BASE_URL = "http://localhost:8501"
TIMEOUT = 30
HEADERS = {"Content-Type": "application/json"}


def test_simulate_queues_api_should_run_discrete_event_simulation_and_return_results():
    # Valid payload example based on "current contractor schedule offsets and timing details"
    valid_schedule_payload = {
        "schedule": {
            "contractors": [
                {
                    "id": "contractor_1",
                    "shift_start_offset": 15,
                    "timing_details": {
                        "arrival_time": "08:00",
                        "departure_time": "16:00"
                    }
                },
                {
                    "id": "contractor_2",
                    "shift_start_offset": 30,
                    "timing_details": {
                        "arrival_time": "09:00",
                        "departure_time": "17:00"
                    }
                }
            ]
        }
    }

    # Invalid payload example (missing required fields)
    invalid_schedule_payload = {
        "schedule": {
            "contractors": [
                {
                    "id": "contractor_1"
                    # missing shift_start_offset and timing_details
                }
            ]
        }
    }

    url = f"{BASE_URL}/simulate_queues"

    # Test valid request
    try:
        response = requests.post(url, json=valid_schedule_payload, headers=HEADERS, timeout=TIMEOUT)
        assert response.status_code == 200, f"Expected 200 but got {response.status_code}"
        json_data = response.json()
        # Validate expected keys in response
        assert "queue_wait_times" in json_data, "Missing 'queue_wait_times' in response"
        assert "service_rates" in json_data, "Missing 'service_rates' in response"
        # Additional sanity checks on returned data types
        assert isinstance(json_data["queue_wait_times"], dict), "'queue_wait_times' should be a dict"
        assert isinstance(json_data["service_rates"], dict), "'service_rates' should be a dict"
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"
    except ValueError:
        assert False, "Response is not valid JSON"

    # Test invalid request
    try:
        response = requests.post(url, json=invalid_schedule_payload, headers=HEADERS, timeout=TIMEOUT)
        assert response.status_code == 400, f"Expected 400 but got {response.status_code}"
        # Optionally check error message presence
        try:
            error_json = response.json()
            assert "error" in error_json or "message" in error_json, "Expected error message in response"
        except ValueError:
            # If no JSON error message, still accept 400 status as valid error handling
            pass
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"


test_simulate_queues_api_should_run_discrete_event_simulation_and_return_results()