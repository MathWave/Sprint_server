from django.contrib import admin
from django.urls import path, re_path, include
from Main import views

urlpatterns = [
    path('grappelli/', include('grappelli.urls')), # grappelli URLS
    path('admin/', admin.site.urls),

    path('main', views.main),
    path('settings', views.settings),
    path('enter', views.enter, name='enter'),
    path('restore', views.restore, name='restore'),
    path('reset_password', views.reset_password),
    path('exit', views.exit),
    path('block', views.block),
    path('task', views.task),
    path('solution', views.solution),
    path('admin/solution', views.solution),
    path('admin/retest', views.retest),
    path('admin/docs', views.docs),

    path('admin/block', views.block_settings),
    path('admin/task', views.task_settings),
    path('admin/main', views.admin),
    path('admin/solutions', views.solutions),
    path('admin/users_settings', views.users_settings),
    # path('admin/download', views.download),
    path('set_result', views.set_result),
    path('task_test', views.task_test),

    re_path('^', views.redirect)
]
