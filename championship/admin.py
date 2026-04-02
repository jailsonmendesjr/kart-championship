from django.contrib import admin
from import_export.admin import ImportExportModelAdmin, ExportActionMixin
from .models import Season, Team, Driver, DriverTeamSeason, Round, RoundResult

# 1. Restaurando o Inline: Isso permite cadastrar os resultados DENTRO da página da Etapa
class RoundResultInline(admin.TabularInline):
    model = RoundResult
    extra = 1
    # Note: Removi 'fastest_lap' daqui pois ele ainda não existe no seu model.py
    fields = ('driver_team_season', 'position', 'points') 

@admin.register(Season)
class SeasonAdmin(ImportExportModelAdmin):
    list_display = ('name', 'year', 'is_active')

@admin.register(Team)
class TeamAdmin(ImportExportModelAdmin):
    list_display = ('name',)

@admin.register(Driver)
class DriverAdmin(ImportExportModelAdmin):
    list_display = ('name', 'nickname')

@admin.register(DriverTeamSeason)
class DriverTeamSeasonAdmin(ImportExportModelAdmin):
    list_display = ('driver', 'team', 'season')
    list_filter = ('season', 'team')

@admin.register(Round)
class RoundAdmin(ImportExportModelAdmin):
    list_display = ('name', 'season', 'date')
    list_filter = ('season',)
    inlines = [RoundResultInline] # <--- Isso traz de volta o que funcionava antes!

# 2. Área de Resultados (apenas para exportação em massa se precisar)
@admin.register(RoundResult)
class RoundResultAdmin(ExportActionMixin, admin.ModelAdmin):
    # Removido 'fastest_lap' para matar o Erro 500
    list_display = ('round', 'driver_team_season', 'position', 'points')
    list_filter = ('round__season', 'round')