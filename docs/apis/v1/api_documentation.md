# AI Services API Documentation

## Overview

The AI Services API Server provides a comprehensive suite of AI-powered services designed to enable seamless integration of AI capabilities into various applications. This server acts as the central gateway for accessing multiple AI analysis services including file analysis, e-commerce compliance checking, cybersecurity incident analysis, and weekly report generation.

**Base URL:** `https://your-api-domain.com`  
**Version:** 1.0.0  
**API Versions:** `/api/`, `/api/v1/`, `/latest/api/`

---

## Authentication

> **Note:** Authentication details are not specified in the current API specification. Please contact your API administrator for authentication requirements.

---

## Endpoints

### Health Check

#### GET `api/health/ai-service`

Check the health status of the API server.

**Response:**
- **200 OK**: Service is healthy
- **Content-Type**: `application/json`

**Example Request:**
```bash
curl -X GET "https://your-api-domain.com/api/health/ai-service"
```

---

### File Analysis

#### POST `/api/analyze/`

Analyze uploaded files using AI-powered analysis capabilities.

**Request Body:**
- **Content-Type**: `multipart/form-data`
- **Required Fields:**
  - `files`: Array of binary files to analyze
  - `file_metadata`: Array of strings containing metadata for each file
- **Optional Fields:**
  - `keywords`: String containing relevant keywords for analysis

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| files | File[] | Yes | Array of files to analyze |
| file_metadata | string[] | Yes | Metadata for each corresponding file |
| keywords | string | No | Keywords to guide the analysis |

**Response:**
- **200 OK**: Analysis completed successfully
- **422 Unprocessable Entity**: Validation error

**Example Request:**
```bash
curl -X POST "https://your-api-domain.com/api/analyze/" \
  -F "files=@document1.pdf" \
  -F "files=@document2.docx" \
  -F 'file_metadata=[{"document_id": 100072, "guid": "test_doc-72"}]' \
  -F 'file_metadata=[{"document_id": 100072, "guid": "test_doc-72"}]' \
  -F "keywords=compliance,security"
```

---

### Retrieve Analysis Results

#### GET `/api/responses/{document_id}`

Retrieve the analysis results for a specific document.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| document_id | integer | Yes | Unique identifier for the analyzed document |

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| guid | string | No | Optional GUID for additional identification |

**Response:**
- **200 OK**: Results retrieved successfully
- **422 Unprocessable Entity**: Validation error

**Example Request:**
```bash
curl -X GET "https://your-api-domain.com/api/responses/123?guid=abc-def-ghi"
```

---

### E-commerce Compliance Analysis

#### POST `/api/ecomm/analyze/`

Analyze email content and/or text for e-commerce compliance issues.

**Request Body:**
- **Content-Type**: `multipart/form-data`
- **Optional Fields:**
  - `file`: Binary file containing email or content to analyze
  - `text`: Raw text content for analysis
  - `keywords`: Keywords to focus the compliance analysis

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file | File | No | Email file or document to analyze |
| text | string | No | Raw text content for analysis |
| keywords | string | No | Keywords for compliance checking |

> **Note:** Either `file` or `text` should be provided for analysis.

**Response:**
- **200 OK**: Compliance analysis completed
- **422 Unprocessable Entity**: Validation error

**Example Request:**
```bash
# Analyze file
curl -X POST "https://your-api-domain.com/api/ecomm/analyze/" \
  -F "file=@email.eml" \
  -F "keywords=gdpr,privacy"

# Analyze text
curl -X POST "https://your-api-domain.com/api/ecomm/analyze/" \
  -F "text=Your email content here..." \
  -F "keywords=compliance,terms"
```

---

### Cybersecurity Incident Analysis

#### POST `/api/cyber/analyze/`

Analyze cybersecurity incident data for compliance issues and security assessment.

**Request Body:**
- **Content-Type**: `application/json`
- **Required Fields:**
  - `text`: JSON object containing incident data
