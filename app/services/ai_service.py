# -*- coding: utf-8 -*-
# ============================================
# AI SERVICE - Análisis Predictivo y Recomendaciones
# ============================================

from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import json


class AIService:
    """Servicio de Inteligencia Artificial Avanzado"""

    @staticmethod
    def generate_executive_report(financial_data: Dict, inventory_data: Dict,
                                  sales_data: Dict, period: str = 'month') -> str:
        """
        Genera reporte ejecutivo completo

        Args:
            financial_data: Datos financieros
            inventory_data: Datos de inventario
            sales_data: Datos de ventas
            period: Período analizado

        Returns:
            str: Reporte ejecutivo formateado
        """
        try:
            # Analizar salud financiera
            financial_health = AIService.analyze_financial_health(financial_data)

            # Analizar inventario
            inventory_analysis = AIService.analyze_inventory_health(inventory_data)

            # Analizar tendencias de ventas
            sales_trends = AIService.analyze_sales_trends(sales_data)

            # Generar recomendaciones estratégicas
            recommendations = AIService.generate_strategic_recommendations(
                financial_health,
                inventory_analysis,
                sales_trends
            )

            # Construir reporte
            report_parts = [
                "📊 **REPORTE EJECUTIVO LUXERA AI**",
                f"📅 Período: {period.upper()}",
                "",
                "🚀 **RESUMEN DE DESEMPEÑO**",
                f"• Salud Financiera: {financial_health['overall_score']}/10",
                f"• Estado de Inventario: {inventory_analysis['overall_score']}/10",
                f"• Tendencias de Ventas: {'📈 Positiva' if sales_trends['trend'] == 'up' else '📉 Negativa' if sales_trends['trend'] == 'down' else '➡️ Estable'}",
                "",
                "💰 **MÉTRICAS CLAVE**",
                f"• Ventas Totales: ${financial_data.get('total_sales', 0):,.2f}",
                f"• Margen Neto: {financial_data.get('net_margin', 0):.1f}%",
                f"• Utilidad Neta: ${financial_data.get('net_profit', 0):,.2f}",
                f"• Rotación de Inventario: {inventory_data.get('turnover', 0):.1f}x",
                "",
                "⚠️ **PUNTOS DE ATENCIÓN**",
            ]

            # Añadir alertas
            alerts = financial_health.get('alerts', []) + inventory_analysis.get('alerts', [])
            if alerts:
                for alert in alerts[:3]:  # Máximo 3 alertas
                    report_parts.append(f"• {alert}")
            else:
                report_parts.append("• ✅ Todo dentro de parámetros normales")

            report_parts.extend([
                "",
                "🎯 **RECOMENDACIONES ESTRATÉGICAS**",
            ])

            # Añadir recomendaciones
            for i, rec in enumerate(recommendations[:5], 1):  # Máximo 5 recomendaciones
                report_parts.append(f"{i}. {rec}")

            report_parts.extend([
                "",
                "📈 **PRONÓSTICO**",
                AIService.generate_forecast(financial_data, sales_trends),
                "",
                "💡 **CONSEJO DEL DÍA**",
                AIService.get_daily_tip(),
                "",
                f"🔄 Reporte generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            ])

            return "\n".join(report_parts)

        except Exception as e:
            print(f"Error en generate_executive_report: {e}")
            return "⚠️ No se pudo generar el reporte ejecutivo en este momento."

    @staticmethod
    def analyze_financial_health(financial_data: Dict) -> Dict:
        """
        Analiza la salud financiera del negocio

        Returns:
            Dict con puntuación y análisis
        """
        try:
            total_sales = financial_data.get('total_sales', 0)
            net_margin = financial_data.get('net_margin', 0)
            net_profit = financial_data.get('net_profit', 0)
            break_even = financial_data.get('break_even_point', 0)

            score = 0
            alerts = []
            strengths = []

            # Evaluar margen neto
            if net_margin > 20:
                score += 3
                strengths.append("Margen neto excelente (>20%)")
            elif net_margin > 10:
                score += 2
                strengths.append("Margen neto saludable (10-20%)")
            elif net_margin > 5:
                score += 1
                alerts.append("Margen neto bajo (5-10%)")
            else:
                score -= 2
                alerts.append("⚠️ Margen neto crítico (<5%)")

            # Evaluar utilidad
            if net_profit > total_sales * 0.15:
                score += 3
                strengths.append("Alta rentabilidad")
            elif net_profit > 0:
                score += 1
            else:
                score -= 3
                alerts.append("🚨 PÉRDIDAS DETECTADAS")

            # Evaluar punto de equilibrio
            if break_even < total_sales * 0.7:
                score += 2
                strengths.append("Bajo punto de equilibrio")
            elif break_even > total_sales:
                score -= 2
                alerts.append("Punto de equilibrio muy alto")

            # Evaluar crecimiento (si hay datos históricos)
            growth_rate = financial_data.get('growth_rate', 0)
            if growth_rate > 15:
                score += 2
                strengths.append("Crecimiento acelerado")
            elif growth_rate < 0:
                score -= 1
                alerts.append("Crecimiento negativo")

            # Normalizar score a 10
            overall_score = min(10, max(0, score + 5))

            return {
                'overall_score': overall_score,
                'grade': AIService.get_grade(overall_score),
                'alerts': alerts,
                'strengths': strengths,
                'financial_metrics': financial_data
            }

        except Exception as e:
            print(f"Error en analyze_financial_health: {e}")
            return {'overall_score': 0, 'grade': 'F', 'alerts': [], 'strengths': []}

    @staticmethod
    def analyze_inventory_health(inventory_data: Dict) -> Dict:
        """
        Analiza la salud del inventario

        Returns:
            Dict con puntuación y análisis
        """
        try:
            turnover = inventory_data.get('turnover', 0)
            dead_stock = inventory_data.get('dead_stock_count', 0)
            low_stock = inventory_data.get('low_stock_count', 0)
            out_of_stock = inventory_data.get('out_of_stock_count', 0)
            total_items = inventory_data.get('total_items', 0)

            score = 0
            alerts = []
            strengths = []

            # Evaluar rotación
            if turnover > 8:
                score += 3
                strengths.append("Alta rotación de inventario")
            elif turnover > 4:
                score += 2
                strengths.append("Rotación adecuada")
            elif turnover > 2:
                score += 1
            else:
                score -= 2
                alerts.append("⚠️ Rotación de inventario muy baja")

            # Evaluar stock muerto
            dead_stock_percent = (dead_stock / total_items * 100) if total_items > 0 else 0
            if dead_stock_percent > 20:
                score -= 3
                alerts.append("🚨 ALTO PORCENTAJE DE STOCK MUERTO")
            elif dead_stock_percent > 10:
                score -= 1
                alerts.append("Stock muerto por encima del óptimo")

            # Evaluar stock bajo
            if low_stock > total_items * 0.3:
                score -= 2
                alerts.append("Muchos productos con stock bajo")

            # Evaluar sin stock
            if out_of_stock > 0:
                score -= 1
                alerts.append(f"{out_of_stock} productos sin stock")

            # Normalizar score a 10
            overall_score = min(10, max(0, score + 5))

            return {
                'overall_score': overall_score,
                'grade': AIService.get_grade(overall_score),
                'alerts': alerts,
                'strengths': strengths,
                'inventory_metrics': inventory_data
            }

        except Exception as e:
            print(f"Error en analyze_inventory_health: {e}")
            return {'overall_score': 0, 'grade': 'F', 'alerts': [], 'strengths': []}

    @staticmethod
    def analyze_sales_trends(sales_data: Dict) -> Dict:
        """
        Analiza tendencias de ventas

        Returns:
            Dict con análisis de tendencias
        """
        try:
            # Obtener serie de tiempo de ventas
            if 'datasets' in sales_data and len(sales_data['datasets']) > 0:
                sales_values = sales_data['datasets'][0].get('data', [])
            else:
                daily_sales = sales_data.get('daily_sales', [])
                sales_values = [day.get('amount', 0) for day in daily_sales]

            if not sales_values or len(sales_values) < 2:
                return {'trend': 'stable', 'momentum': 'neutral', 'trend_percent': 0, 'volatility': 0}

            # Tomar últimos periodos (máximo 7)
            recent_sales = sales_values[-7:] if len(sales_values) >= 7 else sales_values
            
            # Tendencia simple
            split_idx = len(recent_sales) // 2
            first_half = sum(recent_sales[:split_idx]) / split_idx if split_idx > 0 else recent_sales[0]
            second_half = sum(recent_sales[split_idx:]) / (len(recent_sales) - split_idx)
            
            trend_percent = ((second_half - first_half) / first_half * 100) if first_half > 0 else 0

            if trend_percent > 10:
                trend = 'up'
                momentum = 'strong'
            elif trend_percent > 5:
                trend = 'up'
                momentum = 'moderate'
            elif trend_percent < -10:
                trend = 'down'
                momentum = 'strong'
            elif trend_percent < -5:
                trend = 'down'
                momentum = 'moderate'
            else:
                trend = 'stable'
                momentum = 'neutral'

            # Calcular volatilidad
            avg_sales = sum(recent_sales) / len(recent_sales)
            variance = sum((x - avg_sales) ** 2 for x in recent_sales) / len(recent_sales)
            volatility = (variance ** 0.5) / avg_sales if avg_sales > 0 else 0

            # Identificar mejores y peores días
            # Si tenemos daily_sales original (formato antiguo)
            daily_sales = sales_data.get('daily_sales', [])
            if daily_sales:
                best_day = max(daily_sales, key=lambda x: x.get('amount', 0))
                worst_day = min(daily_sales, key=lambda x: x.get('amount', 0))
            else:
                best_day = None
                worst_day = None

            return {
                'trend': trend,
                'momentum': momentum,
                'trend_percent': round(trend_percent, 2),
                'volatility': round(volatility, 3),
                'best_day': best_day,
                'worst_day': worst_day,
                'avg_daily_sales': round(avg_sales, 2)
            }

            return {'trend': 'stable', 'momentum': 'neutral', 'trend_percent': 0}

        except Exception as e:
            print(f"Error en analyze_sales_trends: {e}")
            return {'trend': 'stable', 'momentum': 'neutral', 'trend_percent': 0}

    @staticmethod
    def generate_strategic_recommendations(financial_health: Dict,
                                           inventory_analysis: Dict,
                                           sales_trends: Dict) -> List[str]:
        """
        Genera recomendaciones estratégicas basadas en análisis

        Returns:
            Lista de recomendaciones
        """
        recommendations = []

        # Recomendaciones basadas en salud financiera
        if financial_health['overall_score'] < 6:
            recommendations.append("Optimizar costos operativos para mejorar margen neto")

        if financial_health.get('financial_metrics', {}).get('net_margin', 0) < 10:
            recommendations.append("Revisar estrategia de precios para aumentar márgenes")

        # Recomendaciones basadas en inventario
        if inventory_analysis['overall_score'] < 6:
            recommendations.append("Implementar sistema de reorden automático para stock bajo")

        dead_stock_count = inventory_analysis.get('inventory_metrics', {}).get('dead_stock_count', 0)
        if dead_stock_count > 5:
            recommendations.append(f"Crear promoción para liquidar {dead_stock_count} items de stock muerto")

        # Recomendaciones basadas en ventas
        if sales_trends['trend'] == 'down' and sales_trends['momentum'] == 'strong':
            recommendations.append("Lanzar campaña promocional para reactivar ventas")

        if sales_trends['volatility'] > 0.3:
            recommendations.append("Diversificar canales de venta para estabilizar ingresos")

        # Recomendaciones generales
        recommendations.append("Implementar programa de fidelización para clientes recurrentes")
        recommendations.append("Analizar competencia para ajustar precios competitivamente")
        recommendations.append("Capacitar equipo de ventas en técnicas de upselling")

        return recommendations[:8]  # Máximo 8 recomendaciones

    @staticmethod
    def generate_forecast(financial_data: Dict, sales_trends: Dict) -> str:
        """
        Genera pronóstico basado en datos actuales

        Returns:
            str: Pronóstico formateado
        """
        try:
            current_sales = financial_data.get('total_sales', 0)
            trend_percent = sales_trends.get('trend_percent', 0)

            # Pronóstico simple
            if trend_percent > 0:
                forecast_sales = current_sales * (1 + trend_percent / 100)
                forecast_text = f"Pronóstico positivo: ${forecast_sales:,.0f} (+{trend_percent:.1f}%)"
            elif trend_percent < 0:
                forecast_sales = current_sales * (1 + trend_percent / 100)
                forecast_text = f"Pronóstico cauteloso: ${forecast_sales:,.0f} ({trend_percent:.1f}%)"
            else:
                forecast_sales = current_sales
                forecast_text = f"Pronóstico estable: ${forecast_sales:,.0f}"

            return forecast_text

        except Exception as e:
            print(f"Error en generate_forecast: {e}")
            return "Pronóstico no disponible"

    @staticmethod
    def get_grade(score: float) -> str:
        """Convierte puntuación a letra de calificación"""
        if score >= 9:
            return 'A+'
        elif score >= 8:
            return 'A'
        elif score >= 7:
            return 'B'
        elif score >= 6:
            return 'C'
        elif score >= 5:
            return 'D'
        else:
            return 'F'

    @staticmethod
    def get_daily_tip() -> str:
        """Retorna consejo del día"""
        tips = [
            "📱 Publica en redes sociales al menos 3 veces por semana",
            "💬 Pide reseñas a clientes satisfechos para aumentar credibilidad",
            "📊 Analiza tus productos más rentables cada semana",
            "🔄 Renueva tu inventario de productos destacados mensualmente",
            "🎯 Ofrece paquetes o combos para aumentar ticket promedio",
            "📧 Crea lista de correo para promociones exclusivas",
            "⭐ Premia a tus clientes más fieles con descuentos especiales",
            "🔍 Investiga a tu competencia regularmente para mantener precios competitivos"
        ]
        from datetime import datetime
        day_of_year = datetime.now().timetuple().tm_yday
        return tips[day_of_year % len(tips)]

    @staticmethod
    def generate_bcg_matrix_analysis(laptops_data: List[Dict]) -> Dict:
        """
        Genera análisis avanzado de matriz BCG

        Args:
            laptops_data: Datos de laptops con ventas y crecimiento

        Returns:
            Dict con análisis completo
        """
        try:
            if not laptops_data:
                return {}

            # Calcular métricas para matriz BCG
            total_sales = sum(item.get('z', item.get('sales', 0)) for item in laptops_data)
            total_market_growth = 10  # Umbral de mercado

            matrix_data = []
            for item in laptops_data:
                sales = item.get('z', item.get('sales', 0))
                market_share = item.get('x', (sales / total_sales * 100) if total_sales > 0 else 0)
                growth_rate = item.get('y', item.get('growth_rate', 0))

                # Clasificar en cuadrantes BCG
                # Usar el cuadrante ya definido si existe, o recalcular
                if item.get('quadrant'):
                    quadrant = item['quadrant']
                    label = item.get('label', 'Análisis')
                    color = item.get('color', '#6366f1')
                else:
                    if market_share > 5 and growth_rate > total_market_growth:
                        quadrant = 'star'
                        color = '#6366f1'  # Indigo
                        label = 'Estrella'
                    elif market_share > 5 and growth_rate <= total_market_growth:
                        quadrant = 'cash_cow'
                        color = '#10b981'  # Emerald
                        label = 'Vaca Lechera'
                    elif market_share <= 5 and growth_rate > total_market_growth:
                        quadrant = 'question_mark'
                        color = '#f59e0b'  # Amber
                        label = 'Oportunidad'
                    else:
                        quadrant = 'dog'
                        color = '#6b7280'  # Gray
                        label = 'Riesgo'

                action = {
                    'star': 'Invertir y mantener',
                    'cash_cow': 'Ordeñar ganancia',
                    'question_mark': 'Promocionar',
                    'dog': 'Liquidar/Evaluar'
                }.get(quadrant, 'Evaluar')

                matrix_data.append({
                    'name': item.get('name', ''),
                    'category': item.get('category', ''),
                    'x': round(market_share, 1),
                    'y': round(growth_rate, 1),
                    'z': sales,
                    'color': color,
                    'label': label,
                    'action': action,
                    'profit_margin': item.get('margin', 0),
                    'units_sold': item.get('units_sold', 0)
                })

            # Análisis por cuadrante
            quadrant_analysis = {}
            for item in matrix_data:
                quadrant = item['label']
                if quadrant not in quadrant_analysis:
                    quadrant_analysis[quadrant] = {
                        'count': 0,
                        'total_sales': 0,
                        'total_profit': 0,
                        'avg_margin': 0,
                        'items': []
                    }

                quadrant_analysis[quadrant]['count'] += 1
                quadrant_analysis[quadrant]['total_sales'] += item['z']
                quadrant_analysis[quadrant]['items'].append(item['name'])

            # Calcular márgenes promedio
            for quadrant in quadrant_analysis:
                if quadrant_analysis[quadrant]['count'] > 0:
                    quadrant_analysis[quadrant]['avg_margin'] = (
                            sum(item.get('profit_margin', 0) for item in matrix_data
                                if AIService.get_quadrant_label(item) == quadrant)
                            / quadrant_analysis[quadrant]['count']
                    )

            return {
                'matrix_data': matrix_data,
                'quadrant_analysis': quadrant_analysis,
                'total_items': len(matrix_data),
                'recommendations': AIService.get_bcg_recommendations(quadrant_analysis)
            }

        except Exception as e:
            print(f"Error en generate_bcg_matrix_analysis: {e}")
            return {}

    @staticmethod
    def get_quadrant_label(item: Dict) -> str:
        """Obtiene etiqueta del cuadrante BCG"""
        return item.get('label', '')

    @staticmethod
    def get_bcg_recommendations(quadrant_analysis: Dict) -> List[str]:
        """Genera recomendaciones basadas en análisis BCG"""
        recommendations = []

        if 'Estrella' in quadrant_analysis:
            stars = quadrant_analysis['Estrella']
            recommendations.append(
                f"Invertir en {stars['count']} productos Estrella (${stars['total_sales']:,.0f} en ventas)"
            )

        if 'Vaca Lechera' in quadrant_analysis:
            cash_cows = quadrant_analysis['Vaca Lechera']
            recommendations.append(
                f"Optimizar márgenes de {cash_cows['count']} Vacas Lecheras"
            )

        if 'Oportunidad' in quadrant_analysis:
            questions = quadrant_analysis['Oportunidad']
            recommendations.append(
                f"Promocionar {questions['count']} productos con oportunidad de crecimiento"
            )

        if 'Riesgo' in quadrant_analysis:
            dogs = quadrant_analysis['Riesgo']
            if dogs['count'] > 0:
                recommendations.append(
                    f"Reevaluar o liquidar {dogs['count']} productos de bajo rendimiento"
                )

        return recommendations

    @staticmethod
    def chat_with_gemini(prompt: str, context_data: Dict) -> str:
        """
        Simula conversación con IA (en producción usarías la API real)

        Args:
            prompt: Pregunta del usuario
            context_data: Datos de contexto del negocio

        Returns:
            str: Respuesta generada
        """
        # En producción, aquí conectarías con la API de Gemini
        # Por ahora, simulamos respuestas basadas en reglas

        prompt_lower = prompt.lower()

        # Respuestas predefinidas basadas en palabras clave
        if any(word in prompt_lower for word in ['ventas', 'vender', 'ingresos']):
            return f"📈 Tus ventas actuales son ${context_data.get('total_sales', 0):,.2f} con un margen neto del {context_data.get('net_margin', 0):.1f}%. Recomiendo focalizar en tus productos estrella."

        elif any(word in prompt_lower for word in ['inventario', 'stock', 'bodega']):
            dead_stock = context_data.get('dead_stock_count', 0)
            low_stock = context_data.get('low_stock_count', 0)
            return f"📦 Tienes {dead_stock} productos sin movimiento y {low_stock} con stock bajo. Considera promociones para los primeros y reabastecer los segundos."

        elif any(word in prompt_lower for word in ['margen', 'ganancia', 'utilidad']):
            margin = context_data.get('net_margin', 0)
            if margin < 10:
                return f"⚠️ Tu margen neto ({margin:.1f}%) está bajo. Revisa precios de compra y considera aumentar precios de venta en productos con alta demanda."
            else:
                return f"✅ Tu margen neto ({margin:.1f}%) es saludable. Continúa optimizando costos operativos."

        elif any(word in prompt_lower for word in ['recomendación', 'consejo', 'sugerencia']):
            return "🎯 Basado en tus datos: 1) Crea combos de productos complementarios 2) Implementa programa de referidos 3) Ofrece mantenimiento post-venta como servicio adicional."

        else:
            return "🤖 Soy Luxera AI. Puedo ayudarte a analizar ventas, inventario, márgenes y darte recomendaciones estratégicas. ¿En qué área necesitas ayuda específicamente?"