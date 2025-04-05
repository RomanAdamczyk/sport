import pytest
from django.urls import reverse
from football.models import Team, Match
from datetime import date
from model_bakery import baker
from django.urls.exceptions import NoReverseMatch
# from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import Permission, User, Group
from django.core.exceptions import ValidationError



@pytest.fixture
def login_user(db,client):
    user = baker.make("auth.User")
    client.force_login(user)
    return client

@pytest.fixture
def moderator_user(db, client):

    user = baker.make("auth.User")
    group = baker.make ("auth.Group", name="Moderatorzy")   

    permission_view_match = Permission.objects.get(codename="view_match")
    permission_add_match = Permission.objects.get(codename="add_match")
    permission_change_match = Permission.objects.get(codename="change_match")
    permission_delete_match = Permission.objects.get(codename="delete_match")
    group.permissions.add(permission_view_match, permission_add_match, permission_change_match, permission_delete_match)

    user.groups.add(group)

    client.force_login(user)
    return client, user

@pytest.mark.django_db
class TestIndexView():
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
class TestTeamMatchesView():
    def test_team_matches_view_without_authorization(self,client):
        """ sprawdza, czy przekierowuje użytkownika bez autoryzacji"""
        url = reverse('team_matches',kwargs={'pk': 1})
        response = client.get(url)

        assert response.status_code == 302

    def test_team_matches_view_with_authorization(self,login_user):
        """ sprawdza, czy łączy się ze stroną z meczami danej drużyny"""
        team = baker.make("football.Team", id=1)
        team1 = baker.make("football.Team")
        team2 = baker.make("football.Team")
        game1 = baker.make("football.Match", home_team = team, away_team=team1, lap=1)
        game2 = baker.make("football.Match", home_team = team2, away_team=team, lap=2)
        url = reverse('team_matches',kwargs={'pk': 1})
        response = login_user.get(url)

        assert response.status_code == 200
        assert team.name in response.content.decode()
        assert team1.name in response.content.decode()
        assert team2.name in response.content.decode()
        
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
        """Sprawdza, czy wyrzuca wyjątek, gdy w URL brakuje ID drużyny"""
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

    def test_team_matches_view_with_authorization_without_permission(self,login_user):
        """ sprawdza, czy łączy się ze stroną z meczami danej drużyny"""
        team = baker.make("football.Team", id=1)
        team1 = baker.make("football.Team")
        game1 = baker.make("football.Match", home_team = team, away_team=team1, lap=1)
        url = reverse('team_matches',kwargs={'pk': 1})
        response = login_user.get(url)

        assert response.status_code == 200
        assert "szczegóły" in response.content.decode()
        assert "usuń" not in response.content.decode()
        assert "popraw" not in response.content.decode()

    def test_team_matches_view_with_permission(self,moderator_user):
        """ sprawdza, czy łączy się ze stroną z meczami danej drużyny"""
        team = baker.make("football.Team", id=1)
        team1 = baker.make("football.Team")
        game1 = baker.make("football.Match", home_team = team, away_team=team1, lap=1)
        url = reverse('team_matches',kwargs={'pk': 1})
        client, user = moderator_user
        response = client.get(url)

        assert response.status_code == 200
        assert "szczegóły" in response.content.decode()
        assert "usuń" in response.content.decode()
        assert "popraw" in response.content.decode()


