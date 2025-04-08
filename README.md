# Sleep Data Microservice

A Python-based microservice for tracking, analyzing, and importing sleep data.

## Features

- Track sleep metrics including duration, quality, heart rate, and sleep phases
- Import sleep data from Apple Health
- Generate synthetic sleep data for testing and development
- Analyze sleep patterns to identify trends and provide recommendations
- RESTful API for easy integration with other systems
- PostgreSQL database for reliable data storage

## Architecture

This microservice follows a clean architecture with separation of concerns:

- **API Layer**: FastAPI endpoints for data access and manipulation
- **Service Layer**: Business logic for sleep data processing and analysis
- **Storage Layer**: PostgreSQL database for reliable data persistence
- **Models**: Pydantic models for request/response validation and documentation

## Requirements

- Python 3.9+
- FastAPI
- PostgreSQL
- SQLAlchemy

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/sleep-data-microservice.git
   cd sleep-data-microservice
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Setup PostgreSQL:
   ```bash
   # Create a PostgreSQL database
   createdb sleep_data
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   Edit the `.env` file with your PostgreSQL connection details.

5. Run the service:
   ```bash
   uvicorn app.main:app --reload
   ```

The service will be available at http://localhost:8001 by default.

## API Endpoints

### Sleep Data

- `GET /api/sleep/data` - Get sleep records for a user
- `POST /api/sleep/records` - Create a new sleep record
- `PUT /api/sleep/records/{record_id}` - Update a sleep record
- `DELETE /api/sleep/records/{record_id}` - Delete a sleep record

### Data Import

- `POST /api/sleep/import/apple_health` - Import sleep data from Apple Health export

### Data Generation

- `POST /api/sleep/generate` - Generate synthetic sleep data

### Analysis

- `GET /api/sleep/analytics` - Analyze sleep patterns and trends

## Using with Docker

The easiest way to run the service is with Docker Compose, which will set up PostgreSQL automatically:

```bash
docker-compose up
```

This will start:
- The sleep data microservice on port 8001
- PostgreSQL database on port 5432
- PgAdmin for database management on port 5050

## Development

### Running tests

```bash
pytest
```

### Directory Structure

```
sleep-data-microservice/
├── app/
│   ├── api/             # API routes
│   ├── config/          # Configuration settings
│   ├── models/          # Data models
│   ├── services/        # Business logic
│   │   ├── analytics/   # Sleep data analysis
│   │   ├── import/      # Import services
│   │   └── storage/     # Database interactions
│   └── main.py          # Application entry point
├── tests/               # Test suite
```

## Database Migrations

This project uses Alembic for database migrations. To create and apply migrations:

```bash
# Initialize migrations (first time only)
alembic init migrations

# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head
```

## API Documentation

When the service is running, API documentation is available at:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## Integrating with Other Microservices

While this microservice is designed to work independently, it can be integrated with other services through its API. Some integration examples include:

- **Calendar Microservice**: A separate service can correlate sleep data with calendar events
- **Fitness Microservice**: Can combine sleep data with exercise data for holistic health analysis
- **User Management Service**: For authentication and user data management

## Future Improvements

- Add user authentication and authorization
- Support for additional data sources (Fitbit, Oura Ring, etc.)
- Advanced analytics with machine learning
- Visualization API for generating charts

## License

[MIT](LICENSE)
# Sleep Data Microservice

A Python-based microservice for tracking, analyzing, and correlating sleep data with calendar events.

## Features

- Track sleep metrics including duration, quality, heart rate, and sleep phases
- Import sleep data from Apple Health
- Generate synthetic sleep data for testing and development
- Analyze sleep patterns to identify trends and provide recommendations
- Correlate sleep data with calendar events to discover potential impacts
- RESTful API for easy integration with other systems
- Supports both file-based and database storage

## Architecture

This microservice is designed to work independently or in conjunction with the Google Calendar Microservice. It follows a clean architecture with separation of concerns:

- **API Layer**: FastAPI endpoints for data access and manipulation
- **Service Layer**: Business logic for sleep data processing and analysis
- **Storage Layer**: Abstracted data persistence with support for multiple storage types
- **Models**: Pydantic models for request/response validation and documentation

## Requirements

- Python 3.9+
- FastAPI
- SQLAlchemy (for database storage)
- Optional: Google Calendar Microservice for calendar correlation

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/sleep-data-microservice.git
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
   Edit the `.env` file with your settings.

4. Run the service:
   ```bash
   uvicorn app.main:app --reload
   ```

The service will be available at http://localhost:8001 by default.

## API Endpoints

### Sleep Data

- `GET /api/sleep/data` - Get sleep records for a user
- `POST /api/sleep/records` - Create a new sleep record
- `PUT /api/sleep/records/{record_id}` - Update a sleep record
- `DELETE /api/sleep/records/{record_id}` - Delete a sleep record

### Data Import

- `POST /api/sleep/import/apple_health` - Import sleep data from Apple Health export

### Data Generation

- `POST /api/sleep/generate` - Generate synthetic sleep data

### Analysis

- `GET /api/sleep/analytics` - Analyze sleep patterns and trends
- `GET /api/sleep/correlate` - Correlate sleep data with calendar events

## Using with Docker

1. Build the Docker image:
   ```bash
   docker build -t sleep-data-microservice .
   ```

2. Run the container:
   ```bash
   docker run -p 8001:8001 -e DATABASE_URL=sqlite:///./sleep_data.db sleep-data-microservice
   ```

For full configuration options, see the Docker Compose file.

## Development

### Running tests

```bash
pytest
```

### Directory Structure

```
sleep-data-microservice/
├── app/
│   ├── api/             # API routes
│   ├── config/          # Configuration settings
│   ├── models/          # Data models
│   ├── services/        # Business logic
│   │   ├── analytics/   # Sleep data analysis
│   │   ├── import/      # Import services
│   │   └── storage/     # Database interactions
│   └── main.py          # Application entry point
├── tests/               # Test suite
```

## Future Improvements

- Add user authentication and multi-user support
- Implement more sophisticated sleep analysis algorithms
- Add support for more data sources (Fitbit, Oura Ring, etc.)
- Develop visualization components for sleep metrics
- Create a mobile app for data collection and viewing

## License

[Apache](LICENSE)
