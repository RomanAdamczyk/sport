import pytest
from django.urls import reverse
from football.models import Team, Match, Player, Lineup
from datetime import date
from model_bakery import baker
from faker import Faker
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
    permission_view_lineup = Permission.objects.get(codename="view_lineup")
    permission_add_lineup = Permission.objects.get(codename="add_lineup")
    permission_change_lineup = Permission.objects.get(codename="change_lineup")
    permission_delete_lineup = Permission.objects.get(codename="delete_lineup")
    permission_view_team = Permission.objects.get(codename="view_team")
    permission_view_player = Permission.objects.get(codename="view_player")
    group.permissions.add(permission_view_match, permission_add_match, permission_change_match, permission_delete_match,
                          permission_view_lineup, permission_add_lineup, permission_change_lineup, permission_delete_lineup,
                          permission_view_team,
                          permission_view_player)

    user.groups.add(group)

    client.force_login(user)
    return client, user

@pytest.fixture
def team(db):
    return baker.make("football.Team", _quantity=2)

@pytest.fixture
def single_team(db):
    return baker.make("football.Team")

@pytest.fixture
def game(team):
    return baker.make("football.Match",
        lap= 1,
        date= date(2025, 4, 2),
        home_team= team[0],
        away_team= team[1],
        home_score= 3,
        away_score= 0
    )

@pytest.fixture
def game_data(team):
    return {
        'lap': 1,
        'date': date(2025, 4, 2),
        'home_team': team[0].id,
        'away_team': team[1].id,
        'home_score': 3,
        'away_score': 0
    }

