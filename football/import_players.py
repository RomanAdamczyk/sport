import sys
import os
import django

# Dodanie folderu nadrzędnego sport do ścieżki Pythona
sys.path.append(r"D:\Python\Praktyczny_Python_materialy\Django_pliki\sport")

# Ustawienie zmiennej środowiskowej dla Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sport.settings")

# Konfiguracja Django
django.setup()

print("Django zostało skonfigurowane poprawnie!")

from football.models import Player, Team
from datetime import datetime

# Funkcja do parsowania wzrost/waga
def parse_height_weight(data):
    try:
        height, weight = data.split("/")
        return int(height), int(weight)
    except ValueError:
        return None, None

# Ścieżka do pliku z danymi
file_path = r"D:\Python\Praktyczny_Python_materialy\zawodnicy_v5.txt"

with open(file_path, encoding="utf-8") as file:
    for line in file:
        data = line.strip().split(",")  # Podział linii po przecinku
        if len(data) < 8:  # Sprawdzenie poprawności linii
            continue

        team_name, position, name, nationality, birth_date, height_weight, previous_club, _ = data

        # Znalezienie drużyny
        try:
            team = Team.objects.get(name=team_name)
        except Team.DoesNotExist:
            print(f"Drużyna {team_name} nie istnieje. Popraw dane!")
            continue

        # Parsowanie wzrostu i wagi
        height, weight = parse_height_weight(height_weight)

        # Tworzenie zawodnika
        player = Player.objects.create(
            name=name,
            position=position,
            birth_day=datetime.strptime(birth_date, "%d.%m.%y").date(),
            nationality=nationality,
            
        )
        player.team = team
        player.save()  # Dodanie do drużyny

        # print(f"Dodano zawodnika: {name} do drużyny {team_name}")

from football.models import Team

