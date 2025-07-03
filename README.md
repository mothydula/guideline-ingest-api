# Guideline Ingest API

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Minimal backend API processing guideline documents through two-step GPT chains (summarize → checklist). Returns event_id in <200ms with async Celery processing.
🚀 **Setup**: `docker compose up --build`

## 🏗️ Design Choices

**Fast Response Architecture**: Jobs return immediately (<200ms) by queuing to Redis while Celery workers handle AI processing asynchronously. Satisfies speed requirements for complex operations.
**Two-Step GPT Chain**: Separate summarization and checklist generation provides focused, higher-quality outputs than single prompts. Each step uses specialized prompts for better results.
**Django + DRF**: Rapid development with built-in ORM, auto-generated OpenAPI docs, and robust serialization patterns. DRF provides excellent API validation and error handling.
**PostgreSQL + Redis**: PostgreSQL for reliable job persistence and complex queries; Redis for high-performance message queuing and result caching.
**Docker Compose**: One-command deployment with proper service orchestration, health checks, and environment isolation.
**Error Handling**: Comprehensive retry logic, graceful OpenAI API failures, and production-ready logging ensure reliability.

## 🤖 AI-Assisted Development with GitHub Copilot

GitHub Copilot significantly accelerated development and improved code quality:
**Code Generation**: Copilot generated Django REST framework boilerplate, including serializers, views, and URL patterns. Auto-completed Celery task structures and OpenAI API integration patterns based on best practices.
**Architecture Suggestions**: When typing function signatures and comments, Copilot suggested the async job queue pattern for meeting <200ms requirements, recommending Redis for message queuing and proper error handling flows.
**Database Models**: Copilot generated Django model fields and relationships, suggesting UUIDField for job IDs, JSONField for checklist storage, and appropriate database indexes for performance.
**Testing Code**: Copilot auto-generated comprehensive test cases (~70% coverage) including API endpoint tests, model validation, and edge cases. Suggested mocking patterns for external OpenAI API calls.
**Configuration Management**: Copilot generated Docker Compose configurations, environment variable handling, and settings patterns following Django best practices for production deployment.
**Error Handling**: When writing try-catch blocks, Copilot suggested comprehensive exception handling for OpenAI API failures, Celery task retries, and graceful degradation patterns.
**Documentation**: Copilot generated OpenAPI schema configurations and API documentation comments, creating detailed request/response examples automatically.
**Debugging Assistance**: Copilot suggested logging patterns and debugging approaches when troubleshooting Celery worker issues and OpenAI integration problems.
**Result**: GitHub Copilot enabled building production-quality code with proper patterns and comprehensive error handling in the 2-4 hour timeframe.

## 🚀 Usage

```bash
cp .env.example .env  # Add OPENAI_API_KEY
docker compose up --build
```

## 🧪 Testing

```bash
# Run all tests
docker-compose exec web python manage.py test

# Install coverage first
docker-compose exec web pip install coverage

# Run tests with coverage
docker-compose exec web coverage run --source='.' manage.py test

# Show coverage report
docker-compose exec web coverage report

# Show detailed coverage with missing lines
docker-compose exec web coverage report --show-missing
```
