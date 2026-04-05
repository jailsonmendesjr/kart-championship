from django.contrib import admin
from django.forms.models import BaseInlineFormSet  # <--- IMPORT NOVO E NECESSÁRIO
from .models import Season, Team, Driver, DriverTeamSeason, Round, RoundResult

# --- 1. A NOVA CLASSE MÁGICA QUE PREENCHE OS DADOS ---
class RoundResultFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Se a etapa já foi criada (tem ID) e ainda não tem resultados salvos...
        if self.instance and self.instance.pk and not self.queryset.exists():
            # Busca todos os pilotos oficiais (ignora os convidados)
            drivers = DriverTeamSeason.objects.filter(
                season=self.instance.season,
                is_guest=False
            ).order_by('driver__name')
            
            # Injeta os pilotos já selecionados nas linhas vazias!
            self.initial = [{'entry': d.id} for d in drivers]

# --- 2. O INLINE ATUALIZADO ---
class RoundResultInline(admin.TabularInline):
    model = RoundResult
    formset = RoundResultFormSet  # <--- Aponta para a mágica acima
    readonly_fields = ('points',) 

    def get_extra(self, request, obj=None, **kwargs):
        # Se a etapa já existe e está vazia, abre exatamente o número de linhas de pilotos
        if obj and obj.season and not obj.results.exists():
            return DriverTeamSeason.objects.filter(season=obj.season, is_guest=False).count()
        # Se já tiver resultados (edição futura), deixa só 1 linha extra vazia pro padrão
        return 1

    def get_formset(self, request, obj=None, **kwargs):
        # Mantém a nossa trava de segurança que filtra a lista (feita anteriormente)
        formset = super().get_formset(request, obj, **kwargs)
        if obj and obj.season:
            formset.form.base_fields['entry'].queryset = DriverTeamSeason.objects.filter(
                season=obj.season
            ).order_by('driver__name')
        return formset

# ... (Daqui para baixo continuam os seus @admin.register normais) ...
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