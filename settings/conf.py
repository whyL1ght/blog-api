# Python modules
from decouple import config
from datetime import timedelta

# ----------------------------------------------
# Env id
#
ENV_POSSIBLE_OPTIONS = (
    'local',
    'prod',
)

ENV_ID = config("BLOG_ENV_ID", cast=str)
BLOG_SECRET_KEY = 'django-insecure-17hq)3w=i6r&ov#!cq#kn$8a%06zu)ik+a$tg9#&bt@soubf%+'
