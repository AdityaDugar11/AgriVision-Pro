FROM python:3.11-slim

WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project
COPY . .

# Run with proper shell syntax
CMD ["sh", "-c", "cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000"]
