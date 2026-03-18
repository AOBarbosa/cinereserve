from django.urls import path

from apps.users.views import CookieTokenRefreshView, LoginView, LogoutView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="user-register"),
    path("login/", LoginView.as_view(), name="user-login"),
    path("logout/", LogoutView.as_view(), name="user-logout"),
    path("token/refresh/", CookieTokenRefreshView.as_view(), name="token_refresh"),
]
