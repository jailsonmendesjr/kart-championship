from django.db import models
from django.core.exceptions import ValidationError

# --- Regra de Pontuação (F1) ---
F1_POINTS = {
    1: 25, 2: 18, 3: 15, 4: 12, 5: 10,
    6: 8, 7: 6, 8: 4, 9: 2, 10: 1
}

def get_points_for_position(position):
    return F1_POINTS.get(position, 0)

# --- Models ---

class Season(models.Model):
    name = models.CharField("Nome", max_length=100)
    year = models.PositiveIntegerField("Ano")
    is_active = models.BooleanField("Temporada Ativa?", default=False)

    class Meta:
        verbose_name = "Temporada"
        verbose_name_plural = "Temporadas"
        ordering = ["-year", "name"]

    def __str__(self):
        return f"{self.name} ({self.year})"

class Team(models.Model):
    name = models.CharField("Nome", max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, help_text="Usado na URL")
    primary_color = models.CharField("Cor Primária", max_length=7, blank=True, default="#000000") 
    secondary_color = models.CharField("Cor Secundária", max_length=7, blank=True, default="#FFFFFF")

    class Meta:
        verbose_name = "Equipe"
        verbose_name_plural = "Equipes"
        ordering = ["name"]

    def __str__(self):
        return self.name

class Driver(models.Model):
    name = models.CharField("Nome", max_length=100)
    nickname = models.CharField("Apelido", max_length=50, blank=True)
    slug = models.SlugField(max_length=120, unique=True, help_text="Usado na URL")
    number = models.PositiveIntegerField("Número do Piloto", null=True, blank=True)
    
    class Meta:
        verbose_name = "Piloto"
        verbose_name_plural = "Pilotos"
        ordering = ["name"]

    def __str__(self):
        return self.nickname or self.name

class DriverTeamSeason(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="driver_teams", verbose_name="Temporada")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="season_drivers", verbose_name="Equipe")
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name="seasons", verbose_name="Piloto")
    car_number = models.PositiveIntegerField("Número do Carro", null=True, blank=True)

    class Meta:
        verbose_name = "Inscrição"
        verbose_name_plural = "Inscrições"
        unique_together = ("season", "driver")

    def __str__(self):
        return f"{self.driver} ({self.team})"

    def clean(self):
        existing = DriverTeamSeason.objects.filter(season=self.season, team=self.team)
        if self.pk:
            existing = existing.exclude(pk=self.pk)
        if existing.count() >= 2:
            raise ValidationError("Esta equipe já tem 2 pilotos nesta temporada.")

class Round(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name="rounds", verbose_name="Temporada")
    name = models.CharField("Nome da Etapa", max_length=100)
    date = models.DateField("Data")
    location = models.CharField("Local", max_length=100, blank=True)
    order = models.PositiveIntegerField("Ordem")

    class Meta:
        verbose_name = "Etapa"
        verbose_name_plural = "Etapas"
        ordering = ["season", "order"]
        unique_together = ("season", "order")

    def __str__(self):
        return f"{self.name}"

class RoundResult(models.Model):
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name="results", verbose_name="Etapa")
    entry = models.ForeignKey(DriverTeamSeason, on_delete=models.CASCADE, related_name="results", verbose_name="Piloto/Equipe")
    position = models.PositiveIntegerField("Posição")
    fastest_lap = models.BooleanField("Volta + Rápida?", default=False) # Novo campo
    points = models.PositiveIntegerField("Pontos", default=0, editable=False)

    class Meta:
        verbose_name = "Resultado"
        verbose_name_plural = "Resultados"
        ordering = ["position"]
        unique_together = ("round", "position") # Garante que ninguém duplique a posição

    def __str__(self):
        extra = " (Volta Rápida)" if self.fastest_lap else ""
        return f"P{self.position} - {self.entry.driver}{extra}"

    def clean(self):
        # Validação: Garante apenas 1 volta rápida por etapa
        if self.fastest_lap:
            # Busca se já existe ALGUÉM com volta rápida nesta etapa
            existing = RoundResult.objects.filter(round=self.round, fastest_lap=True)
            
            # Se estou editando uma linha já existente, me excluo da busca
            if self.pk:
                existing = existing.exclude(pk=self.pk)
            
            if existing.exists():
                raise ValidationError("Já existe um piloto com a volta mais rápida nesta etapa. Desmarque o outro primeiro.")

    def save(self, *args, **kwargs):
        # Calcula pontos base + 1 ponto se tiver volta rápida
        base_points = get_points_for_position(self.position)
        bonus = 1 if self.fastest_lap else 0
        self.points = base_points + bonus
        super().save(*args, **kwargs)