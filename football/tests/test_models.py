import pytest
from unittest.mock import MagicMock
from django.forms import ValidationError
from django.db import IntegrityError
from football.models import Team
from football.models import Team, Match 
from datetime import date

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

        match = Match.objects.create(
            home_team=home_team,
            away_team=away_team,
            date=date(2025,3,23),
            home_score=2,
            away_score=1,
            lap=1
        )

        assert match.home_team == home_team
        assert match.away_team == away_team
        assert match.date == date(2025, 3, 23)
        assert match.home_score == 2
        assert match.away_score == 1
        assert match.lap == 1
        assert str(match) == "TestTeam A vs TestTeam B"

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
                date="2025-02-30",
                home_score=2,
                away_score=1,
                lap=1
            )


    def test_match_create_invalid_score(self):

        home_team = Team.objects.create(name="TestTeam A", founded="1964-02-27")  
        away_team = Team.objects.create(name="TestTeam B", founded="1964-01-01")  

        # with pytest.raises(ValidationError):
        match = Match.objects.create(
                home_team=home_team,
                away_team=away_team,
                date="2025-02-23",
                home_score=-2,
                away_score=1,
                lap=1
            )
        with pytest.raises(ValidationError):
            match.clean()

    def test_match_create_invalid_lap(self):

        home_team = Team.objects.create(name="TestTeam A", founded="1964-02-27")  
        away_team = Team.objects.create(name="TestTeam B", founded="1964-01-01")  

        # with pytest.raises(ValidationError):
        match = Match.objects.create(
                home_team=home_team,
                away_team=away_team,
                date="2025-02-23",
                home_score=2,
                away_score=1,
                lap=0
            )
        with pytest.raises(ValidationError):
            match.clean()


    def test_match_create_the_same_teams(self):

        home_team = Team.objects.create(name="TestTeam A", founded="1964-02-27")  

        # with pytest.raises(ValidationError):
        match = Match.objects.create(
                home_team=home_team,
                away_team=home_team,
                date="2025-02-23",
                home_score=2,
                away_score=1,
                lap=1
            )
        with pytest.raises(ValidationError):
            match.clean()