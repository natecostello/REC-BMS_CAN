# Python 3.10.0a7-buster

FROM python:3.10.0a7-buster

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y \
 can-utils

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "./REC-BMS-CAN-logger.py"]
