FROM python:3

COPY . /REMOTE_MANAGER_FLASK

WORKDIR /REMOTE_MANAGER_FLASK

RUN pip install -r requirements.txt

EXPOSE 5000
ENTRYPOINT ["python"]
CMD ["app.py"]