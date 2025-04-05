from typing import Any
from django.views import generic
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, F, Count, Sum, Subquery, OuterRef
from django.http import HttpResponseRedirect
from django.contrib.auth import login
from django.shortcuts import redirect
from django.contrib.auth.models import Group
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin

from .models import Match, Team, Player, Lineup, Event, Substitution
from .forms import MatchForm, LineupForm, EventForm, TeamCreateEventForm
from .forms import RegisterForm


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'football/register.html'
    
    def form_valid(self, form):
        user = form.save()
        default_group, created = Group.objects.get_or_create(name='Uzytkownicy')
        user.groups.add(default_group)
        if user:
            login(self.request, user)

        return redirect('index')

class IndexView(generic.ListView):
    model = Team
    template_name = "football/index.html"

    def get_queryset(self):
       return Team.objects.all()

class TeamMatchesView(LoginRequiredMixin, generic.DetailView):
    model = Team
    template_name = "football/team_matches.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = self.object
        matches = Match.objects.filter(Q(home_team=team) | Q(away_team=team)).order_by('lap')
        context['matches'] = matches
        return context
    
class LapView(LoginRequiredMixin,generic.ListView):
    model = Match
    template_name = "football/lap.html" 

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        lap = self.kwargs['pk']
        matches = Match.objects.filter(lap=lap)
        context['matches'] = matches
        context['lap'] = lap
        return context
    
class MatchCreateView(PermissionRequiredMixin, CreateView):
    model = Match
    fields = ['lap', 'date','home_team', 'away_team', 'home_score', 'away_score']
    template_name = 'football/match_create.html'
    success_url = reverse_lazy('index')
    permission_required = ['football.add_match', 'football.view_match']

    def form_valid(self, form):
        match = form.save()  # Mecz zostaje zapisany i otrzymuje pk
        # Przekieruj do widoku szczegółowego lub update view, gdzie opcjonalnie można ustawić skład
        return redirect(reverse('match_details', kwargs={'pk': match.pk}))

class MatchDeleteView(PermissionRequiredMixin, DeleteView):
    model = Match
    template_name = 'football/match_delete.html'
    success_url = reverse_lazy('index')
    permission_required = ['football.delete_match', 'football.view_match']

class MatchUpdateView(PermissionRequiredMixin, UpdateView):
    model = Match
    form_class = MatchForm
    template_name = 'football/match_update.html'
    success_url = reverse_lazy('index')
    permission_required = ['football.change_match', 'football.view_match']

class TableView(LoginRequiredMixin,generic.ListView):
    model = Team
    template_name = 'football/table.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        teams_stat = Team.objects.annotate(
            home_wins=Count('home_matches', distinct=True, filter=Q(home_matches__home_score__gt=F('home_matches__away_score'))),
            away_wins=Count('away_matches', distinct=True, filter=Q(away_matches__away_score__gt=F('away_matches__home_score'))),
            home_draws=Count('home_matches', distinct=True, filter=Q(home_matches__home_score=F('home_matches__away_score'))),
            away_draws=Count('away_matches', distinct=True, filter=Q(away_matches__away_score=F('away_matches__home_score'))),
            home_loses=Count('home_matches', distinct=True, filter=Q(home_matches__home_score__lt=F('home_matches__away_score'))),
            away_loses=Count('away_matches', distinct=True, filter=Q(away_matches__away_score__lt=F('away_matches__home_score'))),
        ).annotate(
            wins=F('home_wins') + F('away_wins'),
            draws=F('home_draws') + F('away_draws'),
            loses=F('home_loses') + F('away_loses'),
            points=(F('wins') * 3) + (F('draws') * 1),
            home_goals_scored=Subquery(
                Match.objects.filter(home_team=OuterRef('pk'))
                .values('home_team')
                .annotate(total_goals=Sum('home_score'))
                .values('total_goals')
            ),
            away_goals_scored=Subquery(
                Match.objects.filter(away_team=OuterRef('pk'))
                .values('away_team')
                .annotate(total_goals=Sum('away_score'))
                .values('total_goals')
            ),
            home_goals_conceded=Subquery(
                Match.objects.filter(home_team=OuterRef('pk'))
                .values('home_team')
                .annotate(total_conceded=Sum('away_score'))
                .values('total_conceded')
            ),
            away_goals_conceded=Subquery(
                Match.objects.filter(away_team=OuterRef('pk'))
                .values('away_team')
                .annotate(total_conceded=Sum('home_score'))
                .values('total_conceded')
            ),

            # home_goals_scored=Sum('home_matches__home_score'),
            # away_goals_scored=Sum('away_matches__away_score'),
            goals_scored=F('home_goals_scored') + F('away_goals_scored'),
            # home_goals_conceded=Sum('home_matches__away_score'),
            # away_goals_conceded=Sum('away_matches__home_score'),
            goals_conceded=F('home_goals_conceded') + F('away_goals_conceded'),
            goals_difference=F('goals_scored') - F('goals_conceded'),
            matches=F('wins') + F('draws') + F('loses')

        ).order_by('-points', '-goals_difference', '-goals_scored')
        context['teams_stat'] = teams_stat

        return context
    
