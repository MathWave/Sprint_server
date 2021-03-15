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
    path('rating', views.rating),
    path('messages', views.messages),
    path('admin/rating', views.rating),
    path('admin/download_rating', views.download_rating),
    path('admin/solution', views.solution),
    path('admin/retest', views.retest),
    path('admin/docs', views.docs),
    path('admin/block', views.block_settings),
    path('admin/task', views.task_settings),
    path('admin/main', views.admin),
    path('admin/solutions', views.solutions),
    path('admin/users_settings', views.users_settings),
    path('admin/download', views.download),
    path('admin/queue', views.queue),
    path('admin/cheating', views.cheating),
    path('queue_table', views.queue_table),
    path('task_test', views.task_test),
    path('solutions_table', views.solutions_table),
    path('get_result_data', views.get_result_data),
    path('get_comment_data', views.get_comment_data),
    re_path('^', views.redirect)
]
