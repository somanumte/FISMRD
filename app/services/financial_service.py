# -*- coding: utf-8 -*-
# ============================================
# FINANCIAL SERVICE - Cálculos Financieros Avanzados
# ============================================

from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional


class FinancialService:
    """Servicio avanzado para cálculos financieros y métricas"""

    @staticmethod
    def calculate_margin(purchase_cost, sale_price, additional_costs=0):
        """
        Calcula el margen de ganancia con costos adicionales

        Args:
            purchase_cost: Costo de compra
            sale_price: Precio de venta
            additional_costs: Costos adicionales (envío, impuestos, etc.)

        Returns:
            dict con métricas completas
        """
        try:
            purchase_cost = Decimal(str(purchase_cost)) if purchase_cost else Decimal('0')
            sale_price = Decimal(str(sale_price)) if sale_price else Decimal('0')
            additional_costs = Decimal(str(additional_costs)) if additional_costs else Decimal('0')

            # Costo total
            total_cost = purchase_cost + additional_costs

            # Ganancia bruta
            gross_profit = sale_price - total_cost

            # Margen porcentual
            if sale_price > 0:
                margin_percentage = (gross_profit / sale_price) * 100
            else:
                margin_percentage = Decimal('0')

            # ROI (Return on Investment)
            if total_cost > 0:
                roi_percentage = (gross_profit / total_cost) * 100
            else:
                roi_percentage = Decimal('0')

            # Punto de equilibrio
            break_even_point = total_cost / (1 - (margin_percentage / 100)) if margin_percentage < 100 else Decimal('0')

            return {
                'total_cost': round(total_cost, 2),
                'gross_profit': round(gross_profit, 2),
                'margin_percentage': round(margin_percentage, 2),
                'roi_percentage': round(roi_percentage, 2),
                'break_even_point': round(break_even_point, 2),
                'is_profitable': gross_profit > 0
            }
        except Exception as e:
            print(f"Error en calculate_margin: {e}")
            return {
                'total_cost': Decimal('0'),
                'gross_profit': Decimal('0'),
                'margin_percentage': Decimal('0'),
                'roi_percentage': Decimal('0'),
                'break_even_point': Decimal('0'),
                'is_profitable': False
            }

    @staticmethod
    def calculate_financial_metrics(period_data: List[Dict]) -> Dict:
        """
        Calcula métricas financieras complejas para un período

        Args:
            period_data: Lista de diccionarios con ventas, costos, gastos

        Returns:
            dict con todas las métricas financieras
        """
        try:
            if not period_data:
                return {
                    'total_sales': 0,
                    'total_cogs': 0,
                    'total_expenses': 0,
                    'gross_profit': 0,
                    'net_profit': 0,
                    'gross_margin': 0,
                    'net_margin': 0,
                    'break_even_point': 0,
                    'inventory_turnover': 0,
                    'avg_inventory_days': 0,
                    'contribution_margin_ratio': 0
                }

            total_sales = sum(item.get('sales', 0) for item in period_data)
            total_cogs = sum(item.get('cogs', 0) for item in period_data)
            total_expenses = sum(item.get('expenses', 0) for item in period_data)

            gross_profit = total_sales - total_cogs
            net_profit = gross_profit - total_expenses

            gross_margin = (gross_profit / total_sales * 100) if total_sales > 0 else 0
            net_margin = (net_profit / total_sales * 100) if total_sales > 0 else 0

            # Punto de equilibrio
            contribution_margin_ratio = gross_margin / 100 if gross_margin > 0 else 0
            break_even_point = total_expenses / contribution_margin_ratio if contribution_margin_ratio > 0 else 0

            # Rotación de inventario (simplificado)
            avg_inventory_value = total_cogs * 0.3  # Suposición: inventario = 30% COGS
            inventory_turnover = total_sales / avg_inventory_value if avg_inventory_value > 0 else 0
            avg_inventory_days = 365 / inventory_turnover if inventory_turnover > 0 else 0

            return {
                'total_sales': round(total_sales, 2),
                'total_cogs': round(total_cogs, 2),
                'total_expenses': round(total_expenses, 2),
                'gross_profit': round(gross_profit, 2),
                'net_profit': round(net_profit, 2),
                'gross_margin': round(gross_margin, 2),
                'net_margin': round(net_margin, 2),
                'break_even_point': round(break_even_point, 2),
                'inventory_turnover': round(inventory_turnover, 2),
                'avg_inventory_days': round(avg_inventory_days, 2),
                'contribution_margin_ratio': round(contribution_margin_ratio, 4)
            }
        except Exception as e:
            print(f"Error en calculate_financial_metrics: {e}")
            return {}

    @staticmethod
    def calculate_breakdown_analysis(laptops_data: List[Dict]) -> Dict:
        """
        Análisis de desglose por categoría/marca

        Args:
            laptops_data: Lista de laptops con ventas y márgenes

        Returns:
            dict con análisis de contribución
        """
        try:
            if not laptops_data:
                return {}

            total_sales = sum(item.get('sales', 0) for item in laptops_data)
            total_profit = sum(item.get('profit', 0) for item in laptops_data)

            # Por categoría
            category_analysis = {}
            for item in laptops_data:
                category = item.get('category', 'Sin categoría')
                if category not in category_analysis:
                    category_analysis[category] = {
                        'sales': 0,
                        'profit': 0,
                        'units': 0,
                        'margin': 0
                    }

                category_analysis[category]['sales'] += item.get('sales', 0)
                category_analysis[category]['profit'] += item.get('profit', 0)
                category_analysis[category]['units'] += item.get('units_sold', 0)

            # Calcular márgenes por categoría
            for category in category_analysis:
                sales = category_analysis[category]['sales']
                profit = category_analysis[category]['profit']
                category_analysis[category]['margin'] = (profit / sales * 100) if sales > 0 else 0

            # Por marca
            brand_analysis = {}
            for item in laptops_data:
                brand = item.get('brand', 'Sin marca')
                if brand not in brand_analysis:
                    brand_analysis[brand] = {
                        'sales': 0,
                        'profit': 0,
                        'units': 0,
                        'margin': 0
                    }

                brand_analysis[brand]['sales'] += item.get('sales', 0)
                brand_analysis[brand]['profit'] += item.get('profit', 0)
                brand_analysis[brand]['units'] += item.get('units_sold', 0)

            # Calcular márgenes por marca
            for brand in brand_analysis:
                sales = brand_analysis[brand]['sales']
                profit = brand_analysis[brand]['profit']
                brand_analysis[brand]['margin'] = (profit / sales * 100) if sales > 0 else 0

            return {
                'total_sales': total_sales,
                'total_profit': total_profit,
                'category_analysis': category_analysis,
                'brand_analysis': brand_analysis,
                'avg_margin': (total_profit / total_sales * 100) if total_sales > 0 else 0
            }
        except Exception as e:
            print(f"Error en calculate_breakdown_analysis: {e}")
            return {}

    @staticmethod
    def calculate_trend_analysis(current_data: List[Dict], previous_data: List[Dict]) -> Dict:
        """
        Análisis de tendencias vs período anterior

        Args:
            current_data: Datos del período actual
            previous_data: Datos del período anterior

        Returns:
            dict con análisis de tendencias
        """
        try:
            # Calcular totales actuales
            current_totals = FinancialService.calculate_financial_metrics(current_data)

            # Calcular totales anteriores
            previous_totals = FinancialService.calculate_financial_metrics(previous_data)

            trends = {}
            for key in current_totals:
                if key in previous_totals:
                    current_val = current_totals[key]
                    previous_val = previous_totals[key]

                    if previous_val != 0:
                        change_percent = ((current_val - previous_val) / abs(previous_val)) * 100
                    else:
                        change_percent = 100 if current_val > 0 else 0

                    trends[key] = {
                        'current': current_val,
                        'previous': previous_val,
                        'change': round(current_val - previous_val, 2),
                        'change_percent': round(change_percent, 2),
                        'direction': 'up' if current_val > previous_val else 'down' if current_val < previous_val else 'stable'
                    }

            return trends
        except Exception as e:
            print(f"Error en calculate_trend_analysis: {e}")
            return {}

    @staticmethod
    def generate_bcg_matrix(laptops_data: List[Dict]) -> List[Dict]:
        """
        Genera matriz BCG (Boston Consulting Group)

        Args:
            laptops_data: Datos de laptops con ventas y crecimiento

        Returns:
            Lista de items clasificados en la matriz
        """
        try:
            if not laptops_data:
                return []

            # Calcular métricas necesarias
            total_market_growth = 10  # Suposición: 10% crecimiento de mercado
            avg_market_share = sum(item.get('market_share', 5) for item in laptops_data) / len(laptops_data)

            matrix_items = []
            for item in laptops_data:
                market_growth = item.get('growth_rate', total_market_growth)
                relative_market_share = item.get('market_share', 5) / avg_market_share if avg_market_share > 0 else 1

                # Determinar cuadrante BCG
                if market_growth > total_market_growth and relative_market_share > 1:
                    quadrant = 'star'  # Estrella
                elif market_growth <= total_market_growth and relative_market_share > 1:
                    quadrant = 'cash_cow'  # Vaca lechera
                elif market_growth > total_market_growth and relative_market_share <= 1:
                    quadrant = 'question_mark'  # Signo de interrogación
                else:
                    quadrant = 'dog'  # Perro

                matrix_items.append({
                    'name': item.get('name', ''),
                    'category': item.get('category', ''),
                    'market_growth': market_growth,
                    'relative_market_share': relative_market_share,
                    'sales': item.get('sales', 0),
                    'profit': item.get('profit', 0),
                    'quadrant': quadrant,
                    'recommendation': FinancialService.get_bcg_recommendation(quadrant)
                })

            return matrix_items
        except Exception as e:
            print(f"Error en generate_bcg_matrix: {e}")
            return []

    @staticmethod
    def get_bcg_recommendation(quadrant: str) -> str:
        """Retorna recomendación basada en cuadrante BCG"""
        recommendations = {
            'star': 'Invertir y mantener - Alto crecimiento y alta participación',
            'cash_cow': 'Ordeñar ganancia - Bajo crecimiento pero alta participación',
            'question_mark': 'Evaluar - Alto crecimiento pero baja participación',
            'dog': 'Liquidar/eliminar - Bajo crecimiento y baja participación'
        }
        return recommendations.get(quadrant, 'Evaluar')

    @staticmethod
    def validate_prices(purchase_cost, sale_price, market_price=None):
        """
        Validación avanzada de precios

        Args:
            purchase_cost: Costo de compra
            sale_price: Precio de venta
            market_price: Precio de mercado (opcional)

        Returns:
            tuple (is_valid, messages, warnings)
        """
        messages = []
        warnings = []

        if not purchase_cost or not sale_price:
            return False, ["Costos y precios son requeridos"], []

        # Validación básica
        if sale_price < purchase_cost:
            messages.append("El precio de venta no puede ser menor al costo de compra")

        # Validación de márgenes
        margin_info = FinancialService.calculate_margin(purchase_cost, sale_price)

        if margin_info['margin_percentage'] < 10:
            warnings.append(f"Margen bajo ({margin_info['margin_percentage']:.1f}%). Considera aumentar precio.")
        elif margin_info['margin_percentage'] > 50:
            warnings.append(f"Margen muy alto ({margin_info['margin_percentage']:.1f}%). Verifica competitividad.")

        # Comparación con precio de mercado si está disponible
        if market_price:
            price_diff_percent = ((sale_price - market_price) / market_price) * 100

            if price_diff_percent > 20:
                warnings.append(f"Precio {price_diff_percent:.1f}% arriba del mercado. Riesgo de no vender.")
            elif price_diff_percent < -10:
                warnings.append(f"Precio {abs(price_diff_percent):.1f}% abajo del mercado. Oportunidad para aumentar.")

        is_valid = len(messages) == 0

        return is_valid, messages, warnings

    @staticmethod
    def suggest_sale_price(purchase_cost, target_margin=25, market_price=None):
        """
        Sugiere precio de venta óptimo

        Args:
            purchase_cost: Costo de compra
            target_margin: Margen objetivo (%)
            market_price: Precio de mercado referencial

        Returns:
            dict con múltiples opciones de precio
        """
        purchase_cost = Decimal(str(purchase_cost))
        target_margin = Decimal(str(target_margin)) / 100

        # Precio basado en margen objetivo
        suggested_price = purchase_cost / (1 - target_margin)

        # Precio basado en mercado si está disponible
        market_based_price = None
        if market_price:
            market_price_dec = Decimal(str(market_price))
            # Sugerencia: 10% abajo del mercado para ser competitivo
            market_based_price = market_price_dec * Decimal('0.9')

        # Precio premium (margen alto)
        premium_price = purchase_cost / (1 - Decimal('0.35'))  # 35% margen

        # Precio de liquidación (margen bajo)
        clearance_price = purchase_cost / (1 - Decimal('0.15'))  # 15% margen

        return {
            'target_margin_price': round(suggested_price, 2),
            'market_based_price': round(market_based_price, 2) if market_based_price else None,
            'premium_price': round(premium_price, 2),
            'clearance_price': round(clearance_price, 2),
            'recommendation': FinancialService.get_price_recommendation(
                suggested_price,
                market_based_price
            )
        }

    @staticmethod
    def get_price_recommendation(suggested_price, market_price):
        """Genera recomendación de precio"""
        if not market_price:
            return f"Precio sugerido: ${suggested_price:.2f} basado en margen objetivo"

        if suggested_price < market_price:
            return f"Precio competitivo. Puedes vender a ${suggested_price:.2f} (${market_price - suggested_price:.2f} menos que el mercado)"
        else:
            return f"Precio arriba del mercado. Considera bajar a ${market_price:.2f} para ser competitivo"