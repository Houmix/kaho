from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [path('api/', include('api.urls'))]

# Panneau Django natif : maintenance technique uniquement (DJANGO_ADMIN_ENABLED), jamais pour la gestion quotidienne
if settings.DJANGO_ADMIN_ENABLED:
    urlpatterns.insert(0, path('admin/', admin.site.urls))

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
