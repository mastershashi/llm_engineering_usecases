# AMSAB Steel-Box Worker Image
# Minimal Python image — no shell access, no package manager in the container
FROM python:3.12-slim

# Install CA certificates so SSL works without a system CA bundle
RUN apt-get update -qq && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/*

# Create non-root user for extra isolation
RUN useradd -m -u 1000 amsab

# Pre-install common task libraries
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /workspace
USER amsab

# The runner.py script is mounted at /workspace by the executor
CMD ["python", "runner.py"]
