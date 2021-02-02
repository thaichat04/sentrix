FROM python:3.8-buster

WORKDIR /wd
COPY app/requirements.txt /wd/

RUN pip install --upgrade pip \
    &&  pip install --trusted-host pypi.python.org --requirement wd/requirements.txt

CMD ["python", "app.py"]