@pytest.mark.django_db
class TestLapView():

    def test_lap_view_without_authorization(self,client):
        """ sprawdza, czy przekierowuje użytkownika bez autoryzacji"""
        url = reverse('lap',kwargs={'pk': 1})
        response = client.get(url)

        assert response.status_code == 302

    def test_team_matches_view_with_authorization(self,login_user):
        """ sprawdza, czy łączy się ze stroną z meczami danej kolejki"""
        team = baker.make("football.Team", _quantity=4)
        game1 = baker.make("football.Match", home_team = team[0], away_team=team[1], lap=1)
        game2 = baker.make("football.Match", home_team = team[2], away_team=team[3], lap=1)
        url = reverse('lap',kwargs={'pk': 1})
        response = login_user.get(url)

        assert response.status_code == 200
        assert team[0].name in response.content.decode()
        assert team[1].name in response.content.decode()
        assert team[2].name in response.content.decode()
        assert team[3].name in response.content.decode()
        assert Match.objects.filter(lap=1).count() == 2

    def test_lap_view_uses_correct_template(self,login_user):
        """Sprawdza, czy poprawnie wybiera templates"""

        team = baker.make("football.Team", _quantity=2)
        game1 = baker.make("football.Match", home_team = team[0], away_team=team[1], lap=1)
        url = reverse('lap',kwargs={'pk': 1})
        response = login_user.get(url)

        assert 'football/lap.html' in [t.name for t in response.templates]

    def test_lap_view_missing_pk(self, login_user):
        """Sprawdza, czy wyrzuca wyjątek, gdy w URL brakuje ID drużyny"""
        with pytest.raises(NoReverseMatch):
            url = reverse('lap') 
            response = client.get(url)

    def test_lap_view_with_moderator_role(self, client):
        """Sprawdza, czy moderator ma dostęp do meczu drużyny"""
        user = baker.make("auth.User", is_staff=True)
        game = baker.make("football.Match", lap=1)
        client.force_login(user)

        url = reverse('lap', kwargs={'pk': 1})
        response = client.get(url)

        assert response.status_code == 200
            
