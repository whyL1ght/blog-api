# DRF modules
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

class RegisterRateThrottle(AnonRateThrottle):
    scope = "register"


class LoginTareThrottle(AnonRateThrottle):
    scope = "login"


class PostCreateThrottle(UserRateThrottle):
    scope = "post_create"