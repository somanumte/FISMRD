# ============================================
# COMANDOS CLI PERSONALIZADOS
# ============================================

import click
import random
import re
from datetime import date, timedelta

from app.extensions import db
from app.utils.seeds import create_catalogs, create_sample_laptops


def register_cli_commands(app):
    """
    Registra todos los comandos CLI personalizados
    """
    from app.models.invoice import Invoice, InvoiceItem, InvoiceSettings
    from app.models.user import User
    from app.models.laptop import (
        Laptop, LaptopImage, Brand, LaptopModel, Processor,
        OperatingSystem, Screen, GraphicsCard, Storage, Ram,
        Store, Location, Supplier
    )
    from app.services.sku_service import SKUService
    from app.models.expense import ExpenseCategory

    # ===== COMANDO: reset-db =====
    @app.cli.command('reset-db')
    def reset_db():
        """⚠️ PELIGRO: Borra TODA la base de datos y la recrea vacía"""
        confirm = input("⚠️  ¿Estás seguro? Esto BORRARÁ TODOS los datos (yes/no): ").strip()

        if confirm.lower() != 'yes':
            click.echo("❌ Operación cancelada")
            return

        click.echo("🗑️  Eliminando todas las tablas...")
        db.drop_all()

        click.echo("🔨 Creando nuevas tablas...")
        db.create_all()

        click.echo("✅ Base de datos reiniciada correctamente")

    # ===== COMANDO: setup-fresh =====
    @app.cli.command('setup-fresh')
    def setup_fresh():
        """⚠️ Reinicia la BD y carga admin + catálogos + 50 laptops"""
        confirm = input("⚠️  Esto BORRARÁ TODO y creará datos nuevos. ¿Continuar? (yes/no): ").strip()

        if confirm.lower() != 'yes':
            click.echo("❌ Operación cancelada")
            return

        click.echo("\n" + "=" * 60)
        click.echo("🔄 CONFIGURACIÓN INICIAL DE LUXERA")
        click.echo("=" * 60)

        # 1. Reset DB
        click.echo("\n📦 Paso 1/5: Reiniciando base de datos...")
        db.drop_all()
        db.create_all()
        click.echo("   ✅ Base de datos creada")

        # 2. Crear Admin
        click.echo("\n👤 Paso 2/5: Creando usuario administrador...")
        admin = User(
            username='admin',
            email='felixjosemartinezbrito@gmail.com',
            full_name='Felix Jose Martinez Brito',
            is_admin=True,
            is_active=True
        )
        admin.set_password('1234')
        db.session.add(admin)
        db.session.commit()
        click.echo("   ✅ Admin creado: felixjosemartinezbrito@gmail.com")

        # 3. Crear Catálogos
        click.echo("\n📚 Paso 3/5: Creando catálogos...")
        create_catalogs()
        db.session.commit()
        click.echo("   ✅ Catálogos creados")

        # 4. Crear Laptops
        click.echo("\n💻 Paso 4/5: Creando 50 laptops de prueba...")
        create_sample_laptops(admin.id)
        db.session.commit()
        click.echo("   ✅ 50 laptops creadas")

        # 5. Resumen
        click.echo("\n📊 Paso 5/5: Verificando datos...")
        laptops_count = Laptop.query.count()
        brands_count = Brand.query.count()
        expense_categories_count = ExpenseCategory.query.count()

        click.echo("\n" + "=" * 60)
        click.echo("✅ CONFIGURACIÓN COMPLETADA")
        click.echo("=" * 60)
        click.echo(f"   👤 Admin: felixjosemartinezbrito@gmail.com")
        click.echo(f"   🔑 Password: 1234")
        click.echo(f"   💻 Laptops: {laptops_count}")
        click.echo(f"   🏭 Marcas: {brands_count}")
        click.echo(f"   📁 Categorías de gastos: {expense_categories_count}")
        click.echo("=" * 60 + "\n")

    # ===== COMANDO: init-db =====
    @app.cli.command('init-db')
    def init_db():
        """Inicializa la base de datos (crea tablas sin borrar)"""
        db.create_all()
        click.echo("✅ Base de datos inicializada")

    # ===== COMANDO: create-admin =====
    @app.cli.command('create-admin')
    def create_admin():
        """Crea el usuario administrador"""
        existing = User.query.filter_by(email='felixjosemartinezbrito@gmail.com').first()

        if existing:
            click.echo("⚠️  El admin ya existe")
            return

        admin = User(
            username='admin',
            email='felixjosemartinezbrito@gmail.com',
            full_name='Felix Jose Martinez Brito',
            is_admin=True,
            is_active=True
        )
        admin.set_password('1234')
        db.session.add(admin)
        db.session.commit()

        click.echo("✅ Admin creado: felixjosemartinezbrito@gmail.com / 1234")

    # ===== COMANDO: seed-catalog =====
    @app.cli.command('seed-catalog')
    def seed_catalog():
        """Pobla los catálogos con datos"""
        create_catalogs()
        db.session.commit()
        click.echo("✅ Catálogos poblados exitosamente")

    # ===== COMANDO: seed-laptops =====
    @app.cli.command('seed-laptops')
    def seed_laptops():
        """Crea 50 laptops de prueba"""
        admin = User.query.filter_by(is_admin=True).first()
        if not admin:
            click.echo("❌ Primero crea un admin con: flask create-admin")
            return

        create_sample_laptops(admin.id)
        db.session.commit()
        click.echo("✅ 50 laptops creadas")

    # ===== COMANDO: list-users =====
    @app.cli.command('list-users')
    def list_users():
        """Lista todos los usuarios"""
        users = User.query.order_by(User.created_at.desc()).all()

        if not users:
            click.echo("🔭 No hay usuarios registrados")
            return

        click.echo(f"\n📋 Total de usuarios: {len(users)}")
        click.echo("\n" + "=" * 80)
        click.echo(f"{'ID':<5} {'Username':<15} {'Email':<35} {'Admin':<8}")
        click.echo("=" * 80)

        for user in users:
            click.echo(f"{user.id:<5} {user.username:<15} {user.email:<35} {'Sí' if user.is_admin else 'No':<8}")

        click.echo("=" * 80 + "\n")

    # ===== COMANDO: list-laptops =====
    @app.cli.command('list-laptops')
    def list_laptops():
        """Lista las laptops del inventario"""
        laptops = Laptop.query.order_by(Laptop.entry_date.desc()).all()

        if not laptops:
            click.echo("🔭 No hay laptops en el inventario")
            return

        total_value = sum(float(l.sale_price * l.quantity) for l in laptops)

        click.echo(f"\n💻 Total: {len(laptops)} laptops | Valor: ${total_value:,.2f}")
        click.echo("\n" + "=" * 100)
        click.echo(f"{'SKU':<18} {'Marca':<8} {'Modelo':<30} {'Precio':<10} {'Cant.':<6}")
        click.echo("=" * 100)

        for laptop in laptops[:25]:
            model_name = laptop.model.name[:28] if laptop.model else 'N/A'
            brand_name = laptop.brand.name[:6] if laptop.brand else 'N/A'
            click.echo(
                f"{laptop.sku:<18} {brand_name:<8} {model_name:<30} ${float(laptop.sale_price):>7,.0f} {laptop.quantity:>4}")

        if len(laptops) > 25:
            click.echo(f"\n... y {len(laptops) - 25} más")

        click.echo("=" * 100 + "\n")

    # ===== COMANDO: inventory-stats =====
    @app.cli.command('inventory-stats')
    def inventory_stats():
        """Muestra estadísticas del inventario"""
        laptops = Laptop.query.all()

        if not laptops:
            click.echo("🔭 No hay laptops")
            return

        click.echo("\n" + "=" * 50)
        click.echo("📊 ESTADÍSTICAS DEL INVENTARIO")
        click.echo("=" * 50)

        total_units = sum(l.quantity for l in laptops)
        total_value = sum(float(l.sale_price * l.quantity) for l in laptops)
        total_cost = sum(float(l.purchase_cost * l.quantity) for l in laptops)

        click.echo(f"\n💰 FINANCIERO")
        click.echo(f"   Valor de venta: ${total_value:,.2f}")
        click.echo(f"   Costo total: ${total_cost:,.2f}")
        click.echo(f"   Ganancia potencial: ${total_value - total_cost:,.2f}")

        click.echo(f"\n📦 INVENTARIO")
        click.echo(f"   SKUs: {len(laptops)}")
        click.echo(f"   Unidades: {total_units}")
        click.echo(f"   Publicadas: {len([l for l in laptops if l.is_published])}")
        click.echo(f"   Destacadas: {len([l for l in laptops if l.is_featured])}")

        click.echo(f"\n🏷️ POR CATEGORÍA")
        for cat in ['laptop', 'workstation', 'gaming']:
            count = len([l for l in laptops if l.category == cat])
            click.echo(f"   {cat.capitalize()}: {count}")

        click.echo(f"\n🏭 POR MARCA")
        brands_stats = {}
        for l in laptops:
            name = l.brand.name if l.brand else 'N/A'
            brands_stats[name] = brands_stats.get(name, 0) + l.quantity
        for name, qty in sorted(brands_stats.items(), key=lambda x: -x[1]):
            click.echo(f"   {name}: {qty} unidades")

        click.echo("\n" + "=" * 50 + "\n")