FROM python:3.12-slim

WORKDIR /

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
ARG DJANGO_SECRET_KEY
ENV DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}

RUN python manage.py collectstatic --noinput
RUN python manage.py migrate
EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "django_movietv.wsgi:application"]
