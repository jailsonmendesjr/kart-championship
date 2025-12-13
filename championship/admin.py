from django.contrib import admin
from .models import Season, Team, Driver, DriverTeamSeason, Round, RoundResult

@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ('name', 'year', 'is_active')
    list_filter = ('year', 'is_active')

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'primary_color')
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('name', 'nickname', 'number')
    search_fields = ('name', 'nickname')
    prepopulated_fields = {"slug": ("name",)}

@admin.register(DriverTeamSeason)
class DriverTeamSeasonAdmin(admin.ModelAdmin):
    list_display = ('season', 'team', 'driver', 'car_number')
    list_filter = ('season', 'team')

# Configuração da Tabela de Resultados dentro da Etapa
class ResultInline(admin.TabularInline):
    model = RoundResult
    extra = 10 # Mostra 10 linhas vazias para preencher rápido
    fields = ('position', 'entry', 'fastest_lap', 'points') # Ordem das colunas
    readonly_fields = ('points',) # Pontos são calculados, o user não edita na mão

@admin.register(Round)
class RoundAdmin(admin.ModelAdmin):
    list_display = ('name', 'season', 'date', 'location')
    list_filter = ('season',)
    inlines = [ResultInline]