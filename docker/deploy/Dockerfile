FROM python:3.11-slim

WORKDIR /app

# Accept the build argument
ARG ENV_NAME
ARG APP_VERSION
ARG APP_PORT

# Make it an environment variable in container
ENV ENV_NAME=${ENV_NAME}
ENV APP_VERSION=${APP_VERSION}
ENV APP_PORT=${APP_PORT}

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    libicu-dev \
    ca-certificates \
    curl \
    dos2unix \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN update-ca-certificates

# Install uv
RUN curl -Ls https://astral.sh/uv/install.sh -o install_uv.sh && \
    chmod +x install_uv.sh && \
    ./install_uv.sh

# Add uv to PATH
ENV PATH="/root/.local/bin:$PATH"

# Confirm uv is installed
RUN uv --version

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --frozen --no-dev

# Copy application code
COPY ./app ./app
COPY ./database ./database
COPY ./migrations ./migrations
COPY ./alembic.ini ./alembic.ini
COPY ./main.py ./main.py
COPY ./entrypoint.sh ./entrypoint.sh

# Convert shell script to Unix format (important for Windows users)
RUN dos2unix ./entrypoint.sh

RUN chmod +x ./entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]

# Expose the port the app runs on
EXPOSE ${APP_PORT}
