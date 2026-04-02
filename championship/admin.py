from django.contrib import admin
from .models import Season, Team, Driver, DriverTeamSeason, Round, RoundResult

class RoundResultInline(admin.TabularInline):
    model = RoundResult
    extra = 1
    readonly_fields = ('points',) 

    # --- A MÁGICA DA FILTRAGEM COMEÇA AQUI ---
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "entry":
            # Tenta pegar o ID da Etapa (Round) que está sendo editada através da URL
            object_id = request.resolver_match.kwargs.get('object_id')
            
            if object_id:
                # Se estamos editando uma etapa existente, descobre a temporada dela
                current_round = Round.objects.get(pk=object_id)
                # Filtra o dropdown para mostrar APENAS as inscrições daquela temporada
                kwargs["queryset"] = DriverTeamSeason.objects.filter(season=current_round.season)
                
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    # --- FIM DA MÁGICA ---

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