- **Optional Fields:**
  - `rules`: Array of strings specifying rules to check during analysis

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| text | object | Yes | Incident data in JSON format |
| rules | string[] | No | Specific rules to apply during analysis |

**Response:**
- **200 OK**: Cyber security analysis completed
- **422 Unprocessable Entity**: Validation error

**Example Request:**
Payload at location: `python-fast-api-seeds\python-fast-api-seeds\tests\resources\cyber_payload.json` 
```bash
curl -X POST "https://your-api-domain.com/api/cyber/analyze/" \
  -H "Content-Type: application/json" \
  -d '{
    "text": {
      "incident_id": "INC-2024-001",
      "severity": "high",
      "description": "Unauthorized access detected",
      "timestamp": "2024-01-15T10:30:00Z"
    },
    "rules": ["data_breach", "access_control", "incident_response"]
  }'
```

---

### Weekly Summary Report Generation

#### POST `/api/weekly-summary-report/`

Generate a comprehensive weekly summary report from modules data.

**Request Body:**
- **Content-Type**: `application/json`
- **Required Fields:**
  - `modules_data`: JSON object containing data from various modules

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| modules_data | object | Yes | Data from various modules in JSON format |

**Response:**
- **200 OK**: Weekly summary report generated successfully
- **422 Unprocessable Entity**: Validation error

**Example Request:**
Payload at location: `python-fast-api-seeds\python-fast-api-seeds\tests\resources\WSR_Input_data.json` 

```bash
curl -X POST "https://your-api-domain.com/api/weekly-summary-report/" \
  -H "Content-Type: application/json" \
  -d '{
    "modules_data": {
      "analytics": {
        "total_requests": 1500,
        "success_rate": 98.5
      },
      "compliance": {
        "issues_found": 12,
        "resolved": 10
      },
      "security": {
        "incidents": 3,
        "severity_breakdown": {
          "high": 1,
          "medium": 2,
          "low": 0
        }
      }
    }
  }'
```

---

## API Versioning

The API supports multiple versions to ensure backward compatibility:

- **Current Version**: `/api/` - Latest stable version
- **Version 1**: `/api/v1/` - Explicitly versioned endpoints
- **Latest**: `/latest/api/` - Bleeding edge features

All endpoints are available across all versions with identical functionality.

---

## Error Handling

### Standard HTTP Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success - Request completed successfully |
| 422 | Unprocessable Entity - Validation error in request |

### Error Response Format

```json
{
  "detail": [
    {
      "loc": ["field_name"],
      "msg": "Error message description",
      "type": "error_type"
    }
  ]
}
```

### Common Error Scenarios

1. **Missing Required Fields**: Ensure all required parameters are provided
2. **Invalid File Format**: Check that uploaded files are in supported formats
3. **Malformed JSON**: Verify JSON syntax in request bodies
4. **Invalid Document ID**: Ensure the document ID exists and is accessible

---

## Rate Limiting

> **Note:** Rate limiting details are not specified in the current API specification. Please contact your API administrator for rate limiting policies.

---

## Best Practices

### File Upload Guidelines

1. **File Size**: Keep file sizes reasonable for optimal processing
2. **Supported Formats**: Ensure files are in supported formats (PDF, DOCX, TXT, etc.)
3. **Metadata**: Provide descriptive metadata for better analysis results
4. **Keywords**: Use relevant keywords to improve analysis accuracy

### API Usage Tips

1. **Health Checks**: Regularly check API health before making requests
2. **Error Handling**: Implement proper error handling for all API calls
3. **Async Processing**: For large files, consider implementing polling for results
4. **Version Management**: Use explicit versioning for production applications

---

## Support and Resources

For additional support, API access, or technical questions:

- **Documentation**: Keep this document updated with your latest API changes
- **Issues**: Report bugs and feature requests through your issue tracking system
- **Contact**: Reach out to your API development team for assistance

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-01 | Initial API release |

---

*This documentation was generated from the OpenAPI 3.1.0 specification. Last updated: 2024-01-01*