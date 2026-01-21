# ============================================
# RUTAS PÚBLICAS - LANDING PAGE Y CATÁLOGO (ACTUALIZADO)
# ============================================
# Blueprint para la landing page y catálogo público
# sin requerir autenticación

from flask import Blueprint, render_template, request, jsonify, abort, url_for, redirect
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, or_, case
from app import db
from app.models.laptop import Laptop, Brand, LaptopImage, Processor, GraphicsCard, Screen, Storage, Ram, \
    OperatingSystem, LaptopModel
from datetime import datetime, timedelta

# ============================================
# CREAR BLUEPRINT PÚBLICO
# ============================================

public_bp = Blueprint(
    'public',
    __name__,
    url_prefix='',
)


# ============================================
# RUTA: LANDING PAGE PRINCIPAL
# ============================================

@public_bp.route('/')
def landing():
    """
    Landing page principal del sitio
    URL: /
    """
    # Obtener productos destacados (máximo 6) CON imágenes precargadas
    featured_laptops = Laptop.query.options(
        joinedload(Laptop.images)
    ).filter(
        Laptop.is_published == True,
        Laptop.is_featured == True,
        Laptop.quantity > 0
    ).order_by(
        Laptop.created_at.desc()
    ).limit(6).all()

    # Si no hay productos destacados, mostrar los más recientes
    if not featured_laptops:
        featured_laptops = Laptop.query.options(
            joinedload(Laptop.images)
        ).filter(
            Laptop.is_published == True,
            Laptop.quantity > 0
        ).order_by(
            Laptop.created_at.desc()
        ).limit(6).all()

    # Estadísticas para mostrar en la landing
    total_products = Laptop.query.filter_by(is_published=True).count()

    return render_template(
        'landing/home.html',
        featured_laptops=featured_laptops,
        total_products=total_products
    )


# ============================================
# RUTA: CATÁLOGO PÚBLICO - NUEVO DISEÑO CON ALPINE.JS
# ============================================

@public_bp.route('/catalog')
def catalog():
    """
    Catálogo público de productos - Nueva versión con filtros en cliente
    URL: /catalog
    """
    # Obtener todos los productos publicados con stock y relaciones necesarias
    laptops = Laptop.query.options(
        joinedload(Laptop.images),
        joinedload(Laptop.brand),
        joinedload(Laptop.processor),
        joinedload(Laptop.ram),
        joinedload(Laptop.storage),
        joinedload(Laptop.screen),
        joinedload(Laptop.graphics_card),
        joinedload(Laptop.operating_system),
        joinedload(Laptop.model)  # Esta relación YA está siendo cargada
    ).filter(
        Laptop.is_published == True,
        Laptop.quantity > 0
    ).order_by(
        Laptop.created_at.desc()
    ).all()

    # Obtener datos únicos para filtros desde la base de datos
    # Marcas
    brands = Brand.query.filter_by(is_active=True).order_by(Brand.name).all()

    # Procesadores únicos de productos publicados
    processor_subquery = db.session.query(Laptop.processor_id).filter(
        Laptop.is_published == True,
        Laptop.quantity > 0,
        Laptop.processor_id.isnot(None)
    ).distinct().subquery()
    processors = Processor.query.join(
        processor_subquery, Processor.id == processor_subquery.c.processor_id
    ).order_by(Processor.name).all()

    # GPUs únicas
    gpu_subquery = db.session.query(Laptop.graphics_card_id).filter(
        Laptop.is_published == True,
        Laptop.quantity > 0,
        Laptop.graphics_card_id.isnot(None)
    ).distinct().subquery()
    gpus = GraphicsCard.query.join(
        gpu_subquery, GraphicsCard.id == gpu_subquery.c.graphics_card_id
    ).order_by(GraphicsCard.name).all()

    # Pantallas únicas
    screen_subquery = db.session.query(Laptop.screen_id).filter(
        Laptop.is_published == True,
        Laptop.quantity > 0,
        Laptop.screen_id.isnot(None)
    ).distinct().subquery()
    screens = Screen.query.join(
        screen_subquery, Screen.id == screen_subquery.c.screen_id
    ).order_by(Screen.name).all()

    # RAMs únicas
    ram_subquery = db.session.query(Laptop.ram_id).filter(
        Laptop.is_published == True,
        Laptop.quantity > 0,
        Laptop.ram_id.isnot(None)
    ).distinct().subquery()
    rams = Ram.query.join(
        ram_subquery, Ram.id == ram_subquery.c.ram_id
    ).order_by(Ram.name).all()

    # Almacenamientos únicos
    storage_subquery = db.session.query(Laptop.storage_id).filter(
        Laptop.is_published == True,
        Laptop.quantity > 0,
        Laptop.storage_id.isnot(None)
    ).distinct().subquery()
    storages = Storage.query.join(
        storage_subquery, Storage.id == storage_subquery.c.storage_id
    ).order_by(Storage.name).all()

    # Modelos únicos de productos publicados
    model_subquery = db.session.query(Laptop.model_id).filter(
        Laptop.is_published == True,
        Laptop.quantity > 0,
        Laptop.model_id.isnot(None)
    ).distinct().subquery()
    models = LaptopModel.query.join(
        model_subquery, LaptopModel.id == model_subquery.c.model_id
    ).order_by(LaptopModel.name).all()

    # Calcular rango de precios real de productos
    price_range = db.session.query(
        db.func.min(
            case(
                (Laptop.discount_price != None, Laptop.discount_price),
                else_=Laptop.sale_price
            )
        ),
        db.func.max(
            case(
                (Laptop.discount_price != None, Laptop.discount_price),
                else_=Laptop.sale_price
            )
        )
    ).filter(
        Laptop.is_published == True,
        Laptop.quantity > 0
    ).first()

    min_price_available = float(price_range[0]) if price_range[0] else 500
    max_price_available = float(price_range[1]) if price_range[1] else 8000

    # Categorías predefinidas para el filtro
    categories = [
        {'id': 'laptop', 'name': 'Laptop', 'icon': 'ph-laptop'},
        {'id': 'gaming', 'name': 'Gaming', 'icon': 'ph-game-controller'},
        {'id': 'workstation', 'name': 'Workstation', 'icon': 'ph-cpu'}
    ]

    # Condiciones disponibles - IMPORTANTE: debe coincidir con lo que usa el template
    conditions = ['new', 'used', 'refurbished']

    # Pasar los datos con nombres exactos que espera el template
    return render_template(
        'landing/catalog.html',
        laptops=laptops,  # Para flaskLaptops
        brands=brands,  # Para brandsList
        processors=processors,  # Para cpuList
        gpus=gpus,  # Para gpuList
        screens=screens,  # Para screenList
        rams=rams,  # Para ramList
        storages=storages,  # Para ssdList
        conditions=conditions,  # Para conditionList
        categories=categories,  # Para categories
        models=models,  # Para modelList - NUEVO: agregar modelos disponibles
        min_price_available=int(min_price_available),
        max_price_available=int(max_price_available),
        total_products=len(laptops)
    )

