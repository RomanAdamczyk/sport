import pytest
from football.models import Team
from django.db import IntegrityError

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
        # with pytest.raises(IntegrityError):
        team =Team.objects.create(city='Test City', founded='2020-01-01')
        assert team.city == 'Test City'

    def test_team_without_city(self):
        # with pytest.raises(IntegrityError):
        team = Team.objects.create(name='Test Team', founded='2020-01-01')
        assert team.name == "Test Team"
      

    def test_team_without_founded(self):
        with pytest.raises(IntegrityError):
            Team.objects.create(name='Test Team', city='Test City')

