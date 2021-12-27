FROM nginx/unit:1.26.1-python3.9

WORKDIR /fastapi

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements*.txt ./

RUN pip3 install -r /fastapi/requirements.txt

COPY . ./

COPY ./nginx-unit-config.sh /docker-entrypoint.d/

EXPOSE 8080
