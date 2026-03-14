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
SECRET_KEY = config("SECRET_KEY")
