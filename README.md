# Sleep Data Microservice

A Python-based microservice for tracking, analyzing, and visualizing sleep data, built with FastAPI, SQLAlchemy, and PostgreSQL.

## Features

- Track sleep metrics including duration, quality, heart rate, and sleep phases
- Import sleep data from Apple Health exports
- Generate synthetic sleep data for testing and development
- Analyze sleep patterns to provide insights and recommendations
- RESTful API for easy integration with other systems
- PostgreSQL database for reliable data storage

## Architecture

This microservice follows a clean architecture with separation of concerns:

- **API Layer**: FastAPI endpoints for data access and manipulation
- **Service Layer**: Business logic for sleep data processing and analysis
- **Storage Layer**: Database abstraction with support for PostgreSQL and SQLite
- **Models**: Pydantic models for request/response validation and documentation

## Requirements

- Python 3.9+
- PostgreSQL (for production) or SQLite (for development/testing)
- Dependencies listed in `requirements.txt`

## Setup

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/sleep-data-microservice.git
   cd sleep-data-microservice
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit the `.env` file to set your database connection and other settings.

4. Run database migrations:
   ```bash
   alembic upgrade head
   ```

5. Start the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

### Using Docker

For a containerized setup:

```bash
docker-compose up -d
```

This will start:
- The sleep data microservice on port 8001
- PostgreSQL database on port 5432
- PgAdmin for database management on port 5050

## API Endpoints

Once the service is running, API documentation is available at:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/sleep/data` | Get sleep records for a user |
| POST | `/api/sleep/records` | Create a new sleep record |
| PUT | `/api/sleep/records/{record_id}` | Update a sleep record |
| DELETE | `/api/sleep/records/{record_id}` | Delete a sleep record |
| GET | `/api/sleep/users` | List all users with their record counts |
| POST | `/api/sleep/import/apple_health` | Import sleep data from Apple Health |
| POST | `/api/sleep/generate` | Generate synthetic sleep data |
| GET | `/api/sleep/analytics` | Analyze sleep patterns and trends |

## Testing

Run the included test suite:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app tests/

# Quick setup and test
./setup_and_test.sh
```

## Database Migrations

This project uses Alembic for database migrations:

```bash
# Create a new migration after changing models
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Revert migrations
alembic downgrade -1
```

## Project Structure

```
sleep-data-microservice/
├── app/
│   ├── api/             # API routes
│   ├── config/          # Configuration settings
│   ├── models/          # Data models
│   ├── services/        # Business logic
│   │   ├── analytics/   # Sleep data analysis
│   │   ├── extern/      # External integrations
│   │   └── storage/     # Database interactions
│   └── main.py          # Application entry point
├── migrations/          # Database migrations
├── tests/               # Test suite
├── .env.example         # Environment variable template
├── docker-compose.yml   # Docker configuration
├── Dockerfile           # Docker build instructions
└── requirements.txt     # Python dependencies
```

## Development Guidelines

- Code is formatted using Black and checked with Flake8
- Pre-commit hooks are configured to ensure code quality
- CI pipeline runs tests and linting checks on pull requests

## License

[Apache 2.0](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
