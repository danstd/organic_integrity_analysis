#FROM python:3.10-alpine3.16
FROM python:3.10

ENV TZ America/New_York

COPY Application Application
COPY requirements.txt requirements.txt
COPY .env .env

RUN apt-get update && \
    apt-get install -y cron

#RUN apk update && \
#     apk add --virtual build-deps gcc g++ musl-dev busybox-initscripts make blas
#
## Add the cron job
RUN crontab -l | \
    { cat; echo "0 0 15 * * python /Application/processing/process_setup.py" >> \
    /Application/processing/integrity_app_dag_log.log; } | crontab -


RUN pip install -r requirements.txt
#RUN pip install --no-deps pandas sklearn scikit-learn scipy

EXPOSE 5000

WORKDIR /Application

RUN pip install -e /Application

RUN useradd -m containeruser
RUN touch /Application/processing/integrity_app_dag_log_cron.txt
RUN touch /Application/processing/integrity_app_dag_log.log
#RUN chown containeruser /Application/processing/integrity_app_dag_log_cron.txt
RUN chown containeruser /Application/processing/integrity_app_dag_log.log

ADD ./.profile.d /app/.profile.d

# hopefully allowing to remote into heroku.
RUN rm /bin/sh && ln -s /bin/bash /bin/sh

USER containeruser

#RUN crontab -l | \
#    { cat; echo "0 0 15 * * python /Application/processing/process_setup.py" >> \
#    /Application/processing/integrity_app_dag_log_cron.txt; } | crontab -



# Line below is for local.
#ENTRYPOINT [ "flask", "run", "--host", "0.0.0.0"]

ENTRYPOINT ["gunicorn", "integrity_app:app"]