@pytest.mark.django_db
class TestMatchCreateView():
    def test_match_create_view_without_authorization(self,client):
        """ sprawdza, czy przekierowuje użytkownika bez autoryzacji"""
        url = reverse('lap',kwargs={'pk': 1})
        response = client.get(url)

        assert response.status_code == 302

    def test_match_create_view_without_permission(self,login_user):
        """sprawdzam czy tworzony jest nowy mecz"""

        team = baker.make("football.Team", _quantity=2)
        game_data = {
            'lap':1,
            'date': date(2025,4,2),
            'home_team': team[0].id,
            'away_team': team[1].id,
            'home_score': 3,
            'away_score': 0
            }
        games_count = Match.objects.count()

        url = reverse('match_create')
        response = login_user.post(url, data=game_data)
        # with pytest.raises(PermissionDenied):
        game = Match.objects.last()
        assert response.status_code == 403

    def test_match_create_view_with_permission(self,moderator_user):
        """sprawdzam czy tworzony jest nowy mecz"""

        team = baker.make("football.Team", _quantity=2)
        game_data = {
            'lap':1,
            'date': date(2025,4,2),
            'home_team': team[0].id,
            'away_team': team[1].id,
            'home_score': 3,
            'away_score': 0
            }
        games_count = Match.objects.count()

        url = reverse('match_create')
        client, user = moderator_user
        response = client.post(url, data=game_data)

        game = Match.objects.last()
        assert response.status_code == 302
        assert Match.objects.count() == games_count + 1
        assert game.home_team == team[0]
        assert game.away_team == team[1]
        assert game.home_score == 3
        assert game.away_score == 0


    def test_match_create_view_with_the_same_teams(self,moderator_user):
        """sprawdzam czy tworzony jest nowy mecz z tymi samymi drużynami"""

        team = baker.make("football.Team")
        game_data = {
            'lap':1,
            'date': date(2025,4,2),
            'home_team': team.id,
            'away_team': team.id,
            'home_score': 3,
            'away_score': 0
            }
        
        url = reverse('match_create')
        client, user = moderator_user
        games_count = Match.objects.count()
        response = client.post(url, data=game_data)
        
        assert games_count == Match.objects.count()
        assert response.status_code == 200
        assert 'form' in response.context #sprawdza, czy obiekt formularza (form) został przekazany do kontekstu szablonu
        assert 'away_team' in response.context['form'].errors #sprawdza, czy pole away_team ma błąd walidacji

    def test_match_create_view_with_wrong_home_score(self,moderator_user):
        """sprawdzam czy tworzony jest nowy mecz z błędną ilością bramek gospodarza"""

        team = baker.make("football.Team", _quantity=2)
        game_data = {
            'lap':1,
            'date': date(2025,4,2),
            'home_team': team[0].id,
            'away_team': team[1].id,
            'home_score': -3,
            'away_score': 0
            }
        
        url = reverse('match_create')
        client, user = moderator_user
        games_count = Match.objects.count()
        response = client.post(url, data=game_data)
        
        assert games_count == Match.objects.count()
        assert response.status_code == 200
        assert 'form' in response.context #sprawdza, czy obiekt formularza (form) został przekazany do kontekstu szablonu
        assert 'home_score' in response.context['form'].errors #sprawdza, czy pole home_score ma błąd walidacji

    def test_match_create_view_with_wrong_away_score(self,moderator_user):
        """sprawdzam czy tworzony jest nowy mecz z błędną ilością bramek gości"""

        team = baker.make("football.Team", _quantity=2)
        game_data = {
            'lap':1,
            'date': date(2025,4,2),
            'home_team': team[0].id,
            'away_team': team[1].id,
            'home_score': 3,
            'away_score': -1
            }
        
        url = reverse('match_create')
        client, user = moderator_user
        games_count = Match.objects.count()
        response = client.post(url, data=game_data)
        
        assert games_count == Match.objects.count()
        assert response.status_code == 200
        assert 'form' in response.context #sprawdza, czy obiekt formularza (form) został przekazany do kontekstu szablonu
        assert 'away_score' in response.context['form'].errors #sprawdza, czy pole away_score ma błąd walidacji

    def test_match_create_view_with_wrong_lap(self,moderator_user):
        """sprawdzam czy tworzony jest nowy mecz z błędnym numerem kolejki"""

        team = baker.make("football.Team", _quantity=2)
        game_data = {
            'lap':0,
            'date': date(2025,4,2),
            'home_team': team[0].id,
            'away_team': team[1].id,
            'home_score': 3,
            'away_score': 1
            }
        
        url = reverse('match_create')
        client, user = moderator_user
        games_count = Match.objects.count()
        response = client.post(url, data=game_data)
        
        assert games_count == Match.objects.count()
        assert response.status_code == 200
        assert 'form' in response.context #sprawdza, czy obiekt formularza (form) został przekazany do kontekstu szablonu
        assert 'lap' in response.context['form'].errors #sprawdza, czy pole lap ma błąd walidacji

    def test_match_create_view_with_wrong_date(self,moderator_user):
        """sprawdzam czy tworzony jest nowy mecz z błędną datą"""

        team = baker.make("football.Team", _quantity=2)
        game_data = {
            'lap':0,
            'date': "202",
            'home_team': team[0].id,
            'away_team': team[1].id,
            'home_score': 3,
            'away_score': -1
            }
        
        url = reverse('match_create')
        client, user = moderator_user
        games_count = Match.objects.count()
        response = client.post(url, data=game_data)
        
        assert games_count == Match.objects.count()
        assert response.status_code == 200
        assert 'form' in response.context #sprawdza, czy obiekt formularza (form) został przekazany do kontekstu szablonu
        assert 'date' in response.context['form'].errors #sprawdza, czy pole date ma błąd walidacji

    def test_match_create_view_with_missing_data(self,moderator_user):
        """sprawdzam czy tworzony jest nowy mecz z błędnym numerem kolejki"""

        team = baker.make("football.Team", _quantity=2)
        game_data = {
            'lap':0,
            'date': date(2025,4,2),
            'home_team': team[0].id,
            'away_team': team[1].id,
            'away_score': -1
            }
        
        url = reverse('match_create')
        client, user = moderator_user
        games_count = Match.objects.count()
        with pytest.raises(TypeError):
            response = client.post(url, data=game_data)
        assert games_count == Match.objects.count()

    def test_form_display_contains_all_fields(client, moderator_user):
        """ Sprawdzam czy szablon zawiera formularz (`<form>`) i wszystkie wymagane pola"""

        client, _ = moderator_user
        url = reverse('match_create')
        response = client.get(url)

        assert response.status_code == 200
        assert b'<form' in response.content
        assert b'name="home_team"' in response.content
        assert b'name="away_team"' in response.content
        assert b'name="lap"' in response.content
        assert b'type="submit"' in response.content

