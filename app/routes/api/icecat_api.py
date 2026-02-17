# -*- coding: utf-8 -*-
from flask import Blueprint, jsonify, request
from flask_login import login_required
from app.services.icecat_service import IcecatService
from app.utils.decorators import json_response, handle_exceptions

icecat_api_bp = Blueprint('icecat_api', __name__, url_prefix='/api/icecat')

@icecat_api_bp.route('/fetch/<gtin>', methods=['GET'])
@login_required
@json_response
@handle_exceptions
def fetch_product(gtin):
    """
    Endpoint para buscar productos en Icecat por GTIN.
    """
    if not gtin:
        return {'success': False, 'error': 'EAN/UPC no proporcionado.'}, 400
        
    try:
        data = IcecatService.fetch_by_gtin(gtin)
        return data
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error in fetch_product: {str(e)}")
        return {'success': False, 'message': f'Error al consultar Icecat: {str(e)}'}, 200
