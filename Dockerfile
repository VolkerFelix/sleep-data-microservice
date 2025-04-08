FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create a non-root user to run the app
RUN adduser --disabled-password --gecos "" appuser
RUN mkdir -p /app/data && chown -R appuser:appuser /app

USER appuser

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose the port the app runs on
EXPOSE 8001

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]