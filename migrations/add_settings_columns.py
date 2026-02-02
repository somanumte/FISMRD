
import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from sqlalchemy import text

app = create_app()

def run_migration():
    with app.app_context():
        print("Iniciando migración de esquema para InvoiceSettings...")
        
        # Lista de columnas a agregar
        columns = [
            ("tax_rate", "NUMERIC(5, 2) NOT NULL DEFAULT 18.00"),
            ("tax_name", "VARCHAR(20) NOT NULL DEFAULT 'ITBIS'"),
            ("currency_symbol", "VARCHAR(5) NOT NULL DEFAULT 'RD$'"),
            ("bank_details", "TEXT"),
            ("invoice_footer", "TEXT"),
            ("brand_color", "VARCHAR(7) NOT NULL DEFAULT '#4f46e5'")
        ]
        
        with db.engine.connect() as conn:
            for col_name, col_def in columns:
                try:
                    # Intentar agregar la columna
                    print(f"Agregando columna {col_name}...")
                    conn.execute(text(f"ALTER TABLE invoice_settings ADD COLUMN {col_name} {col_def}"))
                    print(f"Columna {col_name} agregada exitosamente.")
                except Exception as e:
                    # Si falla (probablemente porque ya existe), lo ignoramos pero informamos
                    if "duplicate column name" in str(e).lower():
                        print(f"Columna {col_name} ya existe. Saltando.")
                    else:
                        print(f"Nota sobre {col_name}: {str(e)}")
            
            conn.commit()
            print("Migración completada.")

if __name__ == "__main__":
    run_migration()
