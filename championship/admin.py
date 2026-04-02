from django.contrib import admin
from .models import Season, Team, Driver, DriverTeamSeason, Round, RoundResult

class RoundResultInline(admin.TabularInline):
    model = RoundResult
    extra = 1
    readonly_fields = ('points',) 

    def get_formset(self, request, obj=None, **kwargs):
        # 1. Deixa o Django criar o formulário base
        formset = super().get_formset(request, obj, **kwargs)
        
        # 2. Se a Etapa já existe (obj) e tem uma Temporada atrelada...
        if obj and obj.season:
            # 3. Força a raiz do campo 'entry' a carregar APENAS a temporada da etapa
            formset.form.base_fields['entry'].queryset = DriverTeamSeason.objects.filter(
                season=obj.season
            ).order_by('driver__name')
            
        return formset
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