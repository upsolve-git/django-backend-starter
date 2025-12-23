from .import views
from django.urls import path,include
from django.views.generic import RedirectView

urlpatterns=[
    path('', RedirectView.as_view(url='/login/'), name='home'),
    path('login/', views.Login.as_view()),
    path('signup/', views.SignUp.as_view()),
    path('resetPassword/', views.ResetPassword.as_view()),
    path('forgotPassword/', views.ForgotPassword.as_view()),
]   
