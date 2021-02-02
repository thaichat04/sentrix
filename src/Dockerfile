FROM huggingface/transformers-pytorch-cpu

WORKDIR /wd
ADD / /wd

RUN pip install --upgrade pip \
    &&  pip install --trusted-host pypi.python.org --requirement /wd/requirements.txt

CMD ["python3", "-u" , "/wd/app.py", "--conf", "/wd/configuration.yaml", "server"]