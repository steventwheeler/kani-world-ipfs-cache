FROM python:3.8-slim-buster

WORKDIR /src

RUN pip install pipenv

COPY Pipfile Pipfile.lock ./
RUN pipenv requirements > requirements.txt \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "update-kani.py"]