# ============================================
# RUTA: DETALLE DE PRODUCTO (REDIRECCIÓN POR ID)
# ============================================

@public_bp.route('/product/<int:id>')
@public_bp.route('/laptop/<int:id>')
def product_detail(id):
    """
    Redirige al detalle de producto por slug
    URL: /product/<id> -> redirige a /product/<slug>
    URL: /laptop/<id> -> redirige a /laptop/<slug>
    """
    # Obtener la laptop por ID
    laptop = Laptop.query.get_or_404(id)

    # Verificar que esté publicado
    if not laptop.is_published:
        abort(404)

    # Redirigir a la ruta con slug
    return redirect(url_for('public.product_detail_slug', slug=laptop.slug))


# ============================================
# RUTA: DETALLE DE PRODUCTO POR SLUG
# ============================================

@public_bp.route('/product/<slug>')
@public_bp.route('/laptop/<slug>')
def product_detail_slug(slug):
    """
    Detalle público de un producto por slug
    URL: /product/<slug>
    URL: /laptop/<slug>
    """
    # Obtener la laptop con todas las relaciones necesarias por slug
    laptop = Laptop.query.options(
        joinedload(Laptop.brand),
        joinedload(Laptop.processor),
        joinedload(Laptop.ram),
        joinedload(Laptop.storage),
        joinedload(Laptop.screen),
        joinedload(Laptop.graphics_card),
        joinedload(Laptop.operating_system),
        joinedload(Laptop.model),
        joinedload(Laptop.images)
    ).filter_by(
        slug=slug,
        is_published=True
    ).first_or_404()

    # Obtener imágenes ordenadas
    images = sorted(laptop.images, key=lambda img: img.ordering if img.ordering else 0)

    # Imagen de portada
    cover_image = next((img for img in laptop.images if img.is_cover), None)

    # Obtener laptops similares (misma categoría y marca)
    similar_laptops = Laptop.query.filter(
        and_(
            Laptop.category == laptop.category,
            Laptop.brand_id == laptop.brand_id,
            Laptop.id != laptop.id,
            Laptop.is_published == True,
            Laptop.quantity > 0
        )
    ).limit(4).all()

    return render_template(
        'landing/product_datail.html',
        laptop=laptop,
        similar_laptops=similar_laptops,
        images=images,
        cover_image=cover_image
    )


