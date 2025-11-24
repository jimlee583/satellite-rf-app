############################
# Stage 1: Build frontend  #
############################
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

# Install dependencies
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install

# Build Vite app
COPY frontend/ ./
RUN npm run build


############################
# Stage 2: Backend runtime #
############################
FROM python:3.12-slim AS backend-runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


# Copy backend source
COPY backend ./backend

# Copy built frontend assets into the image
COPY --from=frontend-builder /frontend/dist ./frontend/dist

# Cloud Run will set PORT; default to 8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]