class LapsListView(LoginRequiredMixin,generic.ListView):
    model = Match
    template_name = 'football/laps_list.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        laps_list = Match.objects.values('lap').distinct()
        context['laps_list'] = laps_list
        return context

class TeamInfoView(LoginRequiredMixin,generic.DetailView):
    model = Team
    template_name = "football/team_info.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = self.object
    #    players = Player.objects.filter(team=team)
        context['goalkeepers'] = Player.objects.filter(team=team, position='gk')
        context['defenders'] = Player.objects.filter(team=team, position='df')
        context['midfielders'] = Player.objects.filter(team=team, position='mf')
        context['strikers'] = Player.objects.filter(team=team, position='st')
        return context

class LineupCreateView(PermissionRequiredMixin, CreateView):
    model = Lineup
    form_class = LineupForm
    template_name = "football/lineup_form.html"
    permission_required = ['football.add_lineup', 'football.view_lineup', 'football.view_player', 'football.view_team', 'football.view_match']

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        match = Match.objects.get(pk=self.kwargs['pk'])
        team_type = self.kwargs['team_type']
        team = match.home_team if team_type == 'home' else match.away_team
        kwargs['team'] = team
        return kwargs

    def form_valid(self, form):
        # Pobierz mecz na podstawie parametru z URL-a
        match = Match.objects.get(pk=self.kwargs['pk'])
        
        # Pobierz wybranych zawodników
        players = form.cleaned_data['players']
        
        # Pobierz drużynę (np. na podstawie team_type)
        team_type = self.kwargs.get('team_type')
        team = match.home_team if team_type == 'home' else match.away_team
        
        # Tworzenie rekordów w Lineup
        for player in players:
            Lineup.objects.create(
                match=match,
                player=player,
                team=team,
            )
        
        # Przekierowanie na sukces, bez wywoływania super().form_valid(form)
        return HttpResponseRedirect(self.get_success_url())

    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['selected_players'] = (
        list(map(int, self.request.POST.getlist('players'))) if self.request.method == 'POST' else []
        )

        match = Match.objects.get(pk=self.kwargs['pk'])
        team_type = self.kwargs['team_type']
        team = match.home_team if team_type == 'home' else match.away_team
        
        # Pobieranie zawodników według pozycji
        goalkeepers = Player.objects.filter(team=team, position='gk').order_by('name')
        defenders = Player.objects.filter(team=team, position='df').order_by('name')
        midfielders = Player.objects.filter(team=team, position='mf').order_by('name')
        strikers = Player.objects.filter(team=team, position='st').order_by('name')
        
        # Dodanie zawodników do kontekstu
        context['goalkeepers'] = goalkeepers
        context['defenders'] = defenders
        context['midfielders'] = midfielders
        context['strikers'] = strikers

        return context
    
    def get_success_url(self):
        return reverse('match_update', kwargs={'pk': self.kwargs['pk']})

