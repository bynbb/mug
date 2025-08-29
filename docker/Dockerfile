FROM python:3.12-slim
WORKDIR /app
RUN python -m pip install --no-cache-dir pytest
ENTRYPOINT ["python","-m","http.server","--help"]