@pytest.fixture
def lineup(game, team_type):
    """Tworzy lineup dla drużyny na podstawie team_type"""
    team = game.home_team if team_type == 'home_team' else game.away_team
    players = [baker.make('football.Player', team=team) for _ in range(11)]
    lineups = []
    for player in players:
        lineup = baker.make('football.Lineup', match=game, team=team, player=player, is_starting=True, on_bench=False)
        lineups.append(lineup)
    
    return lineups

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

    def test_index_context(self,client,team):
        teams = team
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

    def test_team_matches_view_with_authorization(self,login_user,team,game):
        """ sprawdza, czy łączy się ze stroną z meczami danej drużyny"""
        url = reverse('team_matches',kwargs={'pk': team[0].id})
        response = login_user.get(url)

        assert response.status_code == 200
        assert team[0].name in response.content.decode()
        assert team[1].name in response.content.decode()
        
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

    def test_team_matches_view_with_authorization_without_permission(self,login_user,team,game):
        """ sprawdza, czy łączy się ze stroną z meczami danej drużyny"""
        url = reverse('team_matches',kwargs={'pk': team[0].id})
        response = login_user.get(url)

        assert response.status_code == 200
        assert "szczegóły" in response.content.decode()
        assert "usuń" not in response.content.decode()
        assert "popraw" not in response.content.decode()

    def test_team_matches_view_with_permission(self,moderator_user,team, game):
        """ sprawdza, czy łączy się ze stroną z meczami danej drużyny"""
        url = reverse('team_matches',kwargs={'pk': team[0].id})
        client, _ = moderator_user
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

    def test_lap_view_with_authorization(self,login_user,team, game):
        """ sprawdza, czy łączy się ze stroną z meczami danej kolejki"""
        if len(team) < 4:
            teams = baker.make("football.Team", _quantity=2)
        game2 = baker.make(
            "football.Match",
            lap=1,
            date=date(2025, 4, 2),
            home_team=teams[0],
            away_team=teams[1],
            home_score=3,
            away_score=0
        )
        url = reverse('lap',kwargs={'pk': 1})
        response = login_user.get(url)

        assert response.status_code == 200
        assert team[0].name in response.content.decode()
        assert team[1].name in response.content.decode()
        assert teams[0].name in response.content.decode()
        assert teams[1].name in response.content.decode()
        assert Match.objects.filter(lap=1).count() == 2

    def test_lap_view_uses_correct_template(self,login_user,game):
        """Sprawdza, czy poprawnie wybiera templates"""

        url = reverse('lap',kwargs={'pk': 1})
        response = login_user.get(url)

        assert 'football/lap.html' in [t.name for t in response.templates]

    def test_lap_view_missing_pk(self, login_user):
        """Sprawdza, czy wyrzuca wyjątek, gdy w URL brakuje ID drużyny"""
        with pytest.raises(NoReverseMatch):
            url = reverse('lap') 
            response = client.get(url)

    def test_lap_view_with_moderator_role(self, client,game):
        """Sprawdza, czy moderator ma dostęp do meczu drużyny"""
        user = baker.make("auth.User", is_staff=True)
        
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

    def test_match_create_view_without_permission(self,login_user,game_data):
        """sprawdzam czy tworzony jest nowy mecz"""

        games_count = Match.objects.count()

        url = reverse('match_create')
        response = login_user.post(url, data=game_data)
        # with pytest.raises(PermissionDenied):
        game1 = Match.objects.last()
        assert response.status_code == 403

    def test_match_create_view_with_permission(self,moderator_user, team, game_data):
        """sprawdzam czy tworzony jest nowy mecz"""

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


    def test_match_create_view_with_the_same_teams(self,moderator_user,team, game_data):
        """sprawdzam czy tworzony jest nowy mecz z tymi samymi drużynami"""

        game = game_data.copy()
        game['away_team']=game['home_team']
        url = reverse('match_create')
        client, user = moderator_user
        games_count = Match.objects.count()
        response = client.post(url, data=game)
        
        assert games_count == Match.objects.count()
        assert response.status_code == 200
        assert 'form' in response.context #sprawdza, czy obiekt formularza (form) został przekazany do kontekstu szablonu
        assert 'away_team' in response.context['form'].errors #sprawdza, czy pole away_team ma błąd walidacji

    def test_match_create_view_with_wrong_home_score(self,moderator_user,team, game_data):
        """sprawdzam czy tworzony jest nowy mecz z błędną ilością bramek gospodarza"""

        game = game_data.copy()
        game['home_score'] = -3
        url = reverse('match_create')
        client, user = moderator_user
        games_count = Match.objects.count()
        response = client.post(url, data=game)
        
        assert games_count == Match.objects.count()
        assert response.status_code == 200
        assert 'form' in response.context #sprawdza, czy obiekt formularza (form) został przekazany do kontekstu szablonu
        assert 'home_score' in response.context['form'].errors #sprawdza, czy pole home_score ma błąd walidacji

    def test_match_create_view_with_wrong_away_score(self,moderator_user, team, game_data):
        """sprawdzam czy tworzony jest nowy mecz z błędną ilością bramek gości"""
        
        game = game_data.copy()
        game['away_score'] = -1
        url = reverse('match_create')
        client, user = moderator_user
        games_count = Match.objects.count()
        response = client.post(url, data=game)
        
        assert games_count == Match.objects.count()
        assert response.status_code == 200
        assert 'form' in response.context #sprawdza, czy obiekt formularza (form) został przekazany do kontekstu szablonu
        assert 'away_score' in response.context['form'].errors #sprawdza, czy pole away_score ma błąd walidacji

    def test_match_create_view_with_wrong_lap(self,moderator_user,team,game_data):
        """sprawdzam czy tworzony jest nowy mecz z błędnym numerem kolejki"""

        game = game_data.copy()
        game['lap'] = 0
        url = reverse('match_create')
        client, user = moderator_user
        games_count = Match.objects.count()
        response = client.post(url, data=game)
        
        assert games_count == Match.objects.count()
        assert response.status_code == 200
        assert 'form' in response.context #sprawdza, czy obiekt formularza (form) został przekazany do kontekstu szablonu
        assert 'lap' in response.context['form'].errors #sprawdza, czy pole lap ma błąd walidacji

    def test_match_create_view_with_wrong_date(self,moderator_user,team,game_data):
        """sprawdzam czy tworzony jest nowy mecz z błędną datą"""

        game = game_data.copy()
        game['date'] = -3
        url = reverse('match_create')
        client, user = moderator_user
        games_count = Match.objects.count()
        response = client.post(url, data=game)
        
        assert games_count == Match.objects.count()
        assert response.status_code == 200
        assert 'form' in response.context #sprawdza, czy obiekt formularza (form) został przekazany do kontekstu szablonu
        assert 'date' in response.context['form'].errors #sprawdza, czy pole date ma błąd walidacji

    def test_match_create_view_with_missing_data(self,moderator_user, team, game_data):
        """sprawdzam czy tworzony jest nowy mecz z błędnym numerem kolejki"""

        game = game_data.copy()
        game['date'] = None
        url = reverse('match_create')
        client, user = moderator_user
        games_count = Match.objects.count()
        with pytest.raises(TypeError):
            response = client.post(url, data=game)
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

