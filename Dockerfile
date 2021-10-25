FROM python:3.8-slim-buster

RUN apt-get update && apt-get install -y git
WORKDIR /app
ADD requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY ./src /app

CMD ["python", "-m", "prozorro_bridge_pricequotation.main"]