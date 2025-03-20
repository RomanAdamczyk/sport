from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .models import Match, Lineup, Event, Player, Team, Substitution


class LoginForm(forms.Form):
    username = forms.CharField(max_length=65)
    password = forms.CharField(max_length=65, widget=forms.PasswordInput)

class RegisterForm(UserCreationForm):
    usable_password = None
    
    class Meta:
        model=User
        fields = ['username','email','password1','password2'] 

class MatchForm(forms.ModelForm):
    class Meta:
        model= Match
        fields = ['lap', 'date','home_team', 'away_team', 'home_score', 'away_score']
        widgets = {
            'lap': forms.NumberInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'home_team': forms.Select(attrs={'class': "form-control", 'style': 'width: 80%;'}),
            'away_team': forms.Select(attrs={'class': 'form-control', 'style': 'width: 80%;'}),
            'home_score': forms.NumberInput(attrs={'class': 'form-control'}),
            'away_score': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class LineupForm(forms.ModelForm):
    players = forms.ModelMultipleChoiceField(
    queryset=Player.objects.all(),  # Lista dostępnych zawodników
    widget=forms.CheckboxSelectMultiple,
    )
    
    def __init__(self, *args, **kwargs):
        team = kwargs.pop('team', None)  # Pobieramy drużynę z argumentów
        super().__init__(*args, **kwargs)  # Inicjalizujemy formularz
        if team:
            self.fields['players'].queryset = Player.objects.filter(team=team)

        self.fields['players'].label_from_instance = lambda obj: obj.name

    def clean_players(self):
        players = self.cleaned_data.get('players')
        if len(players) != 11:
            raise forms.ValidationError("Wybierz dokładnie 11 zawodników!")
        return players
    
    def form_valid(self, form):
        # Jeśli formularz jest poprawny, zapisz go i przekieruj
        form.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        # Jeśli formularz jest niepoprawny, po prostu renderuj stronę z błędami
        return self.render_to_response(self.get_context_data(form=form))
        
    class Meta:
        model = Lineup
        fields = ["players"]

class EventForm(forms.ModelForm):

    def __init__(self, *args, match=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.instance.match = match
        self.fields['team'].queryset = Team.objects.filter(pk__in=[match.home_team.pk, match.away_team.pk])
           

    class Meta:
        model = Event
        fields = ["event_type", "team", "minute", "description"]

class TeamCreateEventForm(forms.ModelForm):
    def __init__(self, *args, event_type=None, players_in_match=None, players_on_bench=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['player'].label_from_instance = lambda obj: obj.player.name
        if players_in_match:
            self.fields['player'].queryset = players_in_match
        if event_type == "substitution" and players_on_bench:
            self.fields['player_in'] = forms.ModelChoiceField(
                queryset=players_on_bench,
                label="Player In",
                required=True
            )

    def clean_player(self):
        event = self.cleaned_data.get('player')
        player = event.player
        return player


    # def save(self, commit=True):
    #     event = super().save(commit=False)  # Tworzysz główny obiekt Event
    #     print(commit)
    #     print(event.event_type)
    #     if commit:
    #         event.save()
    #         # Zapisz Substitution, jeśli to konieczne
    #         if event.event_type == "substitution":
    #             player_in = self.cleaned_data['player_in']
    #             Substitution.objects.create(event=event, player_in=player_in)
    #     return event

    class Meta:
        model = Event
        fields = ['player']
