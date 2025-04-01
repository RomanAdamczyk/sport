import pytest
from unittest.mock import MagicMock
from django.forms import ValidationError
from django.db import IntegrityError
from football.models import Team, Match, Player, Lineup, Event, Substitution
from datetime import date
from model_bakery import baker

@pytest.fixture
def match_data(db):
    home_team = baker.make('football.Team', name="Test Team A")
    away_team = baker.make('football.Team', name="Test Team B")
    game = baker.make('football.Match', home_team=home_team, away_team=away_team)
    return game


@pytest.mark.django_db
class TestTeam():
    
    def test_team_create_without_stadium(self):
        team = Team.objects.create(name='Test Team', city='Test City', founded='2020-01-01')
        assert team.name == 'Test Team'
        assert team.city == 'Test City'
        assert team.founded == '2020-01-01'

    def test_team_create_with_stadium(self):
        team = Team.objects.create(name='Test Team', city='Test City', founded='2020-01-01', stadium='Test Stadium')
        assert team.name == 'Test Team'
        assert team.city == 'Test City'
        assert team.founded == '2020-01-01'
        assert team.stadium == 'Test Stadium'

    def test_team_empty_stadium(self):
        team = Team.objects.create(name='Test Team', city='Test City', founded='2020-01-01', stadium='')
        assert team.stadium == ''

    def test_team_str(self):
        team = Team.objects.create(name='Test Team', city='Test City', founded='2020-01-01')
        assert str(team) == 'Test Team'

    def test_team_without_name(self):
        team = Team(city='Test City', founded='2020-01-01')
        with pytest.raises(ValidationError):
            team.full_clean()
            team.save()

    def test_team_without_city(self):
        team = Team(name='Test Team', founded='2020-01-01')
        with pytest.raises(ValidationError):
            team.full_clean()
            team.save()
      

    def test_team_without_founded(self):
        with pytest.raises(IntegrityError):
            Team.objects.create(name='Test Team', city='Test City')

@pytest.mark.django_db
class TestMatch():

    def test_match_create(self):
        
        home_team = Team.objects.create(name="TestTeam A", founded="1964-02-27")  
        away_team = Team.objects.create(name="TestTeam B", founded="1964-01-01")  

        game = Match.objects.create(
            home_team=home_team,
            away_team=away_team,
            date=date(2025,3,23),
            home_score=2,
            away_score=1,
            lap=1
        )

        assert game.home_team == home_team
        assert game.away_team == away_team
        assert game.date == date(2025, 3, 23)
        assert game.home_score == 2
        assert game.away_score == 1
        assert game.lap == 1
        assert str(game) == "TestTeam A vs TestTeam B"

    def test_match_create_empty_fields(self):
        with pytest.raises(IntegrityError):
            Match.objects.create(
                home_team=None,
                away_team=None,
                date=date(2025,3,23),
                home_score=2,
                away_score=1,
                lap=1
            )

    def test_match_create_without_fields(self):
        home_team = Team.objects.create(name="TestTeam A", founded="1964-02-27")  
        away_team = Team.objects.create(name="TestTeam B", founded="1964-01-01")  

        with pytest.raises(IntegrityError):
            Match.objects.create(
                home_team=home_team,
                away_team=away_team,
                date=date(2025,3,23),
                home_score=2,
                away_score=1,
            )

    def test_match_create_invalid_date(self):

        home_team = Team.objects.create(name="TestTeam A", founded="1964-02-27")  
        away_team = Team.objects.create(name="TestTeam B", founded="1964-01-01")  

        with pytest.raises(ValidationError):
            Match.objects.create(
                home_team=home_team,
                away_team=away_team,
                date="2025;02;23",
                home_score=2,
                away_score=1,
                lap=1
            )


    def test_match_create_invalid_home_score(self):

        home_team = Team.objects.create(name="TestTeam A", founded="1964-02-27")  
        away_team = Team.objects.create(name="TestTeam B", founded="1964-01-01")  

        # with pytest.raises(ValidationError):
        game = Match.objects.create(
                home_team=home_team,
                away_team=away_team,
                date="2025-02-23",
                home_score=-2,
                away_score=1,
                lap=1
            )
        with pytest.raises(ValidationError):
            game.clean()

    def test_match_create_invalid_away_score(self):

        home_team = Team.objects.create(name="TestTeam A", founded="1964-02-27")  
        away_team = Team.objects.create(name="TestTeam B", founded="1964-01-01")  

        # with pytest.raises(ValidationError):
        game = Match.objects.create(
                home_team=home_team,
                away_team=away_team,
                date="2025-02-23",
                home_score=2,
                away_score=-1,
                lap=1
            )
        with pytest.raises(ValidationError):
            game.clean()


    def test_match_create_invalid_lap(self):

        home_team = Team.objects.create(name="TestTeam A", founded="1964-02-27")  
        away_team = Team.objects.create(name="TestTeam B", founded="1964-01-01")  

        # with pytest.raises(ValidationError):
        game = Match.objects.create(
                home_team=home_team,
                away_team=away_team,
                date="2025-02-23",
                home_score=2,
                away_score=1,
                lap=0
            )
        with pytest.raises(ValidationError):
            game.clean()


    def test_match_create_the_same_teams(self):

        home_team = Team.objects.create(name="TestTeam A", founded="1964-02-27")  

        # with pytest.raises(ValidationError):
        game = Match.objects.create(
                home_team=home_team,
                away_team=home_team,
                date="2025-02-23",
                home_score=2,
                away_score=1,
                lap=1
            )
        with pytest.raises(ValidationError):
            game.clean()

