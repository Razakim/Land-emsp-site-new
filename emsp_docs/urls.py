from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('bibliotheque/', include('bibliotheque.urls')),
    path('inscription/', include('inscription.urls')),
    path('espace-etudiant/', include('espace_etudiant.urls')),
    path('administration/', include(('administration.urls', 'administration'), namespace='administration')),
    path('admin-emsp/', include(('administration.urls', 'administration'), namespace='administration_emsp')),
    path('admin/', admin.site.urls),
    path('login/', RedirectView.as_view(pattern_name='accounts:login', permanent=False)),
    path('register/', RedirectView.as_view(pattern_name='accounts:register', permanent=False)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