@pytest.mark.django_db
class TestRegisterView():
    def test_register_view_renders_form(self,client):
        """Sprawdzam poprawność przesłanego formularza"""

        url = reverse('register')
        response = client.get(url)

        assert response.status_code == 200
        assert b'<form' in response.content  # Sprawdza czy formularz jest w HTML
        assert b'name="username"' in response.content  # Sprawdza czy pole dla username jest obecne
        assert b'name="password1"' in response.content  # I dla hasła
        assert b'name="password2"' in response.content  # I dla drugiego hasła (potwierdzenie)

    def test_register_view_creates_user_and_adds_to_group(self,client):
        """Sprawdzam poprawność rejestracji i dodawania do grupy"""
        url = reverse('register')
        data = {
            'username': 'testuser',
            'password1': 'TestPassword123',
            'password2': 'TestPassword123',
        }

        user_count = User.objects.count()

        response = client.post(url, data=data)

        # Sprawdzanie, czy użytkownik został zapisany
        user = User.objects.get(username='testuser')
        assert user is not None

        assert user_count + 1 == User.objects.count()

        # Sprawdzanie, czy użytkownik jest dodany do grupy
        default_group = Group.objects.get(name='Uzytkownicy')
        assert default_group in user.groups.all()

        # Sprawdzanie przekierowania na stronę 'index'
        assert response.status_code == 302  # Sprawdzenie, czy przekierowuje
        assert response.url == reverse('index')  # Sprawdzenie, czy przekierowanie jest na stronę główną

    def test_register_view_invalid_password2(self,client):
        """Sprawdzam poprawność rejestracji przy błędnym drugim haśle"""
        
        url = reverse('register')
        user_data = {
            'username': 'testuser',
            'password1': 'TestPassword123',
            'password2': 'WrongPassword123',
        }

        user_count = User.objects.count()
        response = client.post(url, data=user_data)
        assert response.status_code == 200  # Formularz nadal jest renderowany
        assert user_count == User.objects.count()
        
        
        # print(response.content)
        # response_content = response.content.decode('utf-8')
        # print(response_content)
        # Sprawdzenie, czy formularz nie jest poprawny
        # response_content = response.content.decode('utf-8')  # Dekodujemy zawartość na stringa w UTF-8
        # assert b'Hasła muszą być identyczne' in str(response.context['form'].errors)  # Sprawdzamy błąd dotyczący hasła

    def test_register_view_logs_in_user(self, client):
        """Sprawdzam czy użytkownik jest zalogowany po rejestracji"""
        url = reverse('register')
        user_data = {
            'username': 'testuser',
            'password1': 'TestPassword123',
            'password2': 'TestPassword123',
        }

        response = client.post(url, data=user_data)

        # Sprawdzanie, czy użytkownik jest zalogowany
        user = User.objects.get(username='testuser')
        assert user.is_authenticated  # Sprawdzenie, czy użytkownik jest zalogowany

    def test_register_view_short_password(self, client):
        """Sprawdzam czy użytkownik jest zalogowany po rejestracji"""
        url = reverse('register')
        user_data = {
            'username': 'testuser',
            'password1': '1',
            'password2': '1',
        }
        user_count = User.objects.count()
        response = client.post(url, data=user_data)
        
        assert response.status_code == 200  # Formularz nadal jest renderowany
        assert user_count == User.objects.count()

