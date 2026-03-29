FROM python:3.13

WORKDIR /app

RUN pip install poetry

COPY  pyproject.toml requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "Teste:app", "--host", "0.0.0.0", "--port", "8000"]