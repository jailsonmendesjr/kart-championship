import json
from django.shortcuts import render, get_object_or_404
from django.db.models import Sum, Q
from django.db.models.functions import Coalesce
from .models import Season, DriverTeamSeason, Team, Round

def season_list(request):
    seasons = Season.objects.all().order_by('-year')
    return render(request, 'championship/season_list.html', {'seasons': seasons})

def calculate_standings(season, exclude_last_round=False):
    """
    Função auxiliar que calcula o ranking.
    """
    rounds = season.rounds.all().order_by('order')
    if exclude_last_round and rounds.exists():
        last_round = rounds.last()
        rounds = rounds.exclude(pk=last_round.pk)
    
    # Ranking de Pilotos
    drivers = DriverTeamSeason.objects.filter(season=season).annotate(
        total_points=Coalesce(
            Sum('results__points', filter=Q(results__round__in=rounds)), 
            0
        )
    ).order_by('-total_points', 'driver__name')

    drivers_list = list(drivers)
    for index, entry in enumerate(drivers_list):
        entry.position = index + 1
        
    # Ranking de Equipes
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

    # 1. Calcula o Ranking Atual
    current_drivers, current_teams = calculate_standings(season, exclude_last_round=False)

    # 2. Lógica de Mudança de Posição (Setinhas)
    if rounds_count > 1:
        prev_drivers, prev_teams = calculate_standings(season, exclude_last_round=True)
        prev_drivers_map = {d.driver.id: d.position for d in prev_drivers}
        prev_teams_map = {t.id: t.position for t in prev_teams}

        for driver in current_drivers:
            old_pos = prev_drivers_map.get(driver.driver.id)
            driver.change = (old_pos - driver.position) if old_pos else 0

        for team in current_teams:
            old_pos = prev_teams_map.get(team.id)
            team.change = (old_pos - team.position) if old_pos else 0
    else:
        for d in current_drivers: d.change = 0
        for t in current_teams: t.change = 0

    # 3. Busca as etapas ordenadas da mais recente para a mais antiga (Decrescente)
    rounds_list = season.rounds.all().order_by('-order')

    context = {
        'season': season,
        'drivers_ranking': current_drivers,
        'teams_ranking': current_teams,
        'rounds_list': rounds_list, # <--- Nova variável para o template
    }
    return render(request, 'championship/season_detail.html', context)

def round_detail(request, season_id, round_id):
    season = get_object_or_404(Season, pk=season_id)
    round_obj = get_object_or_404(Round, pk=round_id, season=season)
    results = round_obj.results.select_related('entry__driver', 'entry__team').order_by('position')
    context = { 'season': season, 'round': round_obj, 'results': results }
    return render(request, 'championship/round_detail.html', context)

# --- Função Auxiliar para Performance ---
def get_driver_performance_data(season, driver_id):
    if not driver_id:
        return None
    
    try:
        driver_season = DriverTeamSeason.objects.select_related('driver', 'team').get(
            season=season, driver_id=driver_id
        )
    except DriverTeamSeason.DoesNotExist:
        return None

    rounds = season.rounds.all().order_by('order')
    labels = [] 
    points_cumulative = [] 
    positions = [] 
    
    current_total = 0
    total_fast_laps = 0
    best_pos = 999
    
    for r in rounds:
        labels.append(f"R{r.order}")
        result = driver_season.results.filter(round=r).first()
        
        if result:
            current_total += result.points
            points_cumulative.append(current_total)
            positions.append(result.position)
            if result.fastest_lap: total_fast_laps += 1
            if result.position < best_pos: best_pos = result.position
        else:
            points_cumulative.append(current_total)
            positions.append(None) 

    stats = {
        'name': driver_season.driver.name,
        'team_name': driver_season.team.name,
        'team_color': driver_season.team.primary_color,
        'total_points': current_total,
        'best_position': best_pos if best_pos != 999 else '-',
        'fast_laps': total_fast_laps,
        'labels': json.dumps(labels), 
        'data_points': json.dumps(points_cumulative), 
        'data_positions': json.dumps(positions), 
    }
    return stats

# --- A View Principal de Performance ---
def performance_analysis(request, season_id):
    season = get_object_or_404(Season, pk=season_id)
    drivers_list = DriverTeamSeason.objects.filter(season=season).select_related('driver').order_by('driver__name')
    
    p1_id = request.GET.get('p1')
    p2_id = request.GET.get('p2')
    
    # Processa os dados
    driver1_stats = get_driver_performance_data(season, p1_id)
    driver2_stats = get_driver_performance_data(season, p2_id)

    # --- NOVO: Lógica para diferenciar cores de companheiros de equipe ---
    if driver1_stats and driver2_stats:
        # Se as cores forem idênticas (mesma equipe)
        if driver1_stats['team_color'] == driver2_stats['team_color']:
            # Define uma cor de contraste para o Piloto 2 (Cinza Escuro / Preto Suave)
            driver2_stats['team_color'] = "#374151" 
    # ---------------------------------------------------------------------

    context = {
        'season': season,
        'drivers_list': drivers_list,
        'd1': driver1_stats,
        'd2': driver2_stats,
        'selected_p1': int(p1_id) if p1_id else None,
        'selected_p2': int(p2_id) if p2_id else None,
    }
    return render(request, 'championship/performance.html', context)