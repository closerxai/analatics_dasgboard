from django.urls import path

from .views import (
    CompanyCreateAPIView,
    CompanyListAPIView,
    LeadCreateAPIView,
    LeadListAPIView,
    MyCompanyAPIView,
    ProjectListCreateAPIView,
)

urlpatterns = [
    path("companies/", CompanyListAPIView.as_view(), name="company-list"),
    path("companies/create/", CompanyCreateAPIView.as_view(), name="company-create"),
    path("my-company/", MyCompanyAPIView.as_view(), name="my-company"),
    path("projects/", ProjectListCreateAPIView.as_view(), name="project-list-create"),
    path("leads/", LeadListAPIView.as_view(), name="lead-list"),
    path("leads/create/", LeadCreateAPIView.as_view(), name="lead-create"),
]
