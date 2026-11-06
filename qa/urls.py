from django.urls import path
from rest_framework.routers import SimpleRouter

from qa.views import AskView, HistoryViewSet, SearchView

router = SimpleRouter()
router.register("history", HistoryViewSet, basename="history")

urlpatterns = [
    path("ask/", AskView.as_view(), name="ask"),
    path("search/", SearchView.as_view(), name="search"),
    *router.urls,
]
