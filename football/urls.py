from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

urlpatterns = [
    path('login/', LoginView.as_view(template_name="football/login.html"), name='login'),
    path('logout/', LogoutView.as_view(template_name="football/logout.html"), name='logout'),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("", views.IndexView.as_view(), name="index"),
    path("<int:pk>/", views.TeamMatchesView.as_view(), name="team_matches"),
    path("lap/<int:pk>/", views.LapView.as_view(), name="lap"),
    path("match/create/", views.MatchCreateView.as_view(), name="match_create"),
    path("match/<int:pk>/delete/", views.MatchDeleteView.as_view(), name="match_delete"),
    path("match/<int:pk>/update/", views.MatchUpdateView.as_view(), name="match_update"),
    path("match/<int:pk>/update/lineup/<str:team_type>/", views.LineupUpdateView.as_view(), name="lineup"),
    path("match/<int:pk>/create/lineup/<str:team_type>/", views.LineupCreateView.as_view(), name="lineup_create"),
    path("match/<int:pk>/update/event/", views.EventCreateView.as_view(), name="event"),
    path("match/<int:pk>/update/event/<int:event_pk>/", views.TeamCreateEventView.as_view(), name="players_to_event"),
    path("match/<int:pk>/details/", views.MatchDetailsView.as_view(), name="match_details"),
    # path("match/<int:pk>/update/event/substitution/int:event_pk>/")
    path("table/", views.TableView.as_view(), name="table"),
    path("laps/", views.LapsListView.as_view(), name="laps_list"),
    path("team/<int:pk>/", views.TeamInfoView.as_view(), name="team_info"),
]