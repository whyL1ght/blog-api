from typing import Callable, Optional
# Django modules
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.utils import timezone, translation


class LanguageAndTimezoneMiddleware:
    """
    Language and Timezone middleware
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:

        lang: Optional[str] = None

        if request.user.is_authenticated:
            lang = request.user.language

        if not lang:
            lang = request.GET.get("lang")

        if not lang:
            lang = translation.get_language_from_request(request, check_path=False)

        if not lang or lang not in [code for code, _ in settings.LANGUAGES]:
            lang = settings.LANGUAGE_CODE

        translation.activate(lang)
        request.LANGUAGE_CODE = lang 

        if request.user.is_authenticated:
            import pytz
            try:
                user_tz = pytz.timezone(request.user.timezone)
                timezone.activate(user_tz)
            except Exception:
                timezone.activate(pytz.UTC)
        else:
            timezone.deactivate()

        response = self.get_response(request)

        translation.deactivate()

        return response