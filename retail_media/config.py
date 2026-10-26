"""Configuración validada; todo importe monetario se expresa en centavos USD."""
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path


@dataclass(frozen=True)
class Config:
    sessions: int
    campaign_days: int
    block_size: int
    sponsored_slots: tuple[int, ...]
    categories: tuple[str, ...]
    brands: tuple[dict, ...]
    cvr_tolerance: float = 0.0
    minimum_delivery: float = .9
    pacing_slack: float = .075

    def validate(self):
        for name in ('sessions', 'campaign_days', 'block_size'):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise ValueError(f'{name} debe ser un entero positivo')
        if self.block_size != 20 or self.sponsored_slots != (3, 4, 5, 6, 11, 12, 13, 14):
            raise ValueError('Este MVP utiliza bloques de 20 y los ocho spots especificados')
        if len(self.brands) != 3 or len(self.categories) != 3:
            raise ValueError('Este MVP requiere tres marcas y tres categorías')
        for brand in self.brands:
            if not isinstance(brand.get('name'), str) or not brand['name'].strip():
                raise ValueError('Cada marca necesita nombre')
            for key in ('budget_cents', 'cpc_cents'):
                value = brand.get(key)
                if type(value) is not int or value < (1 if key == 'cpc_cents' else 0):
                    raise ValueError(f'{key} inválido')
        if len({b['name'] for b in self.brands}) != len(self.brands):
            raise ValueError('Los nombres de marca deben ser únicos')
        if not 0 <= self.cvr_tolerance <= 1 or not 0 <= self.minimum_delivery <= 1 or not 0 < self.pacing_slack < 1:
            raise ValueError('Umbrales fuera de rango')
        return self

    def fingerprint(self):
        # Traffic volume may change at evaluation; catalog and economics may not.
        payload = asdict(self)
        payload.pop('sessions')
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def load_config(path=None):
    source = Path(path) if path else Path(__file__).with_name('default_config.json')
    values = json.loads(source.read_text(encoding='utf-8'))
    for key in ('sponsored_slots', 'categories', 'brands'):
        values[key] = tuple(values[key])
    return Config(**values).validate()