# ============================================
# API PARA EL NUEVO CATÁLOGO
# ============================================

@public_bp.route('/api/laptops')
def api_laptops():
    """API para obtener laptops en formato JSON (para Alpine.js)"""
    laptops = Laptop.query.options(
        joinedload(Laptop.images),
        joinedload(Laptop.brand),
        joinedload(Laptop.processor),
        joinedload(Laptop.graphics_card),
        joinedload(Laptop.screen),
        joinedload(Laptop.ram),
        joinedload(Laptop.storage),
        joinedload(Laptop.operating_system),
        joinedload(Laptop.model)  # NUEVO: incluir modelo en la API
    ).filter(
        Laptop.is_published == True,
        Laptop.quantity > 0
    ).all()

    laptops_data = []
    for laptop in laptops:
        # Obtener imagen de portada
        cover_image = next((img for img in laptop.images if img.is_cover), None)
        image_url = None
        if cover_image:
            image_url = url_for('static', filename=cover_image.image_path, _external=True)
        elif laptop.images and len(laptop.images) > 0:
            image_url = url_for('static', filename=laptop.images[0].image_path, _external=True)
        else:
            image_url = url_for('static', filename='images/default-laptop.jpg', _external=True)

        # Determinar si es nuevo (menos de 30 días desde entry_date)
        is_new = False
        if laptop.entry_date:
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            is_new = laptop.entry_date > thirty_days_ago

        # Determinar si está en oferta
        is_sale = laptop.discount_price and float(laptop.discount_price) < float(laptop.sale_price)

        # Mapear condición a texto legible
        condition_display = 'Nuevo'
        if laptop.condition == 'used':
            condition_display = 'Usado'
        elif laptop.condition == 'refurbished':
            condition_display = 'Reacondicionado'

        laptop_data = {
            'id': laptop.id,
            'sku': laptop.sku,
            'name': laptop.display_name,
            'brand': laptop.brand.name if laptop.brand else 'Sin marca',
            'model': laptop.model.name if laptop.model else 'Sin modelo',  # NUEVO: agregar campo modelo
            'category': laptop.category or 'laptop',
            'price': float(laptop.sale_price),
            'old_price': float(laptop.discount_price) if laptop.discount_price and float(laptop.discount_price) < float(
                laptop.sale_price) else None,
            'gpu': laptop.graphics_card.name if laptop.graphics_card else 'Integrada',
            'cpu': laptop.processor.name if laptop.processor else 'Sin especificar',
            'ram': laptop.ram.name if laptop.ram else 'No especificado',
            'ssd': laptop.storage.name if laptop.storage else 'No especificado',
            'screen': laptop.screen.name if laptop.screen else 'No especificado',
            'condition': laptop.condition or 'new',
            'condition_display': condition_display,
            'os': laptop.operating_system.name if laptop.operating_system else 'No especificado',
            'image': image_url,
            'entry_date': laptop.entry_date.isoformat() if laptop.entry_date else None,
            'is_new': is_new,
            'is_sale': is_sale,
            'quantity': laptop.quantity,
            'short_description': laptop.short_description or ''
        }
        laptops_data.append(laptop_data)

    return jsonify(laptops_data)


