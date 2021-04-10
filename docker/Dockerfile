# Python 3.10.0a7-buster

FROM python:3.10.0a7-buster

#WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y \
 can-utils\
 sudo

RUN useradd -m nonrootuser


#COPY requirements.txt ./
#RUN pip install -r requirements.txt
RUN pip install python-can


#COPY . .

USER nonrootuser
#CMD ["python", "./REC-BMS-CAN-logger.py"]
CMD ["bash"]
