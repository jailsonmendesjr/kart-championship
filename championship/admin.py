from django.contrib import admin
from import_export.admin import ExportActionMixin
from .models import Season, Team, Driver, DriverTeamSeason, Round, RoundResult

@admin.register(Season)
class SeasonAdmin(ExportActionMixin, admin.ModelAdmin):
    list_display = ('name', 'year', 'is_active')

@admin.register(Team)
class TeamAdmin(ExportActionMixin, admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Driver)
class DriverAdmin(ExportActionMixin, admin.ModelAdmin):
    list_display = ('name', 'nickname')

@admin.register(DriverTeamSeason)
class DriverTeamSeasonAdmin(ExportActionMixin, admin.ModelAdmin):
    list_display = ('driver', 'team', 'season')
    list_filter = ('season', 'team')

@admin.register(Round)
class RoundAdmin(ExportActionMixin, admin.ModelAdmin):
    list_display = ('name', 'season', 'date')
    list_filter = ('season',)

@admin.register(RoundResult)
class RoundResultAdmin(ExportActionMixin, admin.ModelAdmin):
    list_display = ('round', 'driver_team_season', 'position', 'points', 'fastest_lap')
    list_filter = ('round__season', 'round')