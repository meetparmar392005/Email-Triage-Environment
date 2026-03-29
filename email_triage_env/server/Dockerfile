FROM python:3.11-slim

WORKDIR /app

# Install openenv-core and dependencies
RUN pip install --no-cache-dir openenv-core fastapi uvicorn

# Copy the full package
COPY . .

# Install the environment package itself
RUN pip install --no-cache-dir -e .

EXPOSE 7860

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]