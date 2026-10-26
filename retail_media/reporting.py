"""Exportación sin servicios externos ni dependencias de gráficos."""
import csv
import json
from pathlib import Path


def write_report(result, history, output=Path('reports')):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output / 'evaluation.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    with (output / 'evaluation.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(result['runs'][0]))
        writer.writeheader()
        writer.writerows(result['runs'])
    data = json.dumps({'result': result, 'history': history}, ensure_ascii=False).replace('<', '\\u003c')
    template = Path(__file__).with_name('report.html').read_text(encoding='utf-8')
    (output / 'demo.html').write_text(template.replace('__RESULTS__', data), encoding='utf-8')
