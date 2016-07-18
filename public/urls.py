from django.conf.urls import url

from . import views

app_name = 'public'

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^faq$', views.faq, name='faq'),
    url(r'^login$', views.login_user, name='login'),
    url(r'^register$', views.register, name='register'),
    url(r'^confirm-registration/(?P<token>.+)$', views.confirm_registration, name='confirm_registration'),
    url(r'^logout$', views.logout_user, name='logout'),
    url(r'^password-forgotten$', views.password_forgotten, name='password_forgotten'),
    url(r'^password-reset/(?P<token>.+)$', views.password_reset, name='password_reset'),
    url(r'^account$', views.account, name='account'),
    url(r'^create-team$', views.create_team, name='create_team'),
    url(r'^make-submission$', views.make_submission, name='make_submission'),
]
