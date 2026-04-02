from django.contrib import admin
from .models import Season, Team, Driver, DriverTeamSeason, Round, RoundResult

class RoundResultInline(admin.TabularInline):
    model = RoundResult
    extra = 1
    readonly_fields = ('points',) # <--- Essa linha traz a coluna de volta (bloqueada para edição)
    # Removendo a lista estrita de 'fields' deixa o Django renderizar 
    # todos os campos reais do modelo de forma segura, evitando erros.

@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ('name', 'year', 'is_active')

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('name', 'nickname')

@admin.register(DriverTeamSeason)
class DriverTeamSeasonAdmin(admin.ModelAdmin):
    list_display = ('driver', 'team', 'season')
    list_filter = ('season', 'team')

@admin.register(Round)
class RoundAdmin(admin.ModelAdmin):
    list_display = ('name', 'season', 'date')
    list_filter = ('season',)
    inlines = [RoundResultInline]

# Note que eu apaguei a classe RoundResultAdmin. 
# Assim, o menu "Resultados" vai sumir e voltamos à normalidade.