@pytest.mark.django_db
class TestDeleteMatchView():
    
    def test_delete_view_without_authorization(self,client, game):
        """ sprawdzam, czy przekierowuje użytkownika bez autoryzacji"""
        games_count = Match.objects.count()
        url = reverse('match_delete', kwargs={'pk': game.pk})
        response = client.get(url)
        assert response.status_code == 302
        assert games_count == Match.objects.count()

    def test_delete_view_without_permission(self, login_user, game):
        """ sprawdzam, czy odmawia dostępu zalogowanego użytkownika bez uprawnień"""
        games_count = Match.objects.count()
        url = reverse('match_delete', kwargs={'pk': game.pk})
        response = login_user.get(url)
        assert response.status_code == 403
        assert games_count == Match.objects.count()

    def test_delete_view_deletes_object(self, moderator_user, game):
        """sprawdzam, czy poprawnie usuwa mecz"""
        games_count = Match.objects.count()
        client, _ = moderator_user
        url = reverse('match_delete', kwargs={'pk': game.pk})
        response = client.post(url)

        assert games_count -1 == Match.objects.count()
        assert response.status_code == 302
        assert response.url == reverse('index')
        assert not Match.objects.filter(pk=game.pk).exists()

    def test_delete_view_renders_confirmation_template(self, moderator_user, game):
        """sprawdzam, czy poprawnie renderuje szablon z poprawnym kontekstem"""
        client, _ = moderator_user
        url = reverse('match_delete', kwargs={'pk': game.pk})
        response = client.get(url)

        assert response.status_code == 200
        assert "football/match_delete.html" in [t.name for t in response.templates]
        assert response.context["object"] == game


@pytest.mark.django_db
class TestUpdateMatchView():
    
    def test_update_view_without_authorization(self,client, game):
        """ sprawdzam, czy przekierowuje użytkownika bez autoryzacji"""
        url = reverse('match_update', kwargs={'pk': game.pk})
        response = client.get(url)
        assert response.status_code == 302

    def test_update_view_without_permission(self, login_user, game):
        """ sprawdzam, czy odmawia dostępu zalogowanego użytkownika bez uprawnień"""
        url = reverse('match_update', kwargs={'pk': game.pk})
        response = login_user.get(url)
        assert response.status_code == 403

    def test_update_view_update_object(self, moderator_user, game):
        """sprawdzam, czy poprawnie uaktualnia dane meczu"""
        before_lap = Match.objects.get(pk=game.pk).lap
        games_count = Match.objects.count()
        client, user = moderator_user
        url = reverse('match_update', kwargs={'pk': game.pk})
        response = client.post(url, data={
            'lap': 2,
            'date': game.date,
            'home_team': game.home_team.pk,
            'away_team': game.away_team.pk,
            'home_score': game.home_score,
            'away_score': game.away_score,
            })
    
        assert Match.objects.get(pk=game.pk).lap ==2
        assert Match.objects.get(pk=game.pk).lap!= before_lap
        assert games_count == Match.objects.count()
        assert response.status_code == 302
        assert response.url == reverse('index')
        assert Match.objects.filter(pk=game.pk).exists()

    def test_update_view_renders_confirmation_template(self, moderator_user, game):
        """sprawdzam, czy poprawnie renderuje szablon z poprawnym kontekstem"""
        client, user = moderator_user
        url = reverse('match_update', kwargs={'pk': game.pk})
        response = client.get(url)

        assert response.status_code == 200
        assert "football/match_update.html" in [t.name for t in response.templates]
        assert response.context["object"] == game

