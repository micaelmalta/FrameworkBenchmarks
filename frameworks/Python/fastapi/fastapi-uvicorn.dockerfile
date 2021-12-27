FROM python:3.9

WORKDIR /fastapi

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements*.txt ./

RUN pip3 install cython==0.29.13 && \
    pip3 install -r /fastapi/requirements.txt -r /fastapi/requirements-uvicorn.txt

COPY . ./

EXPOSE 8080

CMD uvicorn app.app:app --host 0.0.0.0 --port 8080 --workers $(nproc) --log-level error
