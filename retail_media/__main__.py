"""Ejecutar con python -m retail_media run | train | evaluate."""
import argparse
from dataclasses import replace
import json
from pathlib import Path

from .agent import QAgent
from .config import load_config
from .experiment import evaluate, train
from .reporting import write_report


def main():
    parser = argparse.ArgumentParser(description='MVP de retail media RL con CPC')
    parser.add_argument('command', choices=['run', 'train', 'evaluate'])
    parser.add_argument('--config', type=Path)
    parser.add_argument('--episodes', type=int, default=120)
    parser.add_argument('--sessions', type=int, help='Sesiones por día/episodio')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--eval-seed', type=int, default=30000)
    parser.add_argument('--eval-runs', type=int, default=30)
    parser.add_argument('--artifacts', type=Path, default=Path('artifacts'))
    parser.add_argument('--reports', type=Path, default=Path('reports'))
    args = parser.parse_args()
    try:
        config = load_config(args.config)
        if args.sessions is not None:
            config = replace(config, sessions=args.sessions).validate()
        if args.command in ('run', 'train'):
            agent, history = train(config, args.episodes, args.seed, args.artifacts)
        else:
            agent = QAgent.load(args.artifacts / 'model.npz', config)
            history_path = args.artifacts / 'training.json'
            history = json.loads(history_path.read_text()) if history_path.exists() else []
        if args.command != 'train':
            result = evaluate(config, agent, seeds=range(args.eval_seed, args.eval_seed + args.eval_runs))
            write_report(result, history, args.reports)
            print('\nPolítica       CVR       Δ CVR (pp)    Entrega por marca')
            for policy, metrics in result['policies'].items():
                delivery = ' / '.join(f'{v:.0%}' for v in metrics['brand_delivery'])
                print(f"{policy:12} {metrics['session_cvr']:7.2%} {100 * metrics['delta_cvr']:10.2f}       {delivery}")
            print(f'\nReporte: {(args.reports / "demo.html").resolve()}')
    except (ValueError, FileNotFoundError, KeyError, TypeError) as exc:
        parser.exit(2, f'Error: {exc}\n')


if __name__ == '__main__':
    main()
