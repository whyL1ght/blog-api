# Third party modules
import logging
# DRF modules
from rest_framework.status import HTTP_200_OK
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
# project modules
from apps.blogs.throttles import LoginTareThrottle


logger = logging.getLogger(__name__)


class LoggedTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [LoginTareThrottle]

    def post(self, request, *args, **kwargs):
        email = request.data.get("email", "-")
        logger.info("Login attempt for email : %s", email)
        response = super().post(request, *args, **kwargs)

        if response.status_code == HTTP_200_OK:
            logger.info("Login successful for email: %s", email)
        else:
            logger.warning("Login failed for email: %s", email)
        return response
    

class LoggedTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        logger.debug("Token refresh requested")
        return super().post(request, *args, **kwargs)
