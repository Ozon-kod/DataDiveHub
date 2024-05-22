# docker build -t divedata .

FROM python:3.12-alpine

# Set the working directory
WORKDIR /app

# Copy requirements.txt
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY templates ./templates
COPY app.py .


ENTRYPOINT [ "python3" ]
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]