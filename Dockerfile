# docker build -t divedata .

FROM python:3.12-alpine

# Set the working directory
WORKDIR /database

# Copy requirements.txt
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . /database

EXPOSE 5000



ENTRYPOINT [ "python3" ]
CMD [ "app.py" ]