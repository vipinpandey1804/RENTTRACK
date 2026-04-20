from django.urls import path

from . import views

urlpatterns = [
    path("live/", views.liveness, name="liveness"),
    path("ready/", views.readiness, name="readiness"),
]
