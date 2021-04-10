# Python 3.10.0a7-buster

FROM python:3.10.0a7-buster

# can-utils is required by python-can
# sudo is needed because it is used in code for running on rPi
RUN apt-get update && apt-get install -y \
 can-utils\
 sudo

RUN pip install python-can

# default to shell
CMD ["bash"]
