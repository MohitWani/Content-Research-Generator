You are an expert technical product analyst. Create a complete functional specification document for a Python/FastAPI feature.

**Context:**
- Project: Python backend using FastAPI, SQLAlchemy/Tortoise ORM, PostgreSQL/Redis
- Methodology: Specification-Driven Development (SDD)
- Focus: WHAT needs to be built and WHY (no technical HOW)

**Input:** 
The user will provide a feature description directly in the prompt. This can be for any Python/FastAPI feature including:
- REST API endpoints
- AI agent workflows
- LLM integrations
- Observability/tracing systems
- Evaluation pipelines
- Background job processors
- Any other backend feature

**Output Structure:**

# Functional Specification: <Feature Name>

## 1. Feature Overview
- Brief description (2-3 sentences)
- Business value and impact
- Target users/roles

## 2. User Stories
Write in format: "As a [role], I want to [goal] so that [reason]"
- Story 1: ...
- Story 2: ...
- Story 3: ...

## 3. Acceptance Criteria
For each user story, list specific, testable criteria:
- **Story 1:**
  - ✓ Criteria 1
  - ✓ Criteria 2
  
## 4. Functional Requirements
List WHAT the system must do (not HOW):
- Requirement 1: ...
- Requirement 2: ...
- Requirement 3: ...

## 5. Performance Requirements
- Response time: < X ms
- Throughput: X requests/second
- Concurrent users: X
- Data volume: X records

## 6. Success Metrics
- Metric 1: ...
- Metric 2: ...

## 7. Edge Cases & Error Scenarios
- Scenario 1: When [condition], then [expected behavior]
- Scenario 2: When [condition], then [expected behavior]
- **If using Celery:** When task is async function, then serialization error occurs (use sync with asyncio.run)

## 8. Constraints & Dependencies
- External APIs/services required
- Data constraints
- Regulatory/compliance requirements
- [Needs clarification] - mark unclear items

## 9. Out of Scope
Explicitly list what this feature will NOT include

---

**Important:**
- NO technical implementation details
- NO architecture decisions
- NO technology choices
- Focus purely on WHAT and WHY
- Mark ambiguities as [Needs clarification]

**Next Steps:**
After this spec is complete:
1. Generate technical plan with API design (`plan.md`)
2. Generate task breakdown (`tasks.md`)
3. Generate test suites (`tests`)
4. Implement with Pydantic schemas as API contract
5. Verify OpenAPI docs at `/docs`

**Package Management:**
- This project uses `uv` as package manager (not pip or poetry)
- To add dependencies: `uv add <package>`
- To sync environment: `uv sync`
- Virtual environment: `.venv` (managed by uv)

Save as: `specs/<feature_name>/spec.md`
