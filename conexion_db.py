import mysql.connector
import os
from dotenv import load_dotenv
from flask import flash

import secrets
# Cargar variables de entorno
load_dotenv()
def get_connection():
    conexion = mysql.connector.connect(
        host=os.environ.get('MYSQLHOST'),
        user=os.environ.get('MYSQLUSER'),
        password=os.environ.get('MYSQLPASSWORD'),
        database=os.environ.get('MYSQLDATABASE'),
        port=int(os.environ.get('MYSQLPORT', 3306)),
    )
    return conexion



def insertar_usuario(nombre, apellido_paterno, apellido_materno, email, password):
    conn = get_connection()
    cursor = conn.cursor()


    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    if cursor.fetchone():
        return None

    token = secrets.token_urlsafe(32)

    cursor.execute(
        """
        INSERT INTO users (nombre, apellido_paterno, apellido_materno, email, password, verification_token, email_verified)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (nombre, apellido_paterno, apellido_materno, email, password, token, False)
    )
    nuevo_id = cursor.lastrowid

    # Revisar si es el primer usuario
    cursor.execute("SELECT COUNT(*) FROM users")
    total_usuarios = cursor.fetchone()[0]

    if total_usuarios == 1:
        # Si es el primero, darle rol admin
        cursor.execute("UPDATE users SET rol='admin' WHERE id=%s", (nuevo_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return token

def obtener_todos_usuarios(filtro_columna='id', orden='ASC', search=''):
    columnas_permitidas = ['id', 'nombre', 'apellido_paterno', 'apellido_materno', 'email', 'rol','estado','created_at','updated_at']
    if filtro_columna not in columnas_permitidas:
        filtro_columna = 'id'
    orden = orden.upper()
    if orden not in ['ASC', 'DESC']:
        orden = 'ASC'

    conn = get_connection()
    cursor = conn.cursor()

    query = f"""
        SELECT id, nombre, apellido_paterno, apellido_materno, email, rol, foto_perfil, estado, created_at, updated_at
        FROM users
        WHERE email_verified = TRUE
    """

    params = []
    if search:
        # si el search es un número, busca por ID; si no, por email
        if search.isdigit():
            query += " AND id = %s"
            params.append(int(search))
        else:
            query += " AND email LIKE %s"
            params.append(f"%{search}%")

    query += f" ORDER BY {filtro_columna} {orden}"
    cursor.execute(query, params)
    usuarios = cursor.fetchall()
    cursor.close()
    conn.close()
    return usuarios



def obtener_usuario_por_email(email):
    db = get_connection()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE email = %s AND estado = 1 AND email_verified = TRUE", (email,))
    user = cursor.fetchone()
    cursor.close()
    db.close()
    return user
def obtener_usuario_por_id(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)  # para obtener un diccionario
    cursor.execute("SELECT * FROM users WHERE id = %s AND estado = 1 AND email_verified = TRUE", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user


def obtener_todos_Salas(filtro_columna='id_salon', orden='ASC', search=''):
    columnas_permitidas = ['id_salon', 'nombre_salon', 'ubicacion', 'cantidad_equipos', 'estado', 'descripcion', 'fecha_creacion', 'updated_at']
    if filtro_columna not in columnas_permitidas:
        filtro_columna = 'id_salon'
    orden = orden.upper()
    if orden not in ['ASC', 'DESC']:
        orden = 'ASC'

    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT id_salon, nombre_salon, ubicacion, cantidad_equipos, estado, descripcion, fecha_creacion, updated_at
        FROM Salones
        WHERE 1=1
    """

    params = []
    if search:
        # si el search es un número, busca por ID; si no, por nombre
        if search.isdigit():
            query += " AND id_salon = %s"
            params.append(int(search))
        else:
            query += " AND nombre_salon LIKE %s"
            params.append(f"%{search}%")

    query += f" ORDER BY {filtro_columna} {orden}"

    cursor.execute(query, params)
    salones = cursor.fetchall()
    cursor.close()
    conn.close()
    return salones
def Sala_Existe(sala_id):
        conn = get_connection()
        cursor = conn.cursor()

        # Verificamos que la sala existe
        cursor.execute("SELECT id_salon FROM Salones WHERE id_salon = %s", (sala_id,))
        sala = cursor.fetchone()

        cursor.close()
        conn.close()
        return sala is not None
def eliminar_salon(sala_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Salones WHERE id_salon = %s", (sala_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
# ===================== SALONES =====================
def agregar_salon(nombre_salon, ubicacion, estado, descripcion):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO Salones (nombre_salon, ubicacion, estado, descripcion)
        VALUES (%s, %s, %s, %s)
        """,
        (nombre_salon, ubicacion, estado, descripcion)
    )
    conn.commit()
    cursor.close()
    conn.close()
# ===================== OBTENER SALONES =====================
def obtener_Salones():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Salones;")
    registros = cursor.fetchall()
    cursor.close()
    conn.close()
    return registros
def obtener_salon_por_id(id_salon):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Salones WHERE id_salon = %s AND estado='activo'", (id_salon,))
    salon = cursor.fetchone()
    cursor.close()
    conn.close()
    return salon
# ===================== COMPUTADORAS =====================
def insertar_computadora(matricula, marca, sistema_operativo, estado="bueno",
                        fecha_adquisicion=None, id_pantalla=None,
                        id_teclado=None, id_mouse=None, id_salon=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO Computadoras (
            matricula, marca, sistema_operativo, estado, fecha_adquisicion,
            id_pantalla, id_teclado, id_mouse, id_salon
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (matricula, marca, sistema_operativo, estado, fecha_adquisicion,
        id_pantalla, id_teclado, id_mouse, id_salon))
    conn.commit()
    cursor.close()
    conn.close()
def existe_matricula(matricula):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_computadora FROM Computadoras WHERE matricula = %s", (matricula,))
    existe = cursor.fetchone() is not None
    cursor.close()
    conn.close()
    return existe
# ===================== MOUSE =====================
def insertar_mouse(marca, tipo="óptico", estado="operativa", foto=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO Mouse (marca, tipo, estado, foto)
        VALUES (%s, %s, %s, %s)
        """,
        (marca, tipo, estado, foto)
    )
    mouse_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    return mouse_id  # retornamos el id
# ===================== TECLADOS =====================
def insertar_teclado(marca, tipo="mecánico", estado="operativa", foto=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO Teclados (marca, tipo, estado, foto)
        VALUES (%s, %s, %s, %s)
        """,
        (marca, tipo, estado, foto)
    )
    teclado_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    return teclado_id  # retornamos el id
# ===================== PANTALLAS =====================
def insertar_pantalla(marca, estado="operativa", foto=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO Pantallas (marca, estado, foto)
        VALUES (%s, %s, %s)
        """,
        (marca, estado, foto)
    )
    pantalla_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    return pantalla_id  # retornamos el id
# ===================== OBTENER ID Y NOMBRE DE SALONES =====================
def obtener_id_y_nombre_salones(filtrar_por_permiso, user_id=None):
    conn = get_connection()
    cursor = conn.cursor()

    if filtrar_por_permiso and user_id is not None:
        # Retorna solo los salones a los que el usuario tiene permiso
        cursor.execute("""
            SELECT s.id_salon, s.nombre_salon
            FROM Salones s
            INNER JOIN Permisos p ON s.id_salon = p.id_salon
            WHERE p.id_usuario = %s;
        """, (user_id,))
    else:
        # Retorna todos los salones
        cursor.execute("SELECT id_salon, nombre_salon FROM Salones;")

    resultados = cursor.fetchall()
    cursor.close()
    conn.close()
    return resultados



def obtener_computadora_por_salon(id_salon):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT id_computadora, matricula 
        FROM Computadoras 
        WHERE id_salon = %s
    """
    cursor.execute(query, (id_salon,))
    computadoras = cursor.fetchall()

    cursor.close()
    conn.close()
    return computadoras
def obtener_computadoras_con_sala_id(sala_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id_computadora, id_mouse, id_teclado, id_pantalla FROM Computadoras WHERE id_salon = %s", (sala_id,))
    computadoras = cursor.fetchall()
    cursor.close()
    conn.close()
    return computadoras
def Cantidad_equipos(id_salon):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Salones SET cantidad_equipos = IFNULL(cantidad_equipos, 0) + 1 WHERE id_salon = %s",
        (id_salon,)
    )
    conn.commit()
    cursor.close()
    conn.close()
def obtener_todas_computadoras(filtro_columna='id_computadora', orden='ASC', search=''):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT 
            -- Computadora
            c.id_computadora,
            c.matricula,
            c.marca AS marca_pc,
            c.sistema_operativo,
            c.estado AS estado_pc,
            c.fecha_adquisicion,
            c.id_pantalla,
            c.id_teclado,
            c.id_mouse,
            c.id_salon,
            c.fecha_creacion AS fecha_creacion_pc,
            c.updated_at AS actualizado_pc,
            
            -- Mouse
            m.id_mouse AS mouse_id,
            m.marca AS marca_mouse,
            m.tipo AS tipo_mouse,
            m.estado AS estado_mouse,
            m.foto AS foto_mouse,
            m.fecha_creacion AS fecha_creacion_mouse,
            m.updated_at AS actualizado_mouse,
            
            -- Teclado
            t.id_teclado AS teclado_id,
            t.marca AS marca_teclado,
            t.tipo AS tipo_teclado,
            t.estado AS estado_teclado,
            t.foto AS foto_teclado,
            t.fecha_creacion AS fecha_creacion_teclado,
            t.updated_at AS actualizado_teclado,
            
            -- Pantalla
            p.id_pantalla AS pantalla_id,
            p.marca AS marca_pantalla,
            p.estado AS estado_pantalla,
            p.foto AS foto_pantalla,
            p.fecha_creacion AS fecha_creacion_pantalla,
            p.updated_at AS actualizado_pantalla,
            
            -- Salón
            s.id_salon AS salon_id,
            s.nombre_salon,
            s.ubicacion,
            s.cantidad_equipos,
            s.estado AS estado_salon,
            s.descripcion,
            s.fecha_creacion AS fecha_creacion_salon,
            s.updated_at AS actualizado_salon
        FROM Computadoras c
        LEFT JOIN Mouse m ON c.id_mouse = m.id_mouse
        LEFT JOIN Teclados t ON c.id_teclado = t.id_teclado
        LEFT JOIN Pantallas p ON c.id_pantalla = p.id_pantalla
        INNER JOIN Salones s ON c.id_salon = s.id_salon
        WHERE 1=1
    """

    params = []
    if search:
        if search.isdigit():
            query += " AND c.id_computadora = %s"
            params.append(int(search))
        else:
            query += " AND (c.matricula LIKE %s OR c.marca LIKE %s OR s.nombre_salon LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    # Columnas permitidas para ordenar
    columnas_map = {
        'id_computadora': 'c.id_computadora',
        'matricula': 'c.matricula',
        'marca_pc': 'c.marca',
        'sistema_operativo': 'c.sistema_operativo',
        'estado_pc': 'c.estado',
        'fecha_adquisicion': 'c.fecha_adquisicion',
        'fecha_creacion_pc': 'c.fecha_creacion',
        'actualizado_pc': 'c.updated_at',
        'mouse_id': 'm.id_mouse',
        'marca_mouse': 'm.marca',
        'tipo_mouse': 'm.tipo',
        'estado_mouse': 'm.estado',
        'teclado_id': 't.id_teclado',
        'marca_teclado': 't.marca',
        'tipo_teclado': 't.tipo',
        'estado_teclado': 't.estado',
        'pantalla_id': 'p.id_pantalla',
        'marca_pantalla': 'p.marca',
        'estado_pantalla': 'p.estado',
        'salon_id': 's.id_salon',
        'nombre_salon': 's.nombre_salon',
        'ubicacion': 's.ubicacion',
        'cantidad_equipos': 's.cantidad_equipos',
        'estado_salon': 's.estado',
        'descripcion': 's.descripcion'
    }

    filtro_columna = columnas_map.get(filtro_columna, 'c.id_computadora')
    orden = orden.upper()
    if orden not in ['ASC', 'DESC']:
        orden = 'ASC'

    query += f" ORDER BY {filtro_columna} {orden}"

    cursor.execute(query, params)
    computadoras = cursor.fetchall()
    cursor.close()
    conn.close()
    return computadoras
def obtener_usuarios_basico(filtro_columna='id', orden='ASC', search=''):
    columnas_permitidas = ['id', 'nombre','email']
    if filtro_columna not in columnas_permitidas:
        filtro_columna = 'id'
    orden = orden.upper()
    if orden not in ['ASC', 'DESC']:
        orden = 'ASC'
   
   
    conn = get_connection()
    cursor = conn.cursor()


    query = f"""
        SELECT id, nombre, email
        FROM users
        WHERE estado = 1 AND rol = 'user'
    """


    params = []
    if search:
        # si el search es un número, busca por ID; si no, por email
        if search.isdigit():
            query += " AND id = %s"
            params.append(int(search))
        else:
            query += " AND email LIKE %s"
            params.append(f"%{search}%")

    query += f" ORDER BY {filtro_columna} {orden}"
    cursor.execute(query, params)
    usuarios = cursor.fetchall()
    cursor.close()
    conn.close()
    return usuarios
def obtener_salon_basico(filtro_columna='id_salon', orden='ASC', search=''):
    
    columnas_permitidas = ['id_salon', 'nombre_salon']
    if filtro_columna not in columnas_permitidas:
        filtro_columna = 'id_salon'
    orden = orden.upper()
    if orden not in ['ASC', 'DESC']:
        orden = 'ASC'

    conn = get_connection()
    cursor = conn.cursor()
    query = """
        SELECT id_salon, nombre_salon
        FROM Salones
        WHERE estado = 'activo'
    """
    params = []
    if search:
        # si el search es un número, busca por ID; si no, por nombre
        if search.isdigit():
            query += " AND id_salon = %s"
            params.append(int(search))
        else:
            query += " AND nombre_salon LIKE %s"
            params.append(f"%{search}%")

    query += f" ORDER BY {filtro_columna} {orden}"
    

    cursor.execute(query, params)
    salones = cursor.fetchall()
    cursor.close()
    conn.close()
    return salones
def insertar_acceso_salon(id_usuario, id_salon, asignado_por):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Permisos (id_usuario, id_salon, asignado_por)
            VALUES (%s, %s, %s)
        """, (id_usuario, id_salon, asignado_por))
        conn.commit()
    except Exception as e:
        print("Error al asignar acceso a salón:", e)
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
def permiso_existente(id_usuario, id_salon):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 1 FROM Accesos_Salones
            WHERE id_usuario = %s AND id_salon = %s
        """, (id_usuario, id_salon))
        existe = cursor.fetchone() is not None
        return existe
    except Exception as e:
        print("Error al verificar acceso existente:", e)
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
def obtener_permisos(filtro_columna='id_permiso', orden='ASC', search=''):
    # Columnas permitidas para ordenamiento
    columnas_permitidas = [
    'id_permiso', 'id_usuario', 'nombre_usuario',
    'email', 'id_salon', 'nombre_salon', 'fecha_asignacion', 'asignado_por'
]
    if filtro_columna not in columnas_permitidas:
        filtro_columna = 'id_permiso'

    orden = orden.upper()
    if orden not in ['ASC', 'DESC']:
        orden = 'ASC'

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT 
            p.id_permiso,
            u.id AS id_usuario,
            u.nombre AS nombre_usuario,
            u.email AS email,
            s.id_salon AS id_salon,
            s.nombre_salon,
            p.fecha_asignacion,
            asignador.nombre AS asignado_por
        FROM Permisos p
        INNER JOIN users u ON p.id_usuario = u.id
        INNER JOIN Salones s ON p.id_salon = s.id_salon
        LEFT JOIN users asignador ON p.asignado_por = asignador.id
    """

    params = []
    if search:
        # Si es un número, buscar por id_permiso; si no, por nombre de usuario o nombre del salón
        if search.isdigit():
            query += " WHERE p.id_permiso = %s"
            params.append(int(search))
        else:
            query += " WHERE u.nombre LIKE %s OR u.email LIKE %s OR s.nombre_salon LIKE %s"
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    query += f" ORDER BY {filtro_columna} {orden}"

    cursor.execute(query, params)
    permisos = cursor.fetchall()
    cursor.close()
    conn.close()
    return permisos
def eliminar_permiso(permiso_id):
    conn = None
    cursor = None
    # Eliminar permiso
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("DELETE FROM Permisos WHERE id_permiso = %s", (permiso_id,))
        conn.commit()
        if cursor.rowcount > 0:
            flash("✅ Permiso eliminado correctamente.")
        else:
            flash("⚠️ No se encontró el permiso con ese ID.")
    except Exception as e:
        print("Error al eliminar permiso:", e)
        flash("❌ Error al eliminar el permiso.")
    finally:
        cursor.close()
        conn.close()
def actualizar_pantalla_db(id_pantalla, marca_pantalla, estado_pantalla, foto_filename=None):
    conexion = get_connection()
    cursor = conexion.cursor()

    if foto_filename:
        # Si se sube una nueva foto, actualizar todo
        sql = """
        UPDATE Pantallas 
        SET marca=%s, estado=%s, foto=%s, updated_at=NOW() 
        WHERE id_pantalla=%s
        """
        cursor.execute(sql, (marca_pantalla, estado_pantalla, foto_filename, id_pantalla))
    else:
        # Si no hay foto nueva, mantener la existente
        sql = """
        UPDATE Pantallas 
        SET marca=%s, estado=%s, updated_at=NOW() 
        WHERE id_pantalla=%s
        """
        cursor.execute(sql, (marca_pantalla, estado_pantalla, id_pantalla))

    conexion.commit()
    cursor.close()
    conexion.close()
def actualizar_teclado_db(id_teclado,marca_teclado,tipo_teclado,estado_teclado,foto_filename):
    conexion = get_connection()
    cursor = conexion.cursor()

    if foto_filename:
        # Si se sube una nueva foto, actualizar todo
        sql = """
        UPDATE Teclados 
        SET marca=%s, tipo=%s , estado=%s, foto=%s, updated_at=NOW() 
        WHERE id_teclado=%s
        """
        cursor.execute(sql, (marca_teclado, tipo_teclado, estado_teclado, foto_filename, id_teclado))
    else:
        # Si no hay foto nueva, mantener la existente
        sql = """
        UPDATE Teclados 
        SET marca=%s, tipo=%s, estado=%s, updated_at=NOW() 
        WHERE id_teclado=%s
        """
        cursor.execute(sql, (marca_teclado, tipo_teclado, estado_teclado, id_teclado))

    conexion.commit()
    cursor.close()
    conexion.close()
def actualizar_mouse_db(id_mouse,marca_mouse,tipo_mouse,estado_mouse,foto_filename):
    conexion = get_connection()
    cursor = conexion.cursor()

    if foto_filename:
        # Si se sube una nueva foto, actualizar todo
        sql = """
        UPDATE Mouse 
        SET marca=%s, tipo=%s , estado=%s, foto=%s, updated_at=NOW() 
        WHERE id_mouse=%s
        """
        cursor.execute(sql, (marca_mouse, tipo_mouse, estado_mouse, foto_filename, id_mouse))
    else:
        # Si no hay foto nueva, mantener la existente
        sql = """
        UPDATE Mouse 
        SET marca=%s, tipo=%s, estado=%s, updated_at=NOW() 
        WHERE id_mouse=%s
        """
        cursor.execute(sql, (marca_mouse, tipo_mouse, estado_mouse, id_mouse))

    conexion.commit()
    cursor.close()
    conexion.close()
def insertar_reporte(id_usuario, id_salon, id_computadora, 
                    id_pantalla=None, id_teclado=None, id_mouse=None,
                    estado_pantalla='operativa', score_pantalla=None,
                    estado_teclado='operativa', score_teclado=None,
                    estado_mouse='operativa', score_mouse=None,
                    comentarios=None):
    print('------Entro a insertar reporte------')
    conexion = get_connection()
    cursor = conexion.cursor()
    sql = """
        INSERT INTO Reportes (
            id_usuario, id_salon, id_computadora,
            id_mouse, id_teclado, id_pantalla,
            estado_mouse, score_mouse,
            estado_teclado, score_teclado,
            estado_pantalla, score_pantalla,
            comentarios
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    valores = (
        id_usuario, id_salon, id_computadora,
        id_mouse, id_teclado, id_pantalla,
        estado_mouse, score_mouse,
        estado_teclado, score_teclado,
        estado_pantalla, score_pantalla,
        comentarios
    )
    cursor.execute(sql, valores)
    conexion.commit()

    last_id = cursor.lastrowid  # Guardar el id antes de cerrar
    cursor.close()
    conexion.close()
    return last_id  # Devuelve el id del reporte insertado
def obtener_ids_perifericos(id_computadora):
    print('------Entro a obtener_ids_perifericos ------')
    conexion = get_connection()
    cursor = conexion.cursor(dictionary=True)  # Para que devuelva diccionario

    sql = """
        SELECT id_pantalla, id_teclado, id_mouse
        FROM Computadoras
        WHERE id_computadora = %s
    """
    cursor.execute(sql, (id_computadora,))
    resultado = cursor.fetchone()  # Devuelve None si no existe

    cursor.close()
    conexion.close()

    if resultado:
        return {
            'pantalla': resultado['id_pantalla'],
            'teclado': resultado['id_teclado'],
            'mouse': resultado['id_mouse']
        }
    else:
        return None
def actualizar_estado_foto_pantalla(id_pantalla, estado_pantalla, foto_filename):
    print('---------- actualizar_estado_foto_pantalla ------------------')
    print(f"ID_Pantalla: {id_pantalla}")
    print(f"Estado_pantalla: {estado_pantalla}")
    print(f"Foto_file: {foto_filename}")

    conexion = get_connection()
    cursor = conexion.cursor()


    if foto_filename:
        # Si se sube una nueva foto, actualizar todo
        sql = """
        UPDATE Pantallas 
        SET estado=%s, foto=%s, updated_at=NOW() 
        WHERE id_pantalla=%s
        """
        cursor.execute(sql, (estado_pantalla, foto_filename, id_pantalla))
    conexion.commit()
    cursor.close()
    conexion.close()
def actualizar_estado_foto_teclado(id_teclado, estado_teclado, foto_filename):
    print('---------- actualizar_estado_foto_teclado ------------------')
    print(f"ID_Teclado: {id_teclado}")
    print(f"Estado_Teclado: {estado_teclado}")
    print(f"Foto_file: {foto_filename}")

    conexion = get_connection()
    cursor = conexion.cursor()

    if foto_filename:
        # Si se sube una nueva foto, actualizar todo
        sql = """
        UPDATE Teclados 
        SET estado=%s, foto=%s, updated_at=NOW() 
        WHERE id_teclado=%s
        """
        cursor.execute(sql, (estado_teclado, foto_filename, id_teclado))

    conexion.commit()
    cursor.close()
    conexion.close()
def actualizar_estado_foto_mouse(id_mouse, estado_mouse, foto_filename):
    print('------Entro a actualizar_estado_foto_mouse ------')
    print(f"ID_Mouse: {id_mouse}")
    print(f"Estado_Mouse: {estado_mouse}")
    print(f"Foto_file: {foto_filename}")


    conexion = get_connection()
    cursor = conexion.cursor()

    if foto_filename:
        # Si se sube una nueva foto, actualizar todo
        sql = """
        UPDATE Mouse 
        SET estado=%s, foto=%s, updated_at=NOW() 
        WHERE id_mouse=%s
        """
        cursor.execute(sql, (estado_mouse, foto_filename, id_mouse))

    conexion.commit()
    cursor.close()
    conexion.close()
def obtener_todos_reportes(filtro_columna='id_reporte', orden='ASC', search=''):
    # Columnas permitidas para ordenar (por seguridad)
    columnas_permitidas = [
        'id_reporte', 'nombre_usuario', 'nombre_salon', 'matricula',
        'estado_mouse', 'estado_teclado', 'estado_pantalla',
        'estado_reporte', 'fecha_reporte'
    ]
    if filtro_columna not in columnas_permitidas:
        filtro_columna = 'id_reporte'

    orden = orden.upper()
    if orden not in ['ASC', 'DESC']:
        orden = 'ASC'

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)  # ← Esto devuelve diccionarios, no tuplas

    query = f"""
        SELECT 
            r.id_reporte,
            CONCAT(u.nombre, ' ', u.apellido_paterno, ' ', u.apellido_materno) AS nombre_usuario,
            s.nombre_salon,
            c.matricula AS matricula_computadora,
            r.estado_mouse,
            r.score_mouse,
            r.estado_teclado,
            r.score_teclado,
            r.estado_pantalla,
            r.score_pantalla,
            r.comentarios,
            r.estado_reporte,
            r.fecha_reporte
        FROM Reportes r
        INNER JOIN users u ON r.id_usuario = u.id
        INNER JOIN Salones s ON r.id_salon = s.id_salon
        INNER JOIN Computadoras c ON r.id_computadora = c.id_computadora
        WHERE 1=1
    """

    params = []
    if search:
        if search.isdigit():
            query += " AND (r.id_reporte = %s OR c.matricula LIKE %s)"
            params.extend([int(search), f"%{search}%"])
        else:
            query += """
                AND (
                    u.nombre LIKE %s OR 
                    u.apellido_paterno LIKE %s OR 
                    s.nombre_salon LIKE %s OR 
                    c.matricula LIKE %s OR
                    r.comentarios LIKE %s
                )
            """
            params.extend([f"%{search}%"] * 5)

    query += f" ORDER BY {filtro_columna} {orden}"

    cursor.execute(query, params)
    reportes = cursor.fetchall()
    cursor.close()
    conn.close()
    return reportes
