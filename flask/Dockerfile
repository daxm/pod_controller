FROM ubuntu:latest
MAINTAINER Dax Mickelson "dmickels@cisco.com"
RUN echo "add-apt-repository universe"
RUN echo "apt-get install -y software-properties-common"
RUN apt-get update -y
RUN apt-get install -y python3-pip python3-dev build-essential
COPY . /app
WORKDIR /app
RUN pip3 install -r requirements.txt
ENTRYPOINT ["python3"]
CMD ["myproject.py"]