@public_bp.route('/api/filters')
def api_filters():
    """API para obtener opciones de filtros"""
    # Obtener solo valores que existen en productos publicados
    brand_subquery = db.session.query(Laptop.brand_id).filter(
        Laptop.is_published == True,
        Laptop.quantity > 0
    ).distinct().subquery()

    brands = Brand.query.join(
        brand_subquery, Brand.id == brand_subquery.c.brand_id
    ).filter(Brand.is_active == True).order_by(Brand.name).all()

    processor_subquery = db.session.query(Laptop.processor_id).filter(
        Laptop.is_published == True,
        Laptop.quantity > 0,
        Laptop.processor_id.isnot(None)
    ).distinct().subquery()

    processors = Processor.query.join(
        processor_subquery, Processor.id == processor_subquery.c.processor_id
    ).order_by(Processor.name).all()

    gpu_subquery = db.session.query(Laptop.graphics_card_id).filter(
        Laptop.is_published == True,
        Laptop.quantity > 0,
        Laptop.graphics_card_id.isnot(None)
    ).distinct().subquery()

    gpus = GraphicsCard.query.join(
        gpu_subquery, GraphicsCard.id == gpu_subquery.c.graphics_card_id
    ).order_by(GraphicsCard.name).all()

    screen_subquery = db.session.query(Laptop.screen_id).filter(
        Laptop.is_published == True,
        Laptop.quantity > 0,
        Laptop.screen_id.isnot(None)
    ).distinct().subquery()

    screens = Screen.query.join(
        screen_subquery, Screen.id == screen_subquery.c.screen_id
    ).order_by(Screen.name).all()

    ram_subquery = db.session.query(Laptop.ram_id).filter(
        Laptop.is_published == True,
        Laptop.quantity > 0,
        Laptop.ram_id.isnot(None)
    ).distinct().subquery()

    rams = Ram.query.join(
        ram_subquery, Ram.id == ram_subquery.c.ram_id
    ).order_by(Ram.name).all()

    storage_subquery = db.session.query(Laptop.storage_id).filter(
        Laptop.is_published == True,
        Laptop.quantity > 0,
        Laptop.storage_id.isnot(None)
    ).distinct().subquery()

    storages = Storage.query.join(
        storage_subquery, Storage.id == storage_subquery.c.storage_id
    ).order_by(Storage.name).all()

    # NUEVO: obtener modelos únicos de productos publicados
    model_subquery = db.session.query(Laptop.model_id).filter(
        Laptop.is_published == True,
        Laptop.quantity > 0,
        Laptop.model_id.isnot(None)
    ).distinct().subquery()

    models = LaptopModel.query.join(
        model_subquery, LaptopModel.id == model_subquery.c.model_id
    ).order_by(LaptopModel.name).all()

    filters_data = {
        'brands': [{'id': b.id, 'name': b.name} for b in brands],
        'processors': [{'id': p.id, 'name': p.name} for p in processors],
        'gpus': [{'id': g.id, 'name': g.name} for g in gpus],
        'screens': [{'id': s.id, 'name': s.name} for s in screens],
        'rams': [{'id': r.id, 'name': r.name} for r in rams],
        'storages': [{'id': s.id, 'name': s.name} for s in storages],
        'models': [{'id': m.id, 'name': m.name} for m in models],  # NUEVO: agregar modelos a filtros
        'categories': [
            {'id': 'laptop', 'name': 'Laptop'},
            {'id': 'gaming', 'name': 'Gaming'},
            {'id': 'workstation', 'name': 'Workstation'}
        ],
        'conditions': [
            {'id': 'new', 'name': 'Nuevo'},
            {'id': 'used', 'name': 'Usado'},
            {'id': 'refurbished', 'name': 'Reacondicionado'}
        ]
    }

    return jsonify(filters_data)


# ============================================
# API: BÚSQUEDA RÁPIDA (AUTOCOMPLETE)
# ============================================

@public_bp.route('/api/search')
def api_search():
    """
    API de búsqueda rápida para autocomplete
    URL: /api/search?q=<query>
    """
    query = request.args.get('q', '').strip()

    if not query or len(query) < 2:
        return jsonify([])

    # Buscar en nombre, marca y SKU
    results = Laptop.query.join(Brand).filter(
        Laptop.is_published == True,
        Laptop.quantity > 0,
        or_(
            Laptop.display_name.ilike(f'%{query}%'),
            Brand.name.ilike(f'%{query}%'),
            Laptop.sku.ilike(f'%{query}%'),
            Laptop.short_description.ilike(f'%{query}%')
        )
    ).limit(5).all()

    suggestions = []
    for laptop in results:
        cover_image = next((img for img in laptop.images if img.is_cover), None)
        image_url = None
        if cover_image:
            image_url = url_for('static', filename=cover_image.image_path)
        elif laptop.images and len(laptop.images) > 0:
            image_url = url_for('static', filename=laptop.images[0].image_path)

        suggestions.append({
            'id': laptop.id,
            'name': laptop.display_name,
            'brand': laptop.brand.name if laptop.brand else '',
            'model': laptop.model.name if laptop.model else '',  # NUEVO: agregar modelo a sugerencias
            'price': float(laptop.discount_price or laptop.sale_price),
            'image': image_url,
            'url': f'/product/{laptop.id}',
            'sku': laptop.sku
        })

    return jsonify(suggestions)


# ============================================
# API: PRICE RANGE
# ============================================

@public_bp.route('/api/price-range')
def api_price_range():
    """API para obtener el rango de precios de productos"""
    price_range = db.session.query(
        db.func.min(
            case(
                (Laptop.discount_price != None, Laptop.discount_price),
                else_=Laptop.sale_price
            )
        ),
        db.func.max(
            case(
                (Laptop.discount_price != None, Laptop.discount_price),
                else_=Laptop.sale_price
            )
        )
    ).filter(
        Laptop.is_published == True,
        Laptop.quantity > 0
    ).first()

    min_price = float(price_range[0]) if price_range[0] else 500
    max_price = float(price_range[1]) if price_range[1] else 8000

    return jsonify({
        'min': min_price,
        'max': max_price
    })


