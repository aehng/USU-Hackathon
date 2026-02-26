# 1. Grab a lightweight Linux machine with Python pre-installed
FROM python:3.12-slim

# 2. Make a folder inside the container called /app and go inside it
WORKDIR /app

# 3. Copy your list of libraries from your VM into the container
COPY requirements.txt .

# 4. Tell the container to install those libraries
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your Python code into the container
COPY . .

# 6. The command to start the FastAPI server when the container turns on
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
