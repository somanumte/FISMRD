import logging
logging.basicConfig(level=logging.ERROR)
logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)

from flask import Blueprint, render_template, jsonify, request
# Suppress other loggers if necessary
import sys
import os

# Redirect stdout/stderr to capture clean output if needed, but logging level should suffice for now.

from app import create_app, db
from app.models.laptop import Laptop, Brand
from app.models.invoice import Invoice, InvoiceItem
from sqlalchemy import func

app = create_app()

with app.app_context():
    # Find Dell Brand
    dell = Brand.query.filter(Brand.name.ilike('Dell%')).first()
    if not dell:
        print("Brand 'Dell' not found.")
        exit()
    
    with open('dell_margin_report.txt', 'w', encoding='utf-8') as f:
        f.write(f"Analyzing Brand: {dell.name}\n")
        
        # Get all sold items for this brand
        sales = db.session.query(
            Laptop.display_name,
            InvoiceItem.quantity,
            InvoiceItem.unit_price,
            Laptop.purchase_cost
        ).join(
            Laptop, InvoiceItem.laptop_id == Laptop.id
        ).join(
            Invoice, InvoiceItem.invoice_id == Invoice.id
        ).filter(
            Laptop.brand_id == dell.id,
            Invoice.status.in_(['issued', 'paid', 'completed'])
        ).all()
        
        total_revenue = 0
        total_cost = 0
        total_items = 0
        
        f.write("\n--- Individual Sales ---\n")
        f.write(f"{'Product':<40} | {'Qty':<5} | {'Price':<10} | {'Cost':<10} | {'Revenue':<10} | {'Total Cost':<10} | {'Margin %':<10}\n")
        f.write("-" * 110 + "\n")
        
        for item in sales:
            qty = item.quantity
            price = float(item.unit_price)
            cost = float(item.purchase_cost)
            
            revenue = qty * price
            item_cost = qty * cost
            # Prevent division by zero
            margin_percent = ((price - cost) / price * 100) if price > 0 else 0
            
            total_revenue += revenue
            total_cost += item_cost
            total_items += qty
            
            f.write(f"{item.display_name[:37]:<40} | {qty:<5} | ${price:<9.2f} | ${cost:<9.2f} | ${revenue:<9.2f} | ${item_cost:<9.2f} | {margin_percent:.2f}%\n")
            
        f.write("-" * 110 + "\n")
        f.write("\n--- Summary ---\n")
        f.write(f"Total Items Sold: {total_items}\n")
        f.write(f"Total Revenue:    ${total_revenue:,.2f}\n")
        f.write(f"Total Cost:       ${total_cost:,.2f}\n")
        
        if total_revenue > 0:
            weighted_margin = ((total_revenue - total_cost) / total_revenue) * 100
            f.write(f"Avg Margin (Weighted): {weighted_margin:.2f}%\n")
            
            # Simple Average Calc for comparison
            simple_margins = [((float(i.unit_price) - float(i.purchase_cost)) / float(i.unit_price) * 100) for i in sales if float(i.unit_price) > 0]
            if simple_margins:
                simple_avg = sum(simple_margins) / len(simple_margins)
                f.write(f"Avg Margin (Simple):   {simple_avg:.2f}% (OLD METRIC)\n")
        else:
            f.write("No sales found.\n")
