from django.contrib import admin
from django.conf import settings
from django.conf.urls import patterns, include, url

from oscar.app import shop
from oscar_mws.dashboard.app import application as mws_app


admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    # i18n URLS need to live outside of i18n_patterns scope of the shop
    url(r'^i18n/', include('django.conf.urls.i18n')),

    url(r'^dashboard/', include(mws_app.urls)),
    url(r'', include(shop.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns(
        '',
        url(
            r'^media/(?P<path>.*)$',
            'django.views.static.serve', {
                'document_root': settings.MEDIA_ROOT,
            }
        ),
    )
