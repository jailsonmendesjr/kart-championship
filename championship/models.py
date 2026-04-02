from django.db import models
from django.core.exceptions import ValidationError

# --- Regras de Pontuação ---
POINTS_2025 = {
    1: 25, 2: 18, 3: 15, 4: 12, 5: 10,
    6: 8, 7: 6, 8: 4, 9: 2, 10: 1
}

POINTS_2026 = {
    1: 18, 2: 15, 3: 13, 4: 11, 5: 9,
    6: 7, 7: 5, 8: 3, 9: 2, 10: 1
}

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
    
    # NOVO CAMPO: Etiqueta de Convidado
    is_guest = models.BooleanField("Piloto Convidado?", default=False, help_text="Convidados consomem pontos na etapa, mas NÃO aparecem no Ranking Geral.")

    class Meta:
        verbose_name = "Inscrição"
        verbose_name_plural = "Inscrições"
        unique_together = ("season", "driver")

    def __str__(self):
        # Exibe: "Clauston (Sauber) ---> Campeonato 2026"
        return f"{self.driver.name} ({self.team.name}) ---> {self.season.name}"

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
    STATUS_CHOICES = [
        ('COMPLETED', 'Concluído'),
        ('DNF', 'Não Concluiu (DNF)'),
        ('DNS', 'Faltou (DNS)'),
    ]

    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name="results", verbose_name="Etapa")
    entry = models.ForeignKey(DriverTeamSeason, on_delete=models.CASCADE, related_name="results", verbose_name="Piloto/Equipe")
    position = models.PositiveIntegerField("Posição")
    
    # Novos campos
    status = models.CharField("Status da Prova", max_length=10, choices=STATUS_CHOICES, default='COMPLETED')
    has_penalty = models.BooleanField("Sofreu Punição?", default=False)
    penalty_reason = models.CharField("Motivo da Punição", max_length=200, blank=True)
    fastest_lap = models.BooleanField("Volta + Rápida?", default=False)
    
    points = models.PositiveIntegerField("Pontos", default=0, editable=False)

    class Meta:
        verbose_name = "Resultado"
        verbose_name_plural = "Resultados"
        ordering = ["position"]

    def __str__(self):
        extra = " (Volta Rápida)" if self.fastest_lap else ""
        status_info = f" [{self.status}]" if self.status != 'COMPLETED' else ""
        return f"P{self.position} - {self.entry.driver}{extra}{status_info}"

    def clean(self):
        # Validação de Volta Rápida Única
        if self.fastest_lap:
            existing = RoundResult.objects.filter(round=self.round, fastest_lap=True)
            if self.pk:
                existing = existing.exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError("Já existe um piloto com a volta mais rápida nesta etapa.")
        
        # Validação de Posição Única (ignorando DNS que podem ficar sem posição definida)
        if self.status != 'DNS':
            existing_pos = RoundResult.objects.filter(round=self.round, position=self.position)
            if self.pk:
                existing_pos = existing_pos.exclude(pk=self.pk)
            if existing_pos.exists():
                raise ValidationError(f"A posição {self.position} já foi registrada para outro piloto nesta etapa.")

    def save(self, *args, **kwargs):
        # Se não concluiu ou faltou, pontos = 0
        if self.status in ['DNF', 'DNS']:
            self.points = 0
        else:
            # Trava temporal: Define qual tabela usar
            if self.round.season.year >= 2026:
                base_points = POINTS_2026.get(self.position, 0)
            else:
                base_points = POINTS_2025.get(self.position, 0)
            
            # Bônus de volta rápida (aplica-se a quem completou)
            bonus = 1 if self.fastest_lap else 0
            self.points = base_points + bonus
            
        super().save(*args, **kwargs)