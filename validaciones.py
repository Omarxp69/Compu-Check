import re

def correo_valido(email: str) -> bool:
    patron = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(patron, email))



def contrasena_valida(contrasena: str) -> bool:
    patron = r'^(?=.*[A-Z])(?=.*\d)[A-Za-z\d@#$%^&+=!_]{8,}$'
    return bool(re.match(patron, contrasena))