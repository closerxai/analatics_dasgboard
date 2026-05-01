from django.contrib import admin
from django.urls import path, include

def _superuser_only_admin_has_permission(request):
    user = getattr(request, "user", None)
    return bool(user and user.is_active and user.is_superuser)

# Only superusers can access /admin/ (staff users will be blocked).
admin.site.has_permission = _superuser_only_admin_has_permission

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('auth_app.urls')),
    path('api/', include('crm.urls')),
]
