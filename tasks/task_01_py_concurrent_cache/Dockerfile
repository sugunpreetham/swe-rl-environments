FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir pytest

COPY . /app

CMD ["pytest", "tasks/task_01_py_concurrent_cache/verifier/test_verifier.py", "-v"]
