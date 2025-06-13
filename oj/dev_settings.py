# coding=utf-8
import os
from utils.shortcuts import get_env

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'onlinejudge',
        'USER': 'onlinejudge',
        'PASSWORD': 'onlinejudge',
        'HOST': 'localhost',
        'PORT': '5435',
        'OPTIONS': {
            'options': '-c TimeZone=UTC'
        },
    }
}

REDIS_CONF = {
    'host': get_env('REDIS_HOST', '127.0.0.1'),
    'port': get_env('REDIS_PORT', '6380')
}

DEBUG = True

ALLOWED_HOSTS = ["*"]

DATA_DIR = f"{BASE_DIR}/data"

# CSRF settings
CSRF_TRUSTED_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:8000', 'http://localhost:8080/', 'http://192.168.0.191:8080/']
