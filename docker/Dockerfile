FROM python:3.12-slim

# sane defaults
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Copy only what’s needed to build first for better layer caching
# (include LICENSE so `license = { file = "LICENSE" }` resolves)
COPY pyproject.toml README.md LICENSE* ./

# Then copy sources
COPY src/mug ./src/mug

# Install package
RUN python -m pip install --upgrade pip \
 && pip install .

# Run the CLI by default so `docker run mug/dev:local` does something deterministic
CMD ["python", "-m", "mug.cli"]
