"""Campañas secuenciales: saldo y atraso reales entre días, importes en centavos."""
from copy import deepcopy
import csv
from dataclasses import asdict, replace
import json
from pathlib import Path

import numpy as np

from .environment import RetailMediaEnv
from .experiment import choose_action


class CampaignLedger:
    def __init__(self, config):
        self.config = config.validate()
        self.totals = tuple(b['budget_cents'] for b in config.brands)
        self._spent = [0, 0, 0]
        self.day = 0
        self._allocation = None

    @property
    def spent(self):
        return self._spent.copy()

    def start_day(self):
        if self._allocation is not None:
            raise RuntimeError('Cierra el día actual antes de abrir otro')
        if self.day >= self.config.campaign_days:
            raise RuntimeError('La campaña terminó')
        # Cumulative rounding restores all fractional cents on the final day.
        self._allocation = [total * (self.day + 1) // self.config.campaign_days - spent
                            for total, spent in zip(self.totals, self._spent)]
        return self._allocation.copy()

    def finish_day(self, spent_cents):
        if self._allocation is None:
            raise RuntimeError('No hay un día abierto')
        if (not isinstance(spent_cents, (list, tuple)) or len(spent_cents) != 3
                or any(type(v) is not int or not 0 <= v <= limit
                       for v, limit in zip(spent_cents, self._allocation))):
            raise ValueError('Gasto inválido o superior a la asignación del día')
        self._spent = [past + current for past, current in zip(self._spent, spent_cents)]
        target = [total * (self.day + 1) // self.config.campaign_days for total in self.totals]
        row = {'day': self.day + 1, 'allocation_cents': self._allocation.copy(),
               'target_cents': target, 'spend_cents': list(spent_cents),
               'cumulative_spend_cents': self.spent,
               'carryover_cents': [goal - spent for goal, spent in zip(target, self._spent)],
               'remaining_cents': [total - spent for total, spent in zip(self.totals, self._spent)]}
        self._allocation = None
        self.day += 1
        return row


def run_campaign(config, agent, seed=40000, sessions_per_day=None, policy='rl', verbose=False):
    """Evaluate a frozen policy across one campaign; days are not independent runs."""
    config.validate()
    if policy not in ('rl', 'random', 'relevance', 'organic'):
        raise ValueError('Política de campaña desconocida')
    if type(seed) is not int or seed < 0:
        raise ValueError('seed debe ser un entero no negativo')
    if agent.metadata.get('config_fingerprint', config.fingerprint()) != config.fingerprint():
        raise ValueError('El modelo no corresponde a la configuración de campaña')
    schedule = [config.sessions] * config.campaign_days if sessions_per_day is None else sessions_per_day
    if (not isinstance(schedule, (list, tuple)) or len(schedule) != config.campaign_days
            or any(type(v) is not int or v < 0 for v in schedule)):
        raise ValueError('El tráfico debe indicar sesiones enteras no negativas para cada día')
    seeds = list(range(seed, seed + config.campaign_days))
    if set(seeds) & set(agent.metadata.get('training_seeds', [])):
        raise ValueError('Las semillas de campaña coinciden con entrenamiento')
    ledger = CampaignLedger(config)
    actor = deepcopy(agent)
    actor.rng = np.random.default_rng(seed + 1000000)
    rng = np.random.default_rng(seed + 2000000)
    days = []
    for index, sessions in enumerate(schedule):
        allocation = ledger.start_day()
        if sessions:
            env = RetailMediaEnv(replace(config, sessions=sessions), seeds[index], budget_cents=allocation)
            while not env.done:
                env.step(choose_action(policy, env, actor, rng))
            metrics = env.metrics()
        else:
            metrics = {'sessions': 0, 'converted_sessions': 0, 'organic_converted_sessions': 0,
                       'session_cvr': None, 'organic_session_cvr': None,
                       'spend_cents': [0, 0, 0], 'sponsored_clicks': 0,
                       'sponsored_impressions': 0}
        row = ledger.finish_day(metrics['spend_cents'])
        row.update(seed=seeds[index], metrics=metrics)
        days.append(row)
        if verbose and (index == 0 or (index + 1) % 7 == 0 or index + 1 == config.campaign_days):
            print(f"Día {index + 1}/{config.campaign_days}: {sessions} sesiones | gasto acumulado USD {sum(ledger.spent) / 100:.2f}", flush=True)
    total_sessions = sum(schedule)
    converted = sum(row['metrics']['converted_sessions'] for row in days)
    organic_converted = sum(row['metrics']['organic_converted_sessions'] for row in days)
    cvr = converted / total_sessions if total_sessions else None
    organic_cvr = organic_converted / total_sessions if total_sessions else None
    remaining = [total - spent for total, spent in zip(ledger.totals, ledger.spent)]
    delivery = [spent / total if total else 1. for spent, total in zip(ledger.spent, ledger.totals)]
    status = ['without_budget' if not total else 'complete' if not balance else 'cpc_residual'
              if balance < brand['cpc_cents'] else 'under_target'
              if ratio < config.minimum_delivery else 'above_minimum_with_balance'
              for total, balance, brand, ratio in zip(ledger.totals, remaining, config.brands, delivery)]
    return {'config': asdict(config), 'policy': policy, 'seeds': seeds,
            'sessions_per_day': list(schedule), 'model_metadata': deepcopy(agent.metadata),
            'evaluation_mode': 'single_continuous_campaign', 'days': days,
            'summary': {'sessions': total_sessions, 'converted_sessions': converted,
                        'organic_converted_sessions': organic_converted,
                        'session_cvr': cvr, 'organic_session_cvr': organic_cvr,
                        'delta_cvr': cvr - organic_cvr if total_sessions else None,
                        'cvr_point_pass': cvr - organic_cvr >= -config.cvr_tolerance if total_sessions else None,
                        'spend_cents': ledger.spent, 'remaining_cents': remaining,
                        'brand_delivery': delivery, 'brand_status': status,
                        'delivery_pass': all(v >= config.minimum_delivery for v in delivery),
                        'budget_overshoots': sum(s > t for s, t in zip(ledger.spent, ledger.totals))}}


def write_campaign_report(result, output=Path('reports')):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    stem = f"campaign-{result['policy']}"
    (output / f'{stem}.json').write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')
    fields = ['day', 'seed', 'sessions', 'session_cvr', 'organic_session_cvr', 'brand',
              'allocation_cents', 'target_cents', 'spend_cents', 'cumulative_spend_cents',
              'carryover_cents', 'remaining_cents']
    with (output / f'{stem}.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        for day in result['days']:
            for index, brand in enumerate(result['config']['brands']):
                row = {key: day[key] for key in ['day', 'seed']}
                row.update({key: day['metrics'][key] for key in ['sessions', 'session_cvr', 'organic_session_cvr']})
                row['brand'] = brand['name']
                row.update({key: day[key][index] for key in fields[6:]})
                writer.writerow(row)