class LineupUpdateView(PermissionRequiredMixin, UpdateView):
    model = Lineup
    form_class = LineupForm
    template_name = "football/lineup_form.html"
    permission_required = ['football.add_lineup', 'football.view_lineup', 'football.view_player', 'football.view_team', 'football.view_match']

    def get(self, request, *args, **kwargs):
            # Pobierz mecz na podstawie pk
        try:
            match = Match.objects.get(pk=self.kwargs['pk'])
            
            # Pobierz team_type z URL (home/away)
            team_type = self.kwargs['team_type']
            
            # W zależności od team_type przypisz drużynę
            team = match.home_team if team_type == 'home' else match.away_team
            
            # Możesz przekazać drużynę do kontekstu lub formularza
            self.team = team

            # Kontynuuj z resztą logiki
            response = super().get(request, *args, **kwargs)
            return response
        except Exception as e:
            raise e        
    
    def get_object(self):
        match = Match.objects.get(pk=self.kwargs['pk'])
        team_type = self.kwargs['team_type']
        team = match.home_team if team_type == 'home' else match.away_team
        # Znajdź pierwszy obiekt Lineup pasujący do kryteriów
        return Lineup.objects.filter(match=match, team=team).first()


    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        match = Match.objects.get(pk=self.kwargs['pk'])
        team_type = self.kwargs['team_type']
        team = match.home_team if team_type == 'home' else match.away_team
        # kwargs['team'] = team
        selected_players = Lineup.objects.filter(match=match, team=team).values_list('player', flat=True)
        # Przekaż zaznaczonych zawodników do formularza
        kwargs['initial'] = {'players': selected_players}

        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        form = self.get_form()
        context['form'] = form

        match = Match.objects.get(pk=self.kwargs['pk'])
        team_type = self.kwargs['team_type']
        team = match.home_team if team_type == 'home' else match.away_team
        
        # Pobieranie zawodników według pozycji
        goalkeepers = Player.objects.filter(team=team, position='gk').order_by('name')
        defenders = Player.objects.filter(team=team, position='df').order_by('name')
        midfielders = Player.objects.filter(team=team, position='mf').order_by('name')
        strikers = Player.objects.filter(team=team, position='st').order_by('name')
        
        # Dodanie zawodników do kontekstu
        context['goalkeepers'] = goalkeepers
        context['defenders'] = defenders
        context['midfielders'] = midfielders
        context['strikers'] = strikers

        selected_players = Lineup.objects.filter(match=match, team=team).values_list('player_id', flat=True)
        
        context['selected_players'] = selected_players

        return context
    
    def form_valid(self, form):
        # Pobierz mecz na podstawie parametru z URL-a
        match = Match.objects.get(pk=self.kwargs['pk'])
        
        # Pobierz wybranych zawodników
        players = form.cleaned_data['players']
        
        # Pobierz drużynę (np. na podstawie team_type)
        team_type = self.kwargs.get('team_type')
        team = match.home_team if team_type == 'home' else match.away_team
        

        selected_players = Lineup.objects.filter(match=match, team=team).values_list('player_id', flat=True)

        # Gracze do usunięcia
        players_to_remove = [player for player in selected_players if player not in players]
        Lineup.objects.filter(match=match, team=team, player_id__in=players_to_remove).delete()

        # Gracze do dodania
        players_to_add = [player for player in players if player not in selected_players]
        for player in players_to_add:
            Lineup.objects.create(match=match, player=player, team=team)
        
        # Przekierowanie na sukces, bez wywoływania super().form_valid(form)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('match_update', kwargs={'pk': self.kwargs['pk']})

