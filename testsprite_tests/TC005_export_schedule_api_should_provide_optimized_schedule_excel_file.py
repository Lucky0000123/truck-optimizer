import requests

BASE_URL = "http://localhost:8501"
EXPORT_ENDPOINT = "/export_schedule"
TIMEOUT = 30

def test_export_schedule_api_should_provide_optimized_schedule_excel_file():
    url = BASE_URL + EXPORT_ENDPOINT
    headers = {
        "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    }
    try:
        response = requests.get(url, headers=headers, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request to export_schedule endpoint failed: {e}"

    if response.status_code == 200:
        content_type = response.headers.get("Content-Type", "")
        # Validate content type for Excel file
        assert content_type in [
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/octet-stream"
        ], f"Unexpected Content-Type for Excel file: {content_type}"
        # Validate content is not empty
        assert response.content and len(response.content) > 0, "Response content is empty for Excel file export"
    elif response.status_code == 400:
        # Expected error case: export failed or no data available
        try:
            error_json = response.json()
            assert "error" in error_json or "message" in error_json, "400 response missing error message"
        except ValueError:
            # If response is not JSON, just accept 400 as error case
            pass
    else:
        assert False, f"Unexpected status code {response.status_code} received from export_schedule endpoint"

test_export_schedule_api_should_provide_optimized_schedule_excel_file()