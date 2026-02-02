# -*- coding: utf-8 -*-
import re

def validate_password_strength(password):
    """
    Valida la fortaleza de la contraseña según políticas de seguridad.
    
    Requisitos:
    - Mínimo 8 caracteres
    - Al menos una mayúscula
    - Al menos una minúscula
    - Al menos un número
    - Al menos un caracter especial
    
    Returns:
        tuple: (bool, message)
        - True, "OK" si es válida
        - False, "Mensaje de error" si no cumple
    """
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres."
        
    if not re.search(r"[A-Z]", password):
        return False, "La contraseña debe contener al menos una letra mayúscula."
        
    if not re.search(r"[a-z]", password):
        return False, "La contraseña debe contener al menos una letra minúscula."
        
    if not re.search(r"\d", password):
        return False, "La contraseña debe contener al menos un número."
        
    if not re.search(r"[ !@#$%^&*()_+\-=\[\]{};':\\|,.<>/?]", password):
        return False, "La contraseña debe contener al menos un caracter especial (!@#$%^&*)."
        
    return True, "OK"