@pytest.mark.django_db
class TestTeamInfoView():
    def test_team_info_view_without_authorization(self,client, single_team):
        """ sprawdzam, czy przekierowuje użytkownika bez autoryzacji"""
        url = reverse('team_info', kwargs={'pk': single_team.pk})
        response = client.get(url)
        assert response.status_code == 302

    def test_team_info_view_renders_confirmation_template(self, login_user, single_team):
        """sprawdzam, czy poprawnie renderuje szablon z poprawnym kontekstem"""
        url = reverse('team_info', kwargs={'pk': single_team.pk})
        response = login_user.get(url)

        assert response.status_code == 200
        assert "football/team_info.html" in [t.name for t in response.templates]
        assert response.context["object"] == single_team

    def test_team_info_all_positions_in_context(self, login_user, single_team):
        """sprawdzam, czy gracz z każdą pozycją jest w konteście"""
        positions = ['gk', 'df', 'mf', 'st']
        
        for position in positions:
            baker.make('football.Player', team=single_team, position=position)

        url = reverse('team_info', kwargs={'pk': single_team.pk})
        response = login_user.get(url)

        for position in positions:
            player = Player.objects.get(team=single_team, position=position)
            if position == 'gk':
                assert player in response.context['goalkeepers']
            elif position == 'df':
                assert player in response.context['defenders']
            elif position == 'mf':
                assert player in response.context['midfielders']
            elif position == 'st':
                assert player in response.context['strikers']

    def test_team_info_player_from_another_team(self, login_user, team):
        """sprawdzam, czy gracz z innej drużyny nei pojawi się w kontekscie"""
       
        player = baker.make('football.Player', team=team[0])
        url = reverse('team_info', kwargs={'pk': team[1].pk})
        response = login_user.get(url)

        assert player.position in ['gk', 'df', 'mf', 'st']  #czy na pewno dobrze stworzona pozycja
        assert player not in response.context['goalkeepers']
        assert player not in response.context['defenders']
        assert player not in response.context['midfielders']
        assert player not in response.context['strikers']

    def test_team_info_without_players(self, login_user, single_team):
        """sprawdzam, czy bez wproadzania piłkarzy pojawią się jacyś gracze"""

        url = reverse('team_info', kwargs={'pk': single_team.pk})
        response = login_user.get(url)
     
        assert response.context['goalkeepers'].count() == 0
        assert response.context['defenders'].count() == 0
        assert response.context['midfielders'].count() == 0
        assert response.context['strikers'].count() == 0

    def test_team_info_wrong_team(self, login_user):
        """sprawdzam, czy bez wproadzania piłkarzy pojawią się jacyś gracze"""

        url = reverse('team_info', kwargs={'pk': 9999})
        response = login_user.get(url)

        assert response.status_code == 404
    
