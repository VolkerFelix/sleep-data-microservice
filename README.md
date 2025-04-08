# Sleep Data Microservice

A Python-based microservice for tracking, analyzing, and correlating sleep data with calendar events.

## Features

- Track sleep metrics including duration, quality, heart rate, and sleep phases
- Import sleep data from Apple Health
- Generate synthetic sleep data for testing and development
- Analyze sleep patterns to identify trends
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

[MIT](LICENSE)