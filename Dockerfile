FROM python:3.11-slim AS base

# Set environment variables to ensure output isn't buffered
ENV PYTHONUNBUFFERED=1

# Create a non-root user to run the application (optional, but recommended for
# better security even though the app will be accessed by IP without auth)
RUN adduser --disabled-password --gecos '' appuser

WORKDIR /opt/app

# Copy application code
COPY . /opt/app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Ensure upload directories exist and owned by appuser.  The application
# uses a root‑level `uploads` folder by default; we also create
# `fastreader/uploads` for backward compatibility.
RUN mkdir -p uploads fastreader/uploads && chown -R appuser:appuser uploads fastreader/uploads

USER appuser

EXPOSE 5000

# Default command to run the Flask app. We run the module directly to
# trigger the `__main__` clause in fastreader/app.py.
CMD ["python", "-m", "fastreader.app"]