@pytest.mark.django_db
class TestLinupCreateView:
    
    @pytest.mark.parametrize("team_type", ["home_team", "away_team"])
    def test_lineup_create_view_without_authorization(self,client, game, team_type):
        """ sprawdzam, czy przekierowuje użytkownika bez autoryzacji"""
        url = reverse('lineup_create', kwargs={'pk': game.pk, 'team_type':team_type})
        response = client.get(url)
        assert response.status_code == 302

    @pytest.mark.parametrize("team_type", ["home_team", "away_team"])
    def test_lineup_create_without_permission(self, login_user, game, team_type):
        """ sprawdzam, czy odmawia dostępu zalogowanego użytkownika bez uprawnień"""
        url = reverse('lineup_create', kwargs={'pk': game.pk, 'team_type':team_type})
        response = login_user.get(url)
        assert response.status_code == 403

    @pytest.mark.parametrize("team_type", ["home", "away"])
    def test_lineup_create(self, moderator_user, game, team_type):
        """sprawdzam czy poprawnie tworzy lineup oraz czy poprawnie renderuje formularz"""

        positions = ['gk', 'df', 'mf', 'st']
        
        if team_type == "home":
            first_team = game.home_team
            second_team = game.away_team
        else:
            first_team = game.away_team
            second_team = game.home_team

        for position in positions:
            baker.make('football.Player', team=first_team, position=position, name=f"zawodnik first team {position}")
        for position in positions:
            baker.make('football.Player', team=second_team, position=position, name=f"zawodnik second team {position}")

        client , _ = moderator_user
        url = reverse('lineup_create', kwargs={'pk': game.pk, 'team_type':team_type})
        response = client.get(url)

        assert response.status_code == 200
        assert "football/lineup_form.html" in [t.name for t in response.templates]
        assert 'goalkeepers' in response.context
        assert 'defenders' in response.context
        assert 'midfielders' in response.context
        assert 'strikers' in response.context
        assert len(response.context['goalkeepers']) == 1
        assert len(response.context['defenders']) == 1
        assert len(response.context['midfielders']) == 1
        assert len(response.context['strikers']) == 1
        assert "first team gk" in str(response.context['goalkeepers'])
        assert "first team df" in str(response.context['defenders'])
        assert "first team mf" in str(response.context['midfielders'])
        assert "first team st" in str(response.context['strikers'])
        assert "second team gk" not in str(response.context['goalkeepers'])
        assert "second team df" not in str(response.context['defenders'])
        assert "second team mf" not in str(response.context['midfielders'])
        assert "second team st" not in str(response.context['strikers'])

    @pytest.mark.parametrize("team_type", ["home", "away"])
    def test_lineup_create(self, moderator_user, game, team_type):
        """sprawdzam poprawnośc przesłanego formularza przy POST"""

        client, _ = moderator_user
        team = game.home_team if team_type == 'home' else game.away_team
        players = [baker.make('football.Player', team = team) for _ in range(11)]
        lineups_count = Lineup.objects.filter(match=game, team=team).count()
        lineup_data = {'match':game.id, 'team': team.id, 'players':[player.id for player in players]}
        
        url = reverse('lineup_create', kwargs={'pk': game.pk, 'team_type':team_type})
        response = client.post(url, data=lineup_data)
        player_ids_in_lineups = Lineup.objects.filter(team=team, match=game).values_list('player_id', flat=True)

        assert set(player_ids_in_lineups) == set([p.id for p in players])
        assert len(player_ids_in_lineups) == len(set(player_ids_in_lineups)) 
        assert response.status_code == 302
        assert lineups_count + 11 == Lineup.objects.filter(match=game, team=team).count()
        for l in Lineup.objects.filter(team=team, match=game):
            assert l.is_starting is True
            assert l.on_bench is False
            assert l.team == team
            assert l.match == game


    @pytest.mark.parametrize("team_type", ["home", "away"])
    def test_lineup_create_to_many_players(self, moderator_user, game, team_type):
        """sprawdzam czy zapisze lineup przy zbyt dużej ilości graczy"""

        client, _ = moderator_user
        team = game.home_team if team_type == 'home' else game.away_team
        players = [baker.make('football.Player', team = team) for _ in range(12)]
        lineups_count = Lineup.objects.filter(match=game, team=team).count()
        lineup_data = {'match':game.id, 'team': team.id, 'players':[player.id for player in players]}
        
        url = reverse('lineup_create', kwargs={'pk': game.pk, 'team_type':team_type})
        response = client.post(url, data=lineup_data)
      
        assert response.status_code == 200
        assert lineups_count == Lineup.objects.filter(match=game, team=team).count()

    @pytest.mark.parametrize("team_type", ["home", "away"])
    def test_lineup_create_to_less_players(self, moderator_user, game, team_type):
        """sprawdzam czy zapisze lineup przy zbyt małej ilości graczy"""

        client, _ = moderator_user
        team = game.home_team if team_type == 'home' else game.away_team
        players = [baker.make('football.Player', team = team) for _ in range(10)]
        lineups_count = Lineup.objects.filter(match=game, team=team).count()
        lineup_data = {'match':game.id, 'team': team.id, 'players':[player.id for player in players]}
        
        url = reverse('lineup_create', kwargs={'pk': game.pk, 'team_type':team_type})
        response = client.post(url, data=lineup_data)
      
        assert response.status_code == 200
        assert lineups_count == Lineup.objects.filter(match=game, team=team).count()

    
    @pytest.mark.parametrize("team_type", ["home", "away"])
    def test_lineup_create_wrong_team_players(self, moderator_user, game, team_type):
        """sprawdzam czy zapisze lineup przy wyborze graczy ze złej drużyny"""

        client, _ = moderator_user
        team = game.away_team if team_type == 'home' else game.home_team
        players = [baker.make('football.Player', team = team) for _ in range(11)]
        lineups_count = Lineup.objects.filter(match=game, team=team).count()
        lineup_data = {'match':game.id, 'team': team.id, 'players':[player.id for player in players]}
        
        url = reverse('lineup_create', kwargs={'pk': game.pk, 'team_type':team_type})
        response = client.post(url, data=lineup_data)
      
        assert response.status_code == 200
        assert lineups_count == Lineup.objects.filter(match=game, team=team).count()
          
