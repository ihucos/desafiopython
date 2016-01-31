
from django.conf.urls import url
from .views import UserCreate, UserView, login_view

urlpatterns = [
    url(r'^api/users/(?P<pk>[-\w]+)/$', UserView.as_view(), name='view-user'),
    url(r'^api/users', UserCreate.as_view(), name='create-user'),
    url(r'^api/login', login_view, name='login')
]
