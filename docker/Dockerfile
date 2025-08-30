FROM python:3.12-slim
WORKDIR /app
# Only copy the files needed to install first, for better layer caching
COPY pyproject.toml README.md ./
COPY src/mug ./src/mug
RUN python -m pip install --no-cache-dir --upgrade pip && \
    pip install .
# Run the CLI by default so `docker run mug/dev:local` does something deterministic
CMD ["python", "-m", "mug.cli"]
