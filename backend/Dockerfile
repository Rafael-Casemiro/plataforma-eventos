# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables to optimize Python execution
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Upgrade pip and copy only requirements first to leverage Docker caching
RUN pip install --upgrade pip
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application code to the container
COPY . /app/

# Expose the port Django runs on
EXPOSE 8000

# Apply migrations and start the Django development server
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
