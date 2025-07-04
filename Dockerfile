FROM python
WORKDIR /app
COPY . /app
RUN apt update
RUN apt install --upgrade -y python3-pip expat && apt full-upgrade
RUN pip install -r requirements.txt
EXPOSE 80
CMD ["flask", "--debug", "run", "--host=0.0.0.0", "--port=80"]

