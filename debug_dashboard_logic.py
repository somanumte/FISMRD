from app import create_app
from app.routes.dashboard import get_brand_performance

app = create_app()

with app.app_context():
    with open('debug_output.txt', 'w', encoding='utf-8') as f:
        f.write("--- Running get_brand_performance ---\n")
        data = get_brand_performance()
        
        found_dell = False
        for i, brand in enumerate(data['brands']):
            if 'Dell' in brand:
                found_dell = True
                f.write(f"Brand: {brand}\n")
                f.write(f"Sales: ${data['sales'][i]:,.2f}\n")
                f.write(f"Margin: {data['margins'][i]}%\n")
                
        if not found_dell:
            f.write("Dell not found in top 10 brands of get_brand_performance\n")
        
        f.write("\nFull Data:\n")
        import json
        f.write(json.dumps(data, indent=2))
