from rest_framework.routers import SimpleRouter

from apps.comments.api.views import CommentViewSet

router = SimpleRouter(trailing_slash=False, use_regex_path=False)
router.register("comments", CommentViewSet, basename="comment")

urlpatterns = router.urls
