FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    sqlalchemy \
    psycopg2-binary \
    pydantic \
    passlib[bcrypt] \
    bcrypt==4.0.1 \
    python-jose[cryptography] \
    python-dotenv \
    python-multipart

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]