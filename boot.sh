#!/bin/sh
#gunicorn -b :5000 integrity_app:app
gunicorn -b 0.0.0.0:5000 integrity_app:app