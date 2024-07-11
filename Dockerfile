FROM python:3.12-slim

WORKDIR /

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
ENV DJANGO_SECRET_KEY="django-secure-#9kvl+47k#u5@u#sua6z5u8-n1ib5@r$v4g#n_q^x3@_$^4=yj"
RUN python manage.py collectstatic --noinput
EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "django_movietv.wsgi:application"]
