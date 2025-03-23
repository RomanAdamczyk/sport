from django.db import models
from django.core.exceptions import ValidationError

class Team(models.Model):
    name = models.CharField(max_length=64, null=False, blank=False)
    city = models.CharField(max_length=64, null=False, blank=False)
    founded = models.DateField()
    stadium = models.CharField(max_length=64, blank=True)

    def __str__(self) -> str:
        return self.name

class Match(models.Model):
    home_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='home_matches')
    away_team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='away_matches')
    date = models.DateField()
    home_score = models.IntegerField()
    away_score = models.IntegerField()
    lap = models.IntegerField()

    def __str__(self) -> str:
        return self.home_team.name + " vs " + self.away_team.name
    
    def clean(self):
        if self.home_score < 0:
            raise ValidationError({'home_score': 'Wynik nie może być ujemny.'})
        if self.away_score < 0:
            raise ValidationError({'away_score': 'Wynik nie może być ujemny.'})
        if self.lap <=0:
            raise ValidationError({'lap': 'kolejka nie moze być ujemna'})
        if self.home_team == self.away_team:
            raise ValidationError({'away_team': 'drużyna gości nie może być taka sama jak drućyna gospodarzy'})


class Player(models.Model):
    POSITION=(
        ('gk', 'bramkarz'),
        ('df', 'obrońca'),
        ('mf', 'pomocnik'),
        ('st', 'napastnik')
    )
    team = models.ForeignKey(Team, models.SET_NULL,blank=True,null=True,)
    name = models.CharField(max_length=50)
    birth_day = models.DateField()
    position = models.CharField(max_length=2, choices=POSITION)
    nationality = models.CharField(max_length=40)

    def __str__(self):
        team_name = self.team.name if self.team else "Brak drużyny"
        return f"{self.name} ({team_name}) - {self.get_position_display()} - {self.nationality} - {self.birth_day}"
    
class Lineup(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="lineups")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="lineups")
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="lineups")
    is_starting = models.BooleanField(default=True)  # Czy gracz zaczyna w pierwszym składzie
    on_bench = models.BooleanField(default=False) # Po zejściu z boiska

    def __str__(self):
        status = "Starting" if self.is_starting else "Substitute"
        return f"{self.player.name} ({status}) - {self.team.name} in {self.match}"

class Event(models.Model):
    EVENT_TYPES = [
        ("goal", "Bramka"),
        ("own_goal", "Bramka samobójcza"),
        ("yellow_card", "Żółta kartka"),
        ("red_card", "Czerwona kartka"),
        ("substitution", "Zmiana"),
    ]

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="events")
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name="events")
    player = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name="events")
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    minute = models.PositiveIntegerField()
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.match} ({self.minute} min)"

class Substitution(models.Model):
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name="substitution", help_text="Wydarzenie związane z tą zmianą")
    player_in = models.ForeignKey(Player, on_delete=models.CASCADE, related_name="substitutions_in",help_text="Zawodnik wchodzący na boisko")

    def __str__(self):
        return f"{self.player_in.name} za {self.event.player.name} z {self.event.match} {self.event.minute} mech: {self.event.match}"