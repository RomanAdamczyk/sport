from django.contrib import admin
from .models import Match, Team, Player, Lineup, Event, Substitution

class TeamAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": ["name"]}),
        (None, {"fields": ["city"]}),
        (None, {"fields": ["founded"]}),
        ("Stadium", {"fields": ["stadium"], "classes":["collapse"]})
    ]
    list_display = ["name", "city", "founded", "stadium"]

class MatchAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": [("home_team", "away_team", "home_score", "away_score")]}),
        (None, {"fields": ["date", "lap"]})      
    ]
    list_display = ["id", "home_team", "away_team", "home_score", "away_score", "lap", "date"]
    list_filter = ['lap', 'home_team', 'away_team']

class PlayerAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": [("name", "team", "position")]}),
        (None, {"fields": [("nationality", "birth_day")]})
    ]

    list_display = ["id", "name", "team","position","nationality", "birth_day"]

class LineupAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": [("match", "team","player","is_starting","on_bench")]})
    ]

    list_display = ["id","match", "team","player","is_starting","on_bench"]

class EventAdmin(admin.ModelAdmin):
    fieldsets =[
        (None, {"fields": [("match", "team","player")]}),
        (None, {"fields": [("event_type", "minute", "description")]})
    ]

    list_display = ["id","match", "team","player", "event_type", "minute", "description"]

class SubstitutionAdmin(admin.ModelAdmin):
    fieldsets =[
        (None, {"fields": [("event", "player_in")]})
    ]

    list_display = ["event", "player_in"]


admin.site.register(Team, TeamAdmin)
admin.site.register(Match, MatchAdmin)
admin.site.register(Player, PlayerAdmin)
admin.site.register(Lineup, LineupAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Substitution,SubstitutionAdmin)
