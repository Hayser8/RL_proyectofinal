"""Local SKUs and display metadata for the 48-ad PLP model.

Each category owns 16 advertised SKUs and 20 organic SKUs. Pictures and retail
prices are presentation metadata, never extra observations for the model.
"""
from .lab_model import CATALOGUE, organic_product

CATEGORY_KEYS = ('tech', 'home', 'sport')
ORGANIC = (
    (
        ('Teclado compacto Menta', 5900), ('Mouse ergonómico Marfil', 3500),
        ('Audífonos inalámbricos Terra', 6900), ('Parlante portátil Azul', 7900),
        ('SSD portátil Naranja · 1 TB', 9900), ('Cámara web Focus', 4900),
        ('Control de juego Lila', 6500), ('Lector digital Salvia', 12900),
        ('Batería portátil Noche', 4500), ('Base de carga Vertical', 3900),
        ('Miniproyector Nube', 18900), ('Auriculares de estudio Plata', 10900),
        ('Micrófono de escritorio Coral', 8500), ('Tableta de dibujo Trazo', 11900),
        ('Reloj de escritorio Alba', 2900), ('Cámara instantánea Luz', 9900),
        ('Hub USB Mostaza', 3200), ('Consola portátil Roja', 14900),
        ('Router de doble antena', 7500), ('Cámara compacta Aqua', 15900),
    ),
    (
        ('Olla de hierro Oliva', 8900), ('Florero de vidrio Ámbar', 2800),
        ('Cojín de lino Arena', 2400), ('Manta tejida Avena', 4500),
        ('Tabla de bambú Cocina', 2200), ('Taza de cerámica Brisa', 1400),
        ('Prensa francesa Acero', 3900), ('Maceta con planta Terra', 2700),
        ('Regadera de jardín Azul', 2500), ('Reloj de mesa Latón', 4900),
        ('Organizador de madera', 3200), ('Cesta tejida Coral', 3600),
        ('Jarra de vidrio Clara', 1900), ('Boles de cerámica Crema', 3400),
        ('Ventilador de mesa Bosque', 5900), ('Bandeja de madera Natural', 2900),
        ('Difusor de varillas Ámbar', 2300), ('Cesto de ropa Grafito', 4200),
        ('Lámpara de pie Lino', 7900), ('Frasco de cocina Nórdico', 1800),
    ),
    (
        ('Zapatillas de running Azules', 8900), ('Mancuernas Lila · par', 4500),
        ('Botella térmica Naranja', 2900), ('Mat de yoga Aqua', 3500),
        ('Guantes de boxeo Negros', 5900), ('Casco de ciclismo Rojo', 6900),
        ('Balón de fútbol Clásico', 3200), ('Mochila de senderismo Sol', 7900),
        ('Raqueta de tenis Turquesa', 9900), ('Rodillo de espuma Gris', 2400),
        ('Cuerda para saltar Lima', 1600), ('Pesa rusa Azul', 4900),
        ('Bandas de resistencia Rosa', 2200), ('Balón de baloncesto Cancha', 3900),
        ('Aro de pilates Rojo', 2700), ('Botas de senderismo Roca', 11900),
        ('Balón de voleibol Lima', 3400), ('Bolso de gimnasio Blanco', 5500),
        ('Step de entrenamiento Negro', 6500), ('Rodilleras deportivas Azules', 2500),
    ),
)
# The same SKUs can be bought organically or advertised; 16 per category.
SPONSORED = tuple(category[:16] for category in ORGANIC)


def present_product(product, depth=0):
    """Return a copy with display metadata, without mutating learned catalogue."""
    category = int(product['category_id'])
    key = CATEGORY_KEYS[category]
    action = int(product['action'])
    if action:
        index = int(product['variant'])
        name, price = SPONSORED[category][index]
        name = f"{product['brand']} {name}"
        image_key = f'{key}-organic-{index:02d}'
    else:
        # Reorder the real catalogue between blocks without consuming the RNG
        # that controls simulated outcomes or inventing duplicate SKU identities.
        position = int(product['id'].rsplit('-', 1)[-1])
        index = (position - 1 + int(depth) * 7) % len(ORGANIC[category])
        name, price = ORGANIC[category][index]
        image_key = f'{key}-organic-{index:02d}'
    return {**product, 'name': name, 'price_cents': price,
            'image_key': image_key, 'catalogue_id': image_key}


def present_candidate(candidate, context):
    action = int(candidate['action'])
    raw = CATALOGUE[action - 1] if action else organic_product(context['segment'], context['position'])
    display = present_product(raw, context.get('catalogue_rotation', context['depth']))
    return {**candidate, 'name': display['name'], 'image_key': display['image_key'],
            'catalogue_id': display['catalogue_id'], 'price_cents': display['price_cents']}
