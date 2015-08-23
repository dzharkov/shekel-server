from django.conf.urls import patterns, include, url
from django.contrib import admin
import settings

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'(?P<id>\d+)/?', 'app.views.event'),
    url(r'^login/?', 'app.views.login'),
    url(r'^log/?$', 'app.views.show_log'),
    url(r'^(?P<model_name>[a-z]+)/?$', 'app.views.request_handler'),
    url(r'^(?P<model_name>[a-z]+)/(?P<id>\d+)?$', 'app.views.request_handler'),
)

urlpatterns += patterns('',
         (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
     )
