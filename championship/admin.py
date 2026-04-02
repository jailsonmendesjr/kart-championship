from django.contrib import admin
from .models import Season, Team, Driver, DriverTeamSeason, Round, RoundResult

class RoundResultInline(admin.TabularInline):
    model = RoundResult
    extra = 1
    readonly_fields = ('points',) 

    # 1. O Django chama isso primeiro. Vamos "guardar" a Etapa atual na memória.
    def get_formset(self, request, obj=None, **kwargs):
        request._current_round_obj = obj
        return super().get_formset(request, obj, **kwargs)

    # 2. O Django chama isso para montar o dropdown. Vamos usar a Etapa guardada.
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "entry":
            current_round = getattr(request, '_current_round_obj', None)
            
            # Se a etapa já existe e tem uma temporada, filtra!
            if current_round and current_round.season:
                kwargs["queryset"] = DriverTeamSeason.objects.filter(
                    season=current_round.season
                ).order_by('driver__name')
                
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