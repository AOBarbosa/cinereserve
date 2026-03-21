from django.urls import path

from apps.users.views import CookieTokenRefreshView, ListUsersView, LoginView, LogoutView, MyTicketsView, RegisterView

urlpatterns = [
    path("", ListUsersView.as_view(), name="user-list"),
    path("tickets/", MyTicketsView.as_view(), name="my-tickets"),
    path("register/", RegisterView.as_view(), name="user-register"),
    path("login/", LoginView.as_view(), name="user-login"),
    path("logout/", LogoutView.as_view(), name="user-logout"),
    path("token/refresh/", CookieTokenRefreshView.as_view(), name="token_refresh"),
]
