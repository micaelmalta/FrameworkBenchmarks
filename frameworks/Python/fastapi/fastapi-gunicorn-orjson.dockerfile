FROM python:3.9

WORKDIR /fastapi

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements*.txt ./

RUN pip3 install cython==0.29.13 && \
    pip3 install -r /fastapi/requirements.txt -r /fastapi/requirements-orjson.txt -r /fastapi/requirements-gunicorn.txt

COPY . ./

EXPOSE 8080

CMD gunicorn app.app:app -k uvicorn.workers.UvicornWorker -c fastapi_conf.py