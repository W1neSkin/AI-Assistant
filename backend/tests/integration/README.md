# Integration Tests

This directory contains integration tests for the backend application. These tests verify that different components of the system work together correctly.

## Test Categories

1. **Authentication Flow** - Tests the complete user journey from registration to accessing protected resources.
2. **Document Management** - Tests the full document lifecycle from upload to deletion.
3. **Question Answering** - Tests the QA functionality with document context.
4. **Settings Management** - Tests that changing settings affects system behavior appropriately.
5. **Service Container** - Tests that all services initialize and work together correctly.

## Running the Tests

To run the integration tests, use the following command from the project root:

```bash
cd backend
python -m pytest tests/integration -v
```

To run a specific test file:

```bash
cd backend
python -m pytest tests/integration/test_auth_flow.py -v
```

## Test Dependencies

The integration tests require:
- A running Redis instance for caching
- Access to the LLM service (either local or cloud)
- SQLite for the test database (created automatically in-memory)

## Notes

- These tests use an in-memory SQLite database for testing, which is created and destroyed for each test session.
- Test data files are created dynamically in the `test_data` directory.
- Some tests may be sensitive to the exact behavior of the LLM service, especially those that verify answer content. 