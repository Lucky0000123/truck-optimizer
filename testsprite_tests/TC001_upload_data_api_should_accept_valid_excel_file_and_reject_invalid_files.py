import requests
from io import BytesIO

BASE_URL = "http://localhost:8501"
UPLOAD_ENDPOINT = f"{BASE_URL}/upload_data"
TIMEOUT = 30

def test_upload_data_api_should_accept_valid_excel_file_and_reject_invalid_files():
    # Prepare a minimal valid Excel file content (xlsx) in memory
    # Since we cannot create a real Excel file here, we use a known minimal valid XLSX binary header
    # For a real test, replace this with an actual valid Excel file read from disk or generated dynamically
    valid_xlsx_content = (
        b"PK\x03\x04\x14\x00\x06\x00\x08\x00\x00\x00!\x00\xad\x8f\x9f"
        b"\x4f\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x13\x00"
        b"\x00\x00[Content_Types].xml"
    )
    valid_file = ('valid_data.xlsx', BytesIO(valid_xlsx_content), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    # Prepare invalid file contents (e.g., a text file and a corrupted xlsx)
    invalid_text_content = b"This is not an Excel file."
    invalid_text_file = ('invalid_data.txt', BytesIO(invalid_text_content), 'text/plain')

    corrupted_xlsx_content = b"PK\x03\x04\x14\x00\x06\x00\x08\x00\x00\x00corruptedcontent"
    corrupted_xlsx_file = ('corrupted_data.xlsx', BytesIO(corrupted_xlsx_content), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    # Test valid Excel file upload
    try:
        response = requests.post(
            UPLOAD_ENDPOINT,
            files={'file': valid_file},
            timeout=TIMEOUT
        )
        assert response.status_code == 200, f"Expected 200 OK for valid file, got {response.status_code}"
        # Optionally check success message in response content
        json_resp = response.json()
        assert 'success' in json_resp.get('message', '').lower() or 'uploaded' in json_resp.get('message', '').lower(), "Success message not found in response for valid file upload"
    except requests.RequestException as e:
        assert False, f"Request failed for valid file upload: {e}"

    # Test invalid text file upload
    try:
        response = requests.post(
            UPLOAD_ENDPOINT,
            files={'file': invalid_text_file},
            timeout=TIMEOUT
        )
        assert response.status_code == 400, f"Expected 400 Bad Request for invalid text file, got {response.status_code}"
        json_resp = response.json()
        assert 'error' in json_resp.get('message', '').lower() or 'invalid' in json_resp.get('message', '').lower(), "Error message not found in response for invalid text file upload"
    except requests.RequestException as e:
        assert False, f"Request failed for invalid text file upload: {e}"

    # Test corrupted Excel file upload
    try:
        response = requests.post(
            UPLOAD_ENDPOINT,
            files={'file': corrupted_xlsx_file},
            timeout=TIMEOUT
        )
        assert response.status_code == 400, f"Expected 400 Bad Request for corrupted Excel file, got {response.status_code}"
        json_resp = response.json()
        assert 'error' in json_resp.get('message', '').lower() or 'invalid' in json_resp.get('message', '').lower(), "Error message not found in response for corrupted Excel file upload"
    except requests.RequestException as e:
        assert False, f"Request failed for corrupted Excel file upload: {e}"

test_upload_data_api_should_accept_valid_excel_file_and_reject_invalid_files()