@pytest.mark.django_db
class TestLapsListView:

    def test_laps_list_view_without_authorization(self,client):
        """ sprawdzam, czy przekierowuje użytkownika bez autoryzacji"""
        url = reverse('laps_list')
        response = client.get(url)
        assert response.status_code == 302
 
    def test_laps_list_view_with_authorization(self,login_user):
        """ sprawdzam, kod odpowiedzi oraz czy laps_list jest w kontekście"""
        url = reverse('laps_list')
        response = login_user.get(url)
        assert response.status_code == 200
        assert "laps_list" in response.context

    def test_laps_list_view_laps(self,login_user, game, team):
        """ sprawdzam, czy zwraca odpowiednie kolejki"""
        url = reverse('laps_list')

        baker.make("football.Match",
            lap= 1,
            date= date(2025, 4, 5),
            home_team= team[0],
            away_team= team[1],
            home_score= 3,
            away_score= 0
        )

        baker.make("football.Match",
            lap= 2,
            date= date(2025, 4, 12),
            home_team= team[0],
            away_team= game.home_team,
            home_score= 3,
            away_score= 0
        )

        expected_laps = [{'lap': 1}, {'lap': 2}]

        response = login_user.get(url)
        assert response.status_code == 200
        assert "laps_list" in response.context
        assert list(response.context['laps_list']) == expected_laps

@pytest.mark.django_db
class TestLineupUpdateView:

    @pytest.mark.parametrize("team_type", ["home_team", "away_team"])
    def test_lineup_update_view_without_authorization(self,client, game, team_type):
        """ sprawdzam, czy przekierowuje użytkownika bez autoryzacji"""
        url = reverse('lineup', kwargs={'pk': game.pk, 'team_type':team_type})
        response = client.get(url)
        assert response.status_code == 302

    @pytest.mark.parametrize("team_type", ["home_team", "away_team"])
    def test_lineup_update_without_permission(self, login_user, game, team_type):
        """ sprawdzam, czy odmawia dostępu zalogowanego użytkownika bez uprawnień"""
        url = reverse('lineup', kwargs={'pk': game.pk, 'team_type':team_type})
        response = login_user.get(url)
        assert response.status_code == 403

    # @pytest.mark.parametrize("team_type", ["home", "away"])
    # def test_lineup_update_with_permission_and_checked_players(self, moderator_user, game,lineup, team_type):
    #     """sprawdzam czy poprawnie renderuje, zwraca poprany kod oraz czy zaznaczacza zawodników wybranych wcześniej"""
    #     client, _ = moderator_user
    #     response = client.get(reverse('lineup', kwargs={'pk': game.pk, 'team_type': team_type}))
    #     # form = response.context['form']
    #     initial_players = list(response.context['selected_players'])
    #     selected_ids = [player.id for player in lineup]
    #     print("a ja:", response.context['selected_players'])
    #     print("a ja:", response.context['players'])
    #     print("initial:", initial_players)
    #     print("selected:", selected_ids)

    #     assert response.status_code == 200
    #     assert set(initial_players) == set(selected_ids)