# ============================================
# RUTA COMPATIBILIDAD: CATÁLOGO VIEJO (mantener por compatibilidad)
# ============================================

@public_bp.route('/catalog-old')
def catalog_old():
    """
    Catálogo público de productos - Versión vieja con paginación en servidor
    Mantener por compatibilidad con enlaces existentes
    """
    # Obtener parámetros de búsqueda y filtros
    search_query = request.args.get('q', '').strip()
    brand_id = request.args.get('brand', type=int)
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    category = request.args.get('category', '').strip()
    sort_by = request.args.get('sort', 'newest')

    # Paginación
    page = request.args.get('page', 1, type=int)
    per_page = 12

    # Query base: solo productos activos con stock
    query = Laptop.query.options(
        joinedload(Laptop.images)
    ).filter(
        Laptop.is_published == True,
        Laptop.quantity > 0
    )

    # Aplicar filtros
    if search_query:
        search_pattern = f'%{search_query}%'
        query = query.join(Brand).filter(
            or_(
                Laptop.display_name.ilike(search_pattern),
                Laptop.short_description.ilike(search_pattern),
                Brand.name.ilike(search_pattern)
            )
        )
    if brand_id:
        query = query.filter(Laptop.brand_id == brand_id)

    # Filtro por precio
    if min_price:
        query = query.filter(
            or_(
                and_(Laptop.discount_price != None, Laptop.discount_price >= min_price),
                and_(Laptop.discount_price == None, Laptop.sale_price >= min_price)
            )
        )

    if max_price:
        query = query.filter(
            or_(
                and_(Laptop.discount_price != None, Laptop.discount_price <= max_price),
                and_(Laptop.discount_price == None, Laptop.sale_price <= max_price)
            )
        )

    # Filtro por categoría
    if category and category in ['laptop', 'gaming', 'workstation']:
        query = query.filter(Laptop.category == category)

    # Ordenamiento
    if sort_by == 'price_asc':
        query = query.order_by(
            case(
                (Laptop.discount_price != None, Laptop.discount_price),
                else_=Laptop.sale_price
            ).asc()
        )
    elif sort_by == 'price_desc':
        query = query.order_by(
            case(
                (Laptop.discount_price != None, Laptop.discount_price),
                else_=Laptop.sale_price
            ).desc()
        )
    elif sort_by == 'popular':
        query = query.order_by(Laptop.is_featured.desc(), Laptop.created_at.desc())
    else:  # newest (default)
        query = query.order_by(Laptop.created_at.desc())

    # Paginación
    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    laptops = pagination.items

    # Datos para filtros
    brands = Brand.query.filter_by(is_active=True).order_by(Brand.name).all()

    # Rango de precios
    price_range = db.session.query(
        db.func.min(
            case(
                (Laptop.discount_price != None, Laptop.discount_price),
                else_=Laptop.sale_price
            )
        ),
        db.func.max(
            case(
                (Laptop.discount_price != None, Laptop.discount_price),
                else_=Laptop.sale_price
            )
        )
    ).filter(
        Laptop.is_published == True,
        Laptop.quantity > 0
    ).first()

    min_price_available = float(price_range[0]) if price_range[0] else 0
    max_price_available = float(price_range[1]) if price_range[1] else 10000

    return render_template(
        'landing/catalog_old.html',  # Mantener template viejo separado
        laptops=laptops,
        pagination=pagination,
        brands=brands,
        search_query=search_query,
        selected_brand=brand_id,
        min_price=min_price or min_price_available,
        max_price=max_price or max_price_available,
        min_price_available=min_price_available,
        max_price_available=max_price_available,
        category=category,
        sort_by=sort_by,
        total_products=pagination.total
    )


# ============================================
# ERROR HANDLERS PARA RUTAS PÚBLICAS
# ============================================

@public_bp.errorhandler(404)
def not_found_error(error):
    """Página 404 personalizada para rutas públicas"""
    try:
        return render_template('errors/404_public.html'), 404
    except:
        return render_template('errors/404.html'), 404


@public_bp.errorhandler(500)
def internal_error(error):
    """Página 500 personalizada para rutas públicas"""
    db.session.rollback()
    try:
        return render_template('errors/500_public.html'), 500
    except:
        return render_template('errors/500.html'), 500