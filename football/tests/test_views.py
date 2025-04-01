import pytest
from django.urls import reverse
from football.models import Team, Match
from datetime import date
from model_bakery import baker
from django.urls.exceptions import NoReverseMatch

@pytest.fixture
def login_user(db,client):
    user = baker.make("auth.User")
    client.force_login(user)
    return client

@pytest.mark.django_db
class TestIndex():
    def test_index_view(self, client):
        """ sprawdza, czy dobrze wyświetlana jest strona główna"""
        url = reverse('index')
        response = client.get(url)
        
        assert response.status_code == 200

    def test_index_uses_correct_template(self, client):
        url = reverse('index')
        response = client.get(url)

        assert 'football/index.html' in [t.name for t in response.templates]

    def test_index_context(self,client):
        Team.objects.create(name="TeastTeam", founded = date(1964,1,1))
        url = reverse('index')
        response = client.get(url)
        assert 'object_list' in response.context 

@pytest.mark.django_db
class TestTeamMatches():
    def test_team_matches_view_without_authorization(self,client):
        """ sprawdza, czy przekierowuje użytkownika bez autoryzacji"""
        url = reverse('team_matches',kwargs={'pk': 1})
        response = client.get(url)

        assert response.status_code == 302

    def test_team_matches_view_with_authorization(self,login_user):
        """ sprawdza, czy łączy się ze stroną z meczami danej drużyny"""
        team = baker.make("football.Team", id=1)
        url = reverse('team_matches',kwargs={'pk': 1})
        response = login_user.get(url)

        assert response.status_code == 200
        assert team.name in response.content.decode()
        
    def test_team_matches_uses_correct_template(self,login_user):
        """Sprawdza, czy poprawnie wybiera templates"""
        
        team = baker.make("football.Team", id=1)
        url = reverse('team_matches',kwargs={'pk': 1})
        response = login_user.get(url)

        assert 'football/team_matches.html' in [t.name for t in response.templates]

    def test_team_matches_view_team_not_found(self,login_user):
        """Sprawdza, czy zwracane jest 404 dla drużyny, która nie istnieje"""

        url = reverse('team_matches', kwargs={'pk': 1})
        response = login_user.get(url)

        assert response.status_code == 404

    def test_team_matches_view_team_invalid_id(self,login_user):
        """Sprawdza, czy wyrzucany jest wyjątek przy nieprawdłowym formacie ID"""
       
        with pytest.raises(NoReverseMatch):
            url = reverse('team_matches', kwargs={'pk': 'ab'})
            response = login_user.get(url)

    def test_team_matches_view_missing_pk(self, login_user):
        """Sprawdza, co się dzieje, gdy w URL brakuje ID drużyny"""
        with pytest.raises(NoReverseMatch):
            url = reverse('team_matches') 
            response = client.get(url)


    def test_team_matches_view_with_moderator_role(self, client):
        """Sprawdza, czy moderator ma dostęp do meczu drużyny"""
        user = baker.make("auth.User", is_staff=True)
        team = baker.make("football.Team", id=1)
        client.force_login(user)

        url = reverse('team_matches', kwargs={'pk': team.pk})
        response = client.get(url)

        assert response.status_code == 200