def eliminar_reporte(id_reporte):
    conexion = None
    cursor = None
    try:
        conexion = get_connection()
        cursor = conexion.cursor(dictionary=True)

        # Ejecutar eliminación
        cursor.execute("DELETE FROM Reportes WHERE id_reporte = %s", (id_reporte,))
        conexion.commit()

        if cursor.rowcount > 0:
            flash("✅ Reporte eliminado correctamente.")
        else:
            flash("⚠️ No se encontró un reporte con ese ID.")

    except Exception as e:
        print("Error al eliminar reporte:", e)
        flash("❌ Ocurrió un error al intentar eliminar el reporte.")

    finally:
        if cursor:
            cursor.close()
        if conexion:
            conexion.close()












__all__ = [
    'get_connection',
    'insertar_usuario',
    'obtener_todos_usuarios',
    'obtener_usuario_por_email',
    'obtener_usuario_por_id',
    'obtener_todos_Salas',
    'Sala_Existe',
    'eliminar_salon',
    'agregar_salon',
    'obtener_Salones',
    'insertar_computadora',
    'existe_matricula',
    'insertar_mouse',
    'insertar_teclado',
    'insertar_pantalla',
    'obtener_id_y_nombre_salones',
    'obtener_computadoras_con_sala_id',
    'Cantidad_equipos',
    'obtener_todas_computadoras',
    'obtener_usuarios_basico',
    'obtener_salon_basico',
    'insertar_acceso_salon',
    'permiso_existente',
    'obtener_salon_por_id',
    'obtener_permisos',
    'eliminar_permiso',
    'actualizar_pantalla_db',
    'actualizar_teclado_db',
    'actualizar_mouse_db',
    'obtener_computadora_por_salon',
    'insertar_reporte',
    'obtener_ids_perifericos',
    'actualizar_estado_foto_pantalla',
    'actualizar_estado_foto_teclado',
    'actualizar_estado_foto_mouse',
    'obtener_todos_reportes',
    'eliminar_reporte'
]

