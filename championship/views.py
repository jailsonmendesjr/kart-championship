import json
from django.shortcuts import render, get_object_or_404
from .models import Season, DriverTeamSeason, Team, Round, RoundResult

def season_list(request):
    seasons = Season.objects.all().order_by('-year')
    return render(request, 'championship/season_list.html', {'seasons': seasons})

def calculate_standings(season, exclude_last_round=False):
    """
    Novo motor de cálculo 100% Python. Seguro, rápido e preparado para a futura regra de Descartes.
    """
    # 1. Pega as etapas válidas
    rounds = list(season.rounds.all().order_by('order'))
    if exclude_last_round and rounds:
        rounds = rounds[:-1]
        
    round_ids = [r.id for r in rounds]
    
    # 2. Pega as inscrições de pilotos da temporada (A MÁGICA DOS CONVIDADOS AQUI)
    # Ao adicionar is_guest=False, o sistema ignora por completo os convidados na matemática global.
    drivers = list(DriverTeamSeason.objects.filter(
        season=season, 
        is_guest=False
    ).select_related('driver', 'team'))
    
    # Prepara o contador
    for d in drivers:
        d.total_points = 0
        d.wins = 0

    # ... (o resto da função calculate_standings continua exatamente igual ao que já tem)

    # 3. Pega todos os resultados e processa um a um
    results = RoundResult.objects.filter(round_id__in=round_ids).select_related('entry')
    
    for res in results:
        for d in drivers:
            if d.id == res.entry_id:
                d.total_points += res.points
                if res.status == 'COMPLETED':
                    # Conta vitórias
                    if res.position == 1:
                        d.wins += 1
                    # Conta pódios (1º, 2º e 3º)
                    if res.position in [1, 2, 3]:
                        if not hasattr(d, 'podiums'):
                            d.podiums = 0
                        d.podiums += 1
                break
    
    # Garante que o atributo podiums existe, mesmo que seja zero, para o desempate
    for d in drivers:
        if not hasattr(d, 'podiums'):
            d.podiums = 0

    # 4. Ordenação Profissional (Desempates Atualizados)
    drivers.sort(key=lambda x: x.driver.name.lower())
    # NOVO DESEMPATE: Pontos > Vitórias > Pódios
    drivers.sort(key=lambda x: (x.total_points, x.wins, x.podiums), reverse=True)
    
    for index, d in enumerate(drivers):
        d.position = index + 1
        
    # 5. Cálculo das Equipes
    teams_dict = {}
    for d in drivers:
        if d.team_id not in teams_dict:
            teams_dict[d.team_id] = {
                'team': d.team,
                'total_points': 0,
                'wins': 0,
                'podiums': 0,
                'drivers_list': [] # NOVO: Lista para guardar os pilotos desta equipe
            }
        # Guarda o piloto dentro da sua respectiva equipe
        teams_dict[d.team_id]['drivers_list'].append(d)
            
    for res in results:
        team_id = res.entry.team_id
        if team_id in teams_dict:
            teams_dict[team_id]['total_points'] += res.points
            if res.status == 'COMPLETED':
                if res.position == 1:
                    teams_dict[team_id]['wins'] += 1
                if res.position in [1, 2, 3]:
                    teams_dict[team_id]['podiums'] += 1
                
    teams_list = []
    for team_id, data in teams_dict.items():
        team_obj = data['team']
        team_obj.total_points = data['total_points']
        team_obj.wins = data['wins']
        team_obj.podiums = data['podiums']
        
        # --- A MÁGICA DOS PILOTOS DA EQUIPE AQUI ---
        # 1. Ordena os pilotos da equipe por quem tem mais pontos (reverse=True)
        sorted_drivers = sorted(data['drivers_list'], key=lambda x: x.total_points, reverse=True)
        # 2. Pega só o primeiro nome (split()[0]) e monta a string: "Nome (Pontos)"
        team_obj.drivers_summary = " • ".join([f"{d.driver.name.split()[0]} ({d.total_points})" for d in sorted_drivers])
        
        teams_list.append(team_obj)
        
    teams_list.sort(key=lambda x: x.name.lower())
    # NOVO DESEMPATE EQUIPES: Pontos > Vitórias > Pódios
    teams_list.sort(key=lambda x: (x.total_points, x.wins, x.podiums), reverse=True)
    
    for index, t in enumerate(teams_list):
        t.position = index + 1
        
    return drivers, teams_list

def season_detail(request, season_id):
    season = get_object_or_404(Season, pk=season_id)
    rounds_count = season.rounds.count()

    current_drivers, current_teams = calculate_standings(season, exclude_last_round=False)

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

    rounds_list = season.rounds.all().order_by('-order')

    # NOVO: Descobre o vencedor de cada etapa para exibir no card do mobile
    for r in rounds_list:
        # Tenta achar o resultado de 1º lugar finalizado
        winner_result = r.results.filter(position=1, status='COMPLETED').first()
        if winner_result:
            # Pega só o primeiro nome para não quebrar o layout no celular
            r.winner = winner_result.entry.driver.name.split()[0]
        else:
            r.winner = None

    context = {
        'season': season,
        'drivers_ranking': current_drivers,
        'teams_ranking': current_teams,
        'rounds_list': rounds_list,
    }
    return render(request, 'championship/season_detail.html', context)

def round_detail(request, season_id, round_id):
    season = get_object_or_404(Season, pk=season_id)
    round_obj = get_object_or_404(Round, pk=round_id, season=season)
    results = round_obj.results.select_related('entry__driver', 'entry__team').order_by('position')
    context = { 'season': season, 'round': round_obj, 'results': results }
    return render(request, 'championship/round_detail.html', context)

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

def performance_analysis(request, season_id):
    season = get_object_or_404(Season, pk=season_id)
    drivers_list = DriverTeamSeason.objects.filter(season=season).select_related('driver').order_by('driver__name')
    
    p1_id = request.GET.get('p1')
    p2_id = request.GET.get('p2')
    
    driver1_stats = get_driver_performance_data(season, p1_id)
    driver2_stats = get_driver_performance_data(season, p2_id)

    if driver1_stats and driver2_stats:
        if driver1_stats['team_color'] == driver2_stats['team_color']:
            driver2_stats['team_color'] = "#374151" 

    context = {
        'season': season,
        'drivers_list': drivers_list,
        'd1': driver1_stats,
        'd2': driver2_stats,
        'selected_p1': int(p1_id) if p1_id else None,
        'selected_p2': int(p2_id) if p2_id else None,
    }
    return render(request, 'championship/performance.html', context)