"""Comandos de entrenamiento, evaluación, campañas y laboratorio interactivo."""
import argparse
from dataclasses import replace
import json
from pathlib import Path

from .agent import QAgent
from .campaign import run_campaign, write_campaign_report
from .config import load_config
from .experiment import evaluate, train
from .reporting import write_report


def main():
    parser = argparse.ArgumentParser(description='Laboratorio de retail media: RL, CPC y simulación interactiva')
    parser.add_argument('command', choices=['run', 'train', 'evaluate', 'campaign', 'lab', 'train-lab', 'evaluate-lab'])
    parser.add_argument('--config', type=Path)
    parser.add_argument('--episodes', type=int, default=120)
    parser.add_argument('--sessions', type=int, help='Sesiones por día/episodio')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--eval-seed', type=int, default=30000)
    parser.add_argument('--eval-runs', type=int, default=30)
    parser.add_argument('--artifacts', type=Path, default=Path('artifacts'))
    parser.add_argument('--reports', type=Path, default=Path('reports'))
    parser.add_argument('--campaign-seed', type=int, default=40000)
    parser.add_argument('--traffic-file', type=Path, help='JSON con una lista de sesiones por día; admite días con cero tráfico')
    parser.add_argument('--policy', choices=['rl', 'random', 'relevance', 'bid', 'rotation', 'organic'], default='rl', help='Política para campaign')
    parser.add_argument('--port', type=int, default=8765, help='Puerto local para lab')
    parser.add_argument('--lab-observations', type=int, default=600000)
    parser.add_argument('--lab-sessions', type=int, default=1000)
    parser.add_argument('--lab-runs', type=int, default=8)
    args = parser.parse_args()
    try:
        if args.command == 'lab':
            from .lab_server import serve
            if not 1024 <= args.port <= 65535:
                raise ValueError('El puerto debe estar entre 1024 y 65535')
            serve(args.port)
            return
        if args.command in ('train-lab', 'evaluate-lab'):
            from .lab_model import LabModel
            from .lab_training import train_lab, evaluate_lab
            if args.command == 'train-lab':
                train_lab(output=args.artifacts / 'lab_model.npz', n=args.lab_observations)
            else:
                model = LabModel.load(args.artifacts / 'lab_model.npz')
                evaluate_lab(model, output=args.reports / 'lab_evaluation.json',
                             sessions=args.lab_sessions, seeds=range(80020, 80020 + args.lab_runs))
            return
        config = load_config(args.config)
        if args.sessions is not None:
            config = replace(config, sessions=args.sessions).validate()
        if args.command == 'campaign':
            agent = QAgent.load(args.artifacts / 'model.npz', config)
            traffic = json.loads(args.traffic_file.read_text(encoding='utf-8')) if args.traffic_file else None
            result = run_campaign(config, agent, args.campaign_seed, traffic, args.policy, verbose=True)
            write_campaign_report(result, args.reports)
            summary = result['summary']
            cvr = 'sin tráfico' if summary['session_cvr'] is None else f"{summary['session_cvr']:.2%} (orgánico {summary['organic_session_cvr']:.2%})"
            print(f'\nCVR de campaña: {cvr}')
            status_labels = {'without_budget': 'sin presupuesto', 'complete': 'presupuesto entregado',
                             'cpc_residual': 'saldo menor que un clic', 'under_target': 'meta de entrega incumplida',
                             'above_minimum_with_balance': 'mínimo cumplido con saldo pendiente'}
            for index, brand in enumerate(config.brands):
                print(f"{brand['name']}: entrega {summary['brand_delivery'][index]:.2%} | saldo USD {summary['remaining_cents'][index] / 100:.2f} | {status_labels[summary['brand_status'][index]]}")
            print('Una campaña continua: sus días no son réplicas independientes ni dan un IC por sí solos.')
            print(f"Reportes: {(args.reports / ('campaign-' + args.policy + '.json')).resolve()}")
            return
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
