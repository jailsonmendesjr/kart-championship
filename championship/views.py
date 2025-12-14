from django.shortcuts import render, get_object_or_404
from django.db.models import Sum, Q
from django.db.models.functions import Coalesce
from .models import Season, DriverTeamSeason, Team, Round
import json
from django.shortcuts import render, get_object_or_404
from .models import Season, DriverTeamSeason, Round


def season_list(request):
    seasons = Season.objects.all().order_by('-year')
    return render(request, 'championship/season_list.html', {'seasons': seasons})

def calculate_standings(season, exclude_last_round=False):
    """
    Função auxiliar que calcula o ranking.
    Se exclude_last_round=True, ignora os pontos da última etapa realizada.
    """
    # Identifica quais etapas considerar
    rounds = season.rounds.all().order_by('order')
    if exclude_last_round and rounds.exists():
        # Pega todas as etapas menos a última
        last_round = rounds.last()
        rounds = rounds.exclude(pk=last_round.pk)
    
    # --- Ranking de Pilotos ---
    # Soma pontos apenas das etapas filtradas
    drivers = DriverTeamSeason.objects.filter(season=season).annotate(
        total_points=Coalesce(
            Sum('results__points', filter=Q(results__round__in=rounds)), 
            0
        )
    ).order_by('-total_points', 'driver__name')

    # Transforma em lista e atribui a posição (1º, 2º, 3º...) manualmente
    # Isso é necessário para sabermos a posição exata mesmo com empates
    drivers_list = list(drivers)
    for index, entry in enumerate(drivers_list):
        entry.position = index + 1
        
    # --- Ranking de Equipes ---
    teams = Team.objects.filter(season_drivers__season=season).distinct().annotate(
        total_points=Coalesce(
            Sum('season_drivers__results__points', filter=Q(season_drivers__results__round__in=rounds)),
            0
        )
    ).order_by('-total_points', 'name')
    
    teams_list = list(teams)
    for index, entry in enumerate(teams_list):
        entry.position = index + 1

    return drivers_list, teams_list

def season_detail(request, season_id):
    season = get_object_or_404(Season, pk=season_id)
    rounds_count = season.rounds.count()

    # 1. Calcula o Ranking Atual (Completo)
    current_drivers, current_teams = calculate_standings(season, exclude_last_round=False)

    # 2. Se houver mais de 1 etapa, calcula o Ranking Anterior para comparar
    if rounds_count > 1:
        prev_drivers, prev_teams = calculate_standings(season, exclude_last_round=True)
        
        # Cria dicionários para busca rápida: { id_do_piloto: posicao_anterior }
        prev_drivers_map = {d.driver.id: d.position for d in prev_drivers}
        prev_teams_map = {t.id: t.position for t in prev_teams}

        # Compara Pilotos
        for driver in current_drivers:
            old_pos = prev_drivers_map.get(driver.driver.id)
            if old_pos:
                # Se eu era 5º e virei 3º: 5 - 3 = 2 (Positivo = Subiu)
                # Se eu era 1º e virei 4º: 1 - 4 = -3 (Negativo = Desceu)
                driver.change = old_pos - driver.position
            else:
                driver.change = 0 # Novo no ranking ou sem dados anteriores

        # Compara Equipes
        for team in current_teams:
            old_pos = prev_teams_map.get(team.id)
            if old_pos:
                team.change = old_pos - team.position
            else:
                team.change = 0
    else:
        # Se for a 1ª etapa, não tem mudança
        for d in current_drivers: d.change = 0
        for t in current_teams: t.change = 0

    context = {
        'season': season,
        'drivers_ranking': current_drivers,
        'teams_ranking': current_teams,
    }
    return render(request, 'championship/season_detail.html', context)

def round_detail(request, season_id, round_id):
    season = get_object_or_404(Season, pk=season_id)
    round_obj = get_object_or_404(Round, pk=round_id, season=season)
    
    results = round_obj.results.select_related('entry__driver', 'entry__team').order_by('position')

    context = {
        'season': season,
        'round': round_obj,
        'results': results,
    }
    return render(request, 'championship/round_detail.html', context)


# --- Função Auxiliar (Não é uma view, serve para ajudar a view) ---
def get_driver_performance_data(season, driver_id):
    if not driver_id:
        return None
    
    # Busca a inscrição do piloto
    try:
        driver_season = DriverTeamSeason.objects.select_related('driver', 'team').get(
            season=season, driver_id=driver_id
        )
    except DriverTeamSeason.DoesNotExist:
        return None

    # Busca todas as etapas e resultados
    rounds = season.rounds.all().order_by('order')
    
    # Prepara listas para os gráficos
    labels = [] # Nomes das etapas (ex: R1, R2)
    points_cumulative = [] # Pontos acumulados [25, 43, 58...]
    positions = [] # Posições de chegada [1, 3, 2...]
    
    current_total = 0
    total_fast_laps = 0
    best_pos = 999
    
    for r in rounds:
        labels.append(f"R{r.order}")
        
        # Tenta achar o resultado nesta etapa
        result = driver_season.results.filter(round=r).first()
        
        if result:
            current_total += result.points
            points_cumulative.append(current_total)
            positions.append(result.position)
            
            # Stats extras
            if result.fastest_lap:
                total_fast_laps += 1
            if result.position < best_pos:
                best_pos = result.position
        else:
            # Se não correu, mantém o total anterior e marca posição como null (gráfico ignora)
            points_cumulative.append(current_total)
            positions.append(None) 

    # Estatísticas Resumidas
    stats = {
        'name': driver_season.driver.name,
        'team_name': driver_season.team.name,
        'team_color': driver_season.team.primary_color,
        'total_points': current_total,
        'best_position': best_pos if best_pos != 999 else '-',
        'fast_laps': total_fast_laps,
        'labels': json.dumps(labels), # Para o JS
        'data_points': json.dumps(points_cumulative), # Para o JS
        'data_positions': json.dumps(positions), # Para o JS
    }
    return stats

# --- A View Principal ---
def performance_analysis(request, season_id):
    season = get_object_or_404(Season, pk=season_id)
    
    # Pega todos os pilotos inscritos para preencher o Dropdown
    drivers_list = DriverTeamSeason.objects.filter(season=season).select_related('driver').order_by('driver__name')
    
    # Pega IDs da URL (ex: ?p1=1&p2=5)
    p1_id = request.GET.get('p1')
    p2_id = request.GET.get('p2')
    
    # Processa os dados
    driver1_stats = get_driver_performance_data(season, p1_id)
    driver2_stats = get_driver_performance_data(season, p2_id)

    context = {
        'season': season,
        'drivers_list': drivers_list,
        'd1': driver1_stats,
        'd2': driver2_stats,
        'selected_p1': int(p1_id) if p1_id else None,
        'selected_p2': int(p2_id) if p2_id else None,
    }
    return render(request, 'championship/performance.html', context)