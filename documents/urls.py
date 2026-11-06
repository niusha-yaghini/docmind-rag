from rest_framework.routers import SimpleRouter

from documents.views import DocumentViewSet

router = SimpleRouter()
router.register("documents", DocumentViewSet, basename="document")

urlpatterns = router.urls