@pytest.mark.django_db
class TestPlayer():

    def test_player_create(self):
        team = Team.objects.create(name="TestTeam", founded="1964-02-27")

        player = Player.objects.create(
            team = team,
            name = 'test name',
            birth_day = date(2000,1,1),
            position = 'gk',
            nationality = 'Polska'
        )      
    
        assert player.team == team
        assert player.name == 'test name'
        assert player.birth_day == date(2000,1,1)
        assert player.position == 'gk'
        assert player.nationality == 'Polska'
        assert str(player) == 'test name (TestTeam) - bramkarz - Polska - 2000-01-01'

    def test_player_create_with_empty_team(self):
        
        player = Player.objects.create(
            team = None,
            name = 'test name',
            birth_day = date(2000,1,1),
            position = 'gk',
            nationality = 'Polska'
        )      

        assert player.team == None

    def test_player_create_with_wrong_position(self):
        
        player = Player.objects.create(
            team = None,
            name = 'test name',
            birth_day = date(2000,1,1),
            position = 'gl',
            nationality = 'Polska'
        )      

        with pytest.raises(ValidationError):
            player.full_clean() 
            player.save()

@pytest.mark.django_db
class TestLineup():
    def test_create_starting_lineup(self, match_data):
        lineup = baker.make(
            'football.Lineup',
            player__name = "Test Player",
            team = match_data.home_team,
            match = match_data,
            is_starting = True
        )
        assert str(lineup) == "Test Player (Starting) - Test Team A in Test Team A vs Test Team B"

    def test_create_substitute_lineup(self,match_data):
        lineup = baker.make(
            'football.Lineup',
            player__name = "Test Player",
            team = match_data.home_team,
            match = match_data,
            is_starting = False
        )
        assert str(lineup) == "Test Player (Substitute) - Test Team A in Test Team A vs Test Team B"

@pytest.mark.django_db
class TestEvents():
    
    def test_event_creation(self,match_data):
        event = baker.make(
            'football.Event',
            match = match_data,
            event_type='goal',
            team = match_data.home_team,
            minute = 60 )
        assert str(event) == 'Bramka - Test Team A vs Test Team B (60 min)'

    def test_event_creation_unvalid_type(self,match_data):
        event = baker.make(
            'football.Event',
            match = match_data,
            event_type='goaljj',
            team = match_data.home_team,
            minute = 60 )

        with pytest.raises(ValidationError):  # Spodziewamy się błędu
            event.full_clean()

@pytest.mark.django_db
class TestSubstitution():

    def test_create_substitution(self,match_data):
        event = baker.make('football.Event',
            match = match_data,
            player__name='Test Player Out',
            event_type='substitution',
            team=match_data.home_team,
            minute = 50)

        substitution = baker.make('football.Substitution', event=event, player_in__name='Test Player In')

        assert str(substitution) == 'Test Player In za Test Player Out z Test Team A 50 mecz: Test Team A vs Test Team B'

@pytest.mark.django_db
class TestRelations():

    def test_count_of_players_in_team(self):
        team = Team.objects.create(name="TestTeam", founded=date(1964,2,27))
        assert team.player_set.count() == 0

        player1 = Player.objects.create(
            team = team,
            name = 'test name A',
            birth_day = date(2000,1,1),
            position = 'gk',
            nationality = 'Polska'
        ) 
        assert team.player_set.all().count() == 1

        player2 = Player.objects.create(
            team = team,
            name = 'test name B',
            birth_day = date(2000,3,1),
            position = 'gk',
            nationality = 'Polska'
        ) 
        assert team.player_set.all().count() == 2

    def test_match_count_for_team(self):
        team = Team.objects.create(name="TestTeam A", founded=date(1964,2,27))
        team2 = Team.objects.create(name="TestTeam C", founded=date(1964,2,27))

        assert team.home_matches.count() == 0

        team2 = Team.objects.create(name="TestTeam C", founded=date(1964,2,27))
        game = Match.objects.create(
                home_team=team,
                away_team=team2,
                date="2025-02-23",
                home_score=2,
                away_score=1,
                lap=1
            )

        assert team.home_matches.count() == 1