"""Explicit engineering rubric, not accuracy, certification or learned reward."""
from .lab_model import SERVING_ID


def assess(report, evaluation):
    compatible = bool(evaluation and evaluation.get('model_id') == report['model_id']
                      and evaluation.get('serving_id') == SERVING_ID)
    plps = [p for s in report['scenarios'].values() for p in s['plps']]
    correct_inventory = bool(plps) and all(len(p['ads']) == 16 and all(a['category'] == p['category'] for a in p['ads']) for p in plps)
    runs = [r for r in (evaluation or {}).get('runs', []) if r['policy'] == 'safe_rl'] if compatible else []
    coverage_passes = sum(all(n >= 1 for n in r['ad_impressions'][1:]) for r in runs)
    all_covered = bool(runs) and coverage_passes == len(runs) and all(p['coverage']['complete'] for p in plps)
    integrity = (evaluation or {}).get('integrity_checks', []) if compatible else []
    controls_pass = bool(integrity) and all(p['passed'] for p in integrity) and all(r['budget_overshoots'] == 0 for r in runs)
    rows = [
        {'name': 'Representación de la PLP', 'maximum': 25, 'before': 5, 'points': 25 if correct_inventory else 0,
         'reason': '16 anuncios propios por categoría y 8 espacios por bloque; sin candidatos de otra PLP.'},
        {'name': 'Aprendizaje y evaluación', 'maximum': 25, 'before': 17, 'points': 18 if compatible else 0,
         'reason': '48 acciones patrocinadas reentrenadas, holdouts y baselines. No demuestra superioridad general ni validez en una tienda real.'},
        {'name': 'Conversión y controles', 'maximum': 20, 'before': 18, 'points': 17 if controls_pass else 0,
         'reason': 'CPC, saldo y primera compra verificados. El filtro de CVR es empírico y la cobertura tiene un costo de oportunidad.'},
        {'name': 'Cobertura de anunciantes', 'maximum': 20, 'before': 8, 'points': 20 if all_covered else 0,
         'reason': f'Los 48 anuncios reciben exposición real en {coverage_passes}/{len(runs)} ejecuciones del agente. Tráfico o saldo insuficientes se declaran pendientes.'},
        {'name': 'Explicación y trazabilidad', 'maximum': 10, 'before': 7, 'points': 8,
         'reason': 'Cohortes 8/8 fijadas por el modelo, mínimo por anuncio, denominadores y causas visibles. Falta validación de comprensión con estudiantes.'},
    ]
    return {'score': sum(r['points'] for r in rows), 'before_score': sum(r['before'] for r in rows),
            'scale': 100, 'type': 'Valoración técnica del demostrador para este caso de uso',
            'complete': compatible, 'rows': rows,
            'coverage_runs_passed': coverage_passes, 'coverage_runs_total': len(runs),
            'note': 'Rúbrica de ingeniería propia; los pesos y puntos son juicios explícitos, no una métrica estadística de precisión ni una certificación.'}