class EventCreateView(PermissionRequiredMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = "football/event_form.html"
    permission_required = ['football.add_event', 'football.view_event']

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        match = Match.objects.get(pk=self.kwargs['pk'])  # Pobierasz mecz z URL
        kwargs['match'] = match  # Przekazujesz mecz do formularza
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        match = Match.objects.get(pk=self.kwargs['pk'])
        context['match'] = match
        context['home'] = Lineup.objects.filter(match_id=match.id, team_id=match.home_team.id)
        context['away'] = Lineup.objects.filter(match_id=match.id, team_id=match.away_team.id)
        return context

    def get_success_url(self):
        # if self.object.event_type == "substitution":
        #     return reverse('players_to_substitution', kwargs={'pk':self.object.match.pk, 'event_pk':self.object.pk})
        # else:
            return reverse('players_to_event', kwargs={'pk':self.object.match.pk, 'event_pk':self.object.pk})
            
class TeamCreateEventView(PermissionRequiredMixin, generic.FormView):
    model = Event
    form_class = TeamCreateEventForm
    template_name ="football/players_to_event.html"
    permission_required = ['football.edit_event',
                           'football.view_player',
                           'football.add_lineup',
                           'football.edit_lineup',
                           'football.add.substitution']

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['initial'] = {'pk': self.kwargs['pk']}  # Przekazanie ID meczu jako initial
        event = Event.objects.get(pk=self.kwargs['event_pk'])
        players_in_match = Lineup.objects.filter(
            match_id=self.kwargs['pk'],
            team=event.team,  
            on_bench=False
        )
        red_cards = Event.objects.filter(match_id=self.kwargs['pk'], event_type="red_card").values_list('player_id')
        # kwargs['red_card'] = red_cards
        kwargs['players_in_match'] = players_in_match
        kwargs['event_type'] = event.event_type
        if event.event_type == "substitution":
            players_active_in_match = Lineup.objects.filter(
                match_id=self.kwargs['pk'],
                team=event.team,
            ).values_list('player_id', flat=True)
            players_on_bench = Player.objects.filter(
                team=event.team,  
            ).exclude(Q(id__in=players_active_in_match)|Q(id__in=red_cards))
            kwargs["players_on_bench"] = players_on_bench
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        match = Match.objects.get(pk=self.kwargs['pk'])
        context['match']=match
        event = Event.objects.get(pk=self.kwargs['event_pk'])
        context['event']=event
        players_in_match = Lineup.objects.filter(match=match, team=event.team, on_bench=False).values_list('player_id', flat=True)
        context['player_in_match'] = players_in_match
        context['team']=event.team
        if event.event_type == "substitution":
            players_active_in_match = Lineup.objects.filter(
                match_id=self.kwargs['pk'],
                team=event.team,  
            ).values_list('player_id', flat=True)
            players_on_bench = Player.objects.filter(
                team=event.team,  
            ).exclude(id__in=players_active_in_match)
            context['players_on_bench']=players_on_bench 
        return context

    def form_valid(self, form):
        event_pk = self.kwargs['event_pk']
        player = form.cleaned_data['player']
        Event.objects.filter(pk=event_pk).update(player=player)
        event = Event.objects.get(pk=event_pk)
        if event.event_type == "substitution":
            player_in=form.cleaned_data['player_in']
            Substitution.objects.create(event=event, player_in=player_in)
            Lineup.objects.filter(
                match=event.match,
                player=player
                ).update(on_bench=True)
            Lineup.objects.create(
                match=event.match, 
                team=event.team, 
                player=player_in, 
                is_starting=False
                )
        if event.event_type == "red_card":
                Lineup.objects.filter(
                match=event.match,
                player=player
                ).update(on_bench=True)
        return super().form_valid(form)

    def form_invalid(self, form):
        print("Form is invalid")
        print("Errors:", form.errors)
        return super().form_invalid(form)
    
    def get_success_url(self):
        return reverse('match_update', kwargs={'pk': self.kwargs['pk']})
    
class MatchDetailsView(LoginRequiredMixin,generic.DetailView):
    model = Match
    template_name = "football/match_details.html"

    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        current_match = Match.objects.get(pk=self.kwargs['pk'])
        home_team = Lineup.objects.filter(match_id = self.kwargs['pk'], team = current_match.home_team)
        away_team = Lineup.objects.filter(match_id = self.kwargs['pk'], team = current_match.away_team)
        events = Event.objects.filter(match_id = self.kwargs['pk'])
        context['current_match'] = current_match
        home = [[lineup.player.name,[event for event in events if event.player == lineup.player]] for lineup in home_team]
        away = [[lineup.player.name,[event for event in events if event.player == lineup.player]] for lineup in away_team]
            # for player, events in home:
            #     if player.is_startnig == False:
            #         pass #docelowo wpisać zawodników wchodzących    ZOSTAWIĆ

        context['home_team'] = home_team
        context['away_team'] = away_team
        context['home'] = home
        context['away'] = away
        return context