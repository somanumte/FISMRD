# ============================================
# COMANDOS CLI PERSONALIZADOS
# ============================================

import click
import random
import re
from datetime import date, timedelta
from sqlalchemy import text  # Añadido para usar text() en SQL

from app.extensions import db
from app.utils.seeds import create_catalogs, create_sample_laptops, create_extensive_laptops, generate_financial_history


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

    def drop_all_tables_safe():
        """
        Elimina todas las tablas de forma segura manejando dependencias
        """
        click.echo("🗑️  Eliminando todas las tablas...")

        try:
            # Método 1: Usar metadata.drop_all con cascade=True
            db.metadata.drop_all(bind=db.engine, checkfirst=True, cascade=True)
            click.echo("✅ Base de datos eliminada correctamente")
            return True
        except Exception as e:
            click.echo(f"⚠️  Método 1 falló: {str(e)[:100]}...")
            click.echo("🔄 Intentando método alternativo...")

            # Método 2: SQL directo para PostgreSQL
            try:
                with db.engine.begin() as conn:
                    # Desactivar triggers temporalmente
                    conn.execute(text('SET session_replication_role = replica'))

                    # Eliminar todas las tablas del esquema público
                    conn.execute(text("""
                        DO $$ DECLARE
                            r RECORD;
                        BEGIN
                            -- Eliminar tablas normales
                            FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                                EXECUTE 'DROP TABLE IF EXISTS "' || r.tablename || '" CASCADE';
                            END LOOP;
                            -- Eliminar vistas
                            FOR r IN (SELECT viewname FROM pg_views WHERE schemaname = 'public') LOOP
                                EXECUTE 'DROP VIEW IF EXISTS "' || r.viewname || '" CASCADE';
                            END LOOP;
                        END $$;
                    """))

                    # Reactivar triggers
                    conn.execute(text('SET session_replication_role = DEFAULT'))

                click.echo("✅ Base de datos eliminada correctamente (método alternativo)")
                return True
            except Exception as e2:
                click.echo(f"❌ Método 2 falló: {str(e2)[:100]}...")
                click.echo("🤔 Intentando método de emergencia...")

                # Método 3: Eliminar esquema completo
                try:
                    with db.engine.begin() as conn:
                        # Eliminar el esquema público y recrearlo
                        conn.execute(text('DROP SCHEMA IF EXISTS public CASCADE'))
                        conn.execute(text('CREATE SCHEMA public'))
                        conn.execute(text('GRANT ALL ON SCHEMA public TO postgres'))
                        conn.execute(text('GRANT ALL ON SCHEMA public TO public'))

                    click.echo("✅ Esquema público recreado correctamente")
                    return True
                except Exception as e3:
                    click.echo(f"❌ Error crítico: {str(e3)[:100]}...")
                    return False

    # ===== COMANDO: reset-db =====
    @app.cli.command('reset-db')
    def reset_db():
        """⚠️ PELIGRO: Borra TODA la base de datos y la recrea vacía"""
        confirm = input("⚠️  ¿Estás seguro? Esto BORRARÁ TODOS los datos (yes/no): ").strip()

        if confirm.lower() != 'yes':
            click.echo("❌ Operación cancelada")
            return

        # Eliminar tablas de forma segura
        if not drop_all_tables_safe():
            click.echo("❌ No se pudo eliminar la base de datos")
            return

        # Crear nuevas tablas
        click.echo("🔨 Creando nuevas tablas...")
        try:
            db.create_all()
            click.echo("✅ Base de datos recreada correctamente")
        except Exception as e:
            click.echo(f"❌ Error al crear tablas: {str(e)[:100]}...")
            click.echo("🤔 Intentando recrear esquema...")

            # Asegurar que el esquema público existe
            with db.engine.begin() as conn:
                conn.execute(text('CREATE SCHEMA IF NOT EXISTS public'))

            db.create_all()
            click.echo("✅ Base de datos recreada correctamente")

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
        if not drop_all_tables_safe():
            click.echo("❌ No se pudo reiniciar la base de datos")
            return

        try:
            db.create_all()
            click.echo("   ✅ Base de datos creada")
        except Exception as e:
            click.echo(f"   ❌ Error: {str(e)[:100]}...")
            return

        # 2. Crear Admin
        click.echo("\n👤 Paso 2/5: Creando usuario administrador...")
        try:
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
        except Exception as e:
            click.echo(f"   ❌ Error al crear admin: {str(e)[:100]}...")
            db.session.rollback()

        # 3. Crear Catálogos
        click.echo("\n📚 Paso 3/5: Creando catálogos...")
        try:
            create_catalogs()
            db.session.commit()
            click.echo("   ✅ Catálogos creados")
        except Exception as e:
            click.echo(f"   ❌ Error al crear catálogos: {str(e)[:100]}...")
            db.session.rollback()

        # 4. Crear Laptops
        click.echo("\n💻 Paso 4/5: Creando 50 laptops de prueba...")
        try:
            create_sample_laptops(admin.id if 'admin' in locals() else 1)
            db.session.commit()
            click.echo("   ✅ 50 laptops creadas")
        except Exception as e:
            click.echo(f"   ❌ Error al crear laptops: {str(e)[:100]}...")
            db.session.rollback()

        # 5. Resumen
        click.echo("\n📊 Paso 5/5: Verificando datos...")
        try:
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
        except Exception as e:
            click.echo(f"   ⚠️  No se pudo obtener el resumen: {str(e)[:100]}...")

    # ===== COMANDO: init-db =====
    @app.cli.command('init-db')
    def init_db():
        """Inicializa la base de datos (crea tablas sin borrar)"""
        try:
            db.create_all()
            click.echo("✅ Base de datos inicializada")
        except Exception as e:
            click.echo(f"❌ Error: {str(e)[:100]}...")

    # ===== COMANDO: create-admin =====
    @app.cli.command('create-admin')
    def create_admin():
        """Crea el usuario administrador"""
        try:
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
        except Exception as e:
            click.echo(f"❌ Error: {str(e)[:100]}...")
            db.session.rollback()

    # ===== COMANDO: seed-catalog =====
    @app.cli.command('seed-catalog')
    def seed_catalog():
        """Pobla los catálogos con datos"""
        try:
            create_catalogs()
            db.session.commit()
            click.echo("✅ Catálogos poblados exitosamente")
        except Exception as e:
            click.echo(f"❌ Error: {str(e)[:100]}...")
            db.session.rollback()

    # ===== COMANDO: seed-laptops =====
    @app.cli.command('seed-laptops')
    def seed_laptops():
        """Crea 50 laptops de prueba"""
        try:
            admin = User.query.filter_by(is_admin=True).first()
            if not admin:
                click.echo("❌ Primero crea un admin con: flask create-admin")
                return

            create_sample_laptops(admin.id)
            db.session.commit()
            click.echo("✅ 50 laptops creadas")
        except Exception as e:
            click.echo(f"❌ Error: {str(e)[:100]}...")
            db.session.rollback()

    # ===== COMANDO: list-users =====
    @app.cli.command('list-users')
    def list_users():
        """Lista todos los usuarios"""
        try:
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
        except Exception as e:
            click.echo(f"❌ Error: {str(e)[:100]}...")

    # ===== COMANDO: list-laptops =====
    @app.cli.command('list-laptops')
    def list_laptops():
        """Lista las laptops del inventario"""
        try:
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
        except Exception as e:
            click.echo(f"❌ Error: {str(e)[:100]}...")

    # ===== COMANDO: inventory-stats =====
    @app.cli.command('inventory-stats')
    def inventory_stats():
        """Muestra estadísticas del inventario"""
        try:
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
        except Exception as e:
            click.echo(f"❌ Error: {str(e)[:100]}...")

    # ===== COMANDO NUEVO: fix-db =====
    @app.cli.command('fix-db')
    def fix_db():
        """Repara problemas comunes en la base de datos"""
        click.echo("🔧 Reparando base de datos...")

        try:
            # Verificar si existe la tabla 'user'
            with db.engine.connect() as conn:
                result = conn.execute(text("""
                                           SELECT EXISTS (SELECT
                                                          FROM information_schema.tables
                                                          WHERE table_schema = 'public'
                                                            AND table_name = 'user');
                                           """))
                user_table_exists = result.scalar()

                if user_table_exists:
                    click.echo("✅ Tabla 'user' existe")

                    # Verificar si existe la tabla 'users_roles'
                    result = conn.execute(text("""
                                               SELECT EXISTS (SELECT
                                                              FROM information_schema.tables
                                                              WHERE table_schema = 'public'
                                                                AND table_name = 'users_roles');
                                               """))
                    users_roles_exists = result.scalar()

                    if users_roles_exists:
                        click.echo("⚠️  Tabla 'users_roles' encontrada")
                        click.echo("   Eliminando restricciones problemáticas...")

                        # Eliminar constraints problemáticos
                        conn.execute(text("""
                                          ALTER TABLE IF EXISTS users_roles
                                          DROP
                                          CONSTRAINT IF EXISTS users_roles_user_id_fkey;
                                          """))

                        click.echo("✅ Restricciones eliminadas")

                click.echo("\n✅ Base de datos reparada")
        except Exception as e:
            click.echo(f"❌ Error: {str(e)[:100]}...")

    # ===== COMANDO: seed-laptops-real =====
    @app.cli.command('seed-laptops-real')
    def seed_laptops_real():
        """Genera 100 modelos de laptops reales con UPC y DOP"""
        try:
            admin = User.query.filter_by(is_admin=True).first()
            if not admin:
                click.echo("❌ Primero crea un admin con: flask create-admin")
                return

            click.echo("🚀 Generando catálogo de 100 laptops reales...")
            create_extensive_laptops(admin.id)
            click.echo("✅ Catálogo de 100 laptops completado")
        except Exception as e:
            click.echo(f"❌ Error: {str(e)}")
            db.session.rollback()

    # ===== COMANDO: seed-financials =====
    @app.cli.command('seed-financials')
    @click.option('--months', default=24, help='Meses de historia a simular')
    def seed_financials(months):
        """Simula historial financiero (Ventas 3M/mes, Gastos 500k/mes)"""
        try:
            admin = User.query.filter_by(is_admin=True).first()
            if not admin:
                click.echo("❌ Primero crea un admin con: flask create-admin")
                return

            click.echo(f"📈 Simulando {months} meses de historia financiera...")
            result = generate_financial_history(admin.id, months=months)
            click.echo(f"✅ {result}")
        except Exception as e:
            click.echo(f"❌ Error: {str(e)}")
            db.session.rollback()