# TestSprite AI Testing Report(MCP)

-- -

## 1️⃣ Document Metadata
- **Project Name:** DUMP OPTIMISER
- **Version:** N/A
- **Date:** 2025-07-26
- **Prepared by:** TestSprite AI Team

-- -

## 2️⃣ Requirement Validation Summary

### Requirement: API Endpoint Validation
- **Description:** This requirement covers the validation of the main API endpoints for data upload, KPI metrics, optimization, and data export.

#### Test 1
- **Test ID:** TC001
- **Test Name:** test_data_upload_endpoint
- **Test Code:** [TC001_test_data_upload_endpoint.py](./TC001_test_data_upload_endpoint.py)
- **Test Error:** N/A
- **Test Visualization and Result:** [View Test Details](https://www.testsprite.com/dashboard/mcp/tests/4691da8c-0cb7-4366-ae2c-d3f057534f36/c4d55819-849d-4e16-aaa8-44051b1b9d4b)
- **Status:** ✅ Passed
- **Severity:** Low
- **Analysis / Findings:** The `data_upload` POST endpoint correctly accepts and processes Excel .xlsx files, handling both valid and invalid inputs as expected.

-- -

#### Test 2
- **Test ID:** TC002
- **Test Name:** test_get_kpi_metrics_endpoint
- **Test Code:** [TC002_test_get_kpi_metrics_endpoint.py](./TC002_test_get_kpi_metrics_endpoint.py)
- **Test Error:** `requests.exceptions.JSONDecodeError: Expecting value: line 1 column 1 (char 0)`
- **Test Visualization and Result:** [View Test Details](https://www.testsprite.com/dashboard/mcp/tests/4691da8c-0cb7-4366-ae2c-d3f057534f36/603deb7c-b315-441d-bae2-2118751bbc5f)
- **Status:** ❌ Failed
- **Severity:** High
- **Analysis / Findings:** The test failed due to the response from the `get_kpi_metrics` GET endpoint not returning a valid JSON payload. This suggests the backend service might be returning an empty body or invalid content type when KPI metrics are requested.

-- -

#### Test 3
- **Test ID:** TC003
- **Test Name:** test_optimize_offsets_endpoint
- **Test Code:** [TC003_test_optimize_offsets_endpoint.py](./TC003_test_optimize_offsets_endpoint.py)
- **Test Error:** `requests.exceptions.HTTPError: 403 Client Error: Forbidden for url: http://localhost:8501/optimize_offsets`
- **Test Visualization and Result:** [View Test Details](https://www.testsprite.com/dashboard/mcp/tests/4691da8c-0cb7-4366-ae2c-d3f057534f36/749f185c-ec8c-404e-9eae-cd1f3d74472f)
- **Status:** ❌ Failed
- **Severity:** High
- **Analysis / Findings:** The test failed due to a 403 Forbidden HTTP error when accessing the `optimize_offsets` POST endpoint. This indicates an authorization or permission misconfiguration in the backend service preventing the auto-optimization algorithm from being triggered.

-- -

#### Test 4
- **Test ID:** TC004
- **Test Name:** test_export_schedule_endpoint
- **Test Code:** [TC004_test_export_schedule_endpoint.py](./TC004_test_export_schedule_endpoint.py)
- **Test Error:** `AssertionError: Unexpected Content-Type: text/html`
- **Test Visualization and Result:** [View Test Details](https://www.testsprite.com/dashboard/mcp/tests/4691da8c-0cb7-4366-ae2c-d3f057534f36/66bb1475-6ead-4b88-a69d-dd5147279fd3)
- **Status:** ❌ Failed
- **Severity:** High
- **Analysis / Findings:** The test failed because the `export_schedule` GET endpoint returned an unexpected Content-Type 'text/html' instead of an Excel file. This likely indicates that an error page or invalid response was served instead of the expected schedule export file.

-- -

## 3️⃣ Coverage & Matching Metrics

- **100%** of product requirements tested
- **25%** of tests passed
- **Key gaps / risks:**
    - The KPI metrics endpoint is not returning valid JSON.
    - The optimization endpoint is inaccessible due to a permissions issue.
    - The schedule export endpoint is returning an HTML page instead of an Excel file.

| Requirement             | Total Tests | ✅ Passed | ⚠️ Partial | ❌ Failed |
|-------------------------|-------------|-----------|-------------|------------|
| API Endpoint Validation | 4           | 1         | 0           | 3          | 