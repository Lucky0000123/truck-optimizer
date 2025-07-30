import requests
import io

def test_data_upload_endpoint():
    base_url = "http://localhost:8501"
    url = f"{base_url}/data_upload"
    headers = {}
    timeout = 30

    # Prepare a minimal valid Excel file in memory for upload
    # Since we cannot create a real Excel file without external libraries,
    # we will use a minimal valid XLSX file binary content placeholder.
    # For demonstration, we create a minimal valid XLSX file binary using openpyxl.
    try:
        import openpyxl
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.title = "Sheet1"
        ws.append(["Contractor", "CycleTime", "StartTime"])
        ws.append(["ContractorA", 120, "08:00"])
        excel_buffer = io.BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)
        valid_file = ("Time_Data.xlsx", excel_buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except ImportError:
        # If openpyxl is not installed, skip valid file test
        valid_file = None

    # Test valid file upload
    if valid_file:
        files = {"file": valid_file}
        try:
            response = requests.post(url, files=files, headers=headers, timeout=timeout)
            assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"
            json_resp = response.json()
            assert "success" in json_resp.get("message", "").lower() or "uploaded" in json_resp.get("message", "").lower(), \
                "Response message does not indicate success"
        except requests.RequestException as e:
            assert False, f"Request failed: {e}"
        finally:
            excel_buffer.close()

    # Test invalid file upload (e.g., text file with wrong content type)
    invalid_content = io.BytesIO(b"This is not an Excel file")
    files = {"file": ("invalid.txt", invalid_content, "text/plain")}
    try:
        response = requests.post(url, files=files, headers=headers, timeout=timeout)
        # Expecting a 4xx error or a 200 with error message depending on API design
        if response.status_code == 200:
            json_resp = response.json()
            assert "error" in json_resp.get("message", "").lower() or "invalid" in json_resp.get("message", "").lower(), \
                "Response should indicate error for invalid file"
        else:
            assert 400 <= response.status_code < 500, f"Expected client error status code, got {response.status_code}"
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"
    finally:
        invalid_content.close()

test_data_upload_endpoint()