from flask import Flask, jsonify,render_template,make_response,redirect,request,flash,url_for,session
import bcrypt
from functools import wraps
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import glob 
from datetime import timedelta,datetime

from tensorflow.keras.applications import MobileNetV2



# -----Archivos de python--------
from funciones_ia import clasificar_dispositivos,prueba
from config import config
from validaciones import correo_valido, contrasena_valida 
from conexion_db import (
    get_connection,
    insertar_usuario,
    obtener_todos_usuarios,
    obtener_usuario_por_email,
    obtener_usuario_por_id,
    obtener_todos_Salas,
    Sala_Existe,
    eliminar_salon,
    agregar_salon,
    obtener_Salones,
    insertar_computadora,
    existe_matricula,
    insertar_mouse,
    insertar_teclado,
    insertar_pantalla,
    obtener_id_y_nombre_salones,
    obtener_computadoras_con_sala_id,
    Cantidad_equipos,
    obtener_todas_computadoras,
    obtener_usuarios_basico,
    obtener_salon_basico,
    insertar_acceso_salon,
    permiso_existente,
    obtener_salon_por_id,
    obtener_permisos,
    eliminar_permiso,
    actualizar_pantalla_db,
    actualizar_teclado_db,
    actualizar_mouse_db,
    obtener_computadora_por_salon,
    insertar_reporte,
    obtener_ids_perifericos,
    actualizar_estado_foto_pantalla,
    actualizar_estado_foto_teclado,   
    actualizar_estado_foto_mouse
)





load_dotenv()
app=Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
app.permanent_session_lifetime = timedelta(hours=1)

# -------------- Manejo de rutas para archivos --------------
UPLOAD_FOLDER = 'static/uploads/foto_perfil'
MAIN_UPLOAD_FOLDER = 'static/uploads'

PANTALLAS_FOLDER = os.path.join(MAIN_UPLOAD_FOLDER, 'pantallas')
TECLADOS_FOLDER = os.path.join(MAIN_UPLOAD_FOLDER, 'teclados')
MOUSE_FOLDER = os.path.join(MAIN_UPLOAD_FOLDER, 'mouse')
TEMPORAL_FOLDER=os.path.join(MAIN_UPLOAD_FOLDER, 'Temporal')

for folder in [PANTALLAS_FOLDER, TECLADOS_FOLDER, MOUSE_FOLDER,TEMPORAL_FOLDER]:
    os.makedirs(folder, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['MAIN_UPLOAD_FOLDER'] = MAIN_UPLOAD_FOLDER
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PANTALLAS_FOLDER'] = PANTALLAS_FOLDER
app.config['TECLADOS_FOLDER'] = TECLADOS_FOLDER
app.config['MOUSE_FOLDER'] = MOUSE_FOLDER
app.config['UPLOAD_FOLDER_TEMP'] = TEMPORAL_FOLDER
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#---------- Roles de usuario y sesiones -------------------
ROLE_DASHBOARDS = {
    'admin': 'dashboard',
    'moderador': 'dashboard',
    'user': 'dashboard'
}
def role_required(*roles_permitidos):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session:
                flash("❌ Debes iniciar sesión")
                return redirect(url_for('login'))
            if session['role'] not in roles_permitidos:
                flash("❌ Acceso denegado")
                # Redirige al dashboard según su rol si no tiene permisos
                return redirect(url_for(ROLE_DASHBOARDS.get(session['role'], 'index')))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def logout_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' in session:
            # Redirige al dashboard correspondiente según rol
            return redirect(url_for(ROLE_DASHBOARDS.get(session['role'], 'index')))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. Verificar sesión
        if 'role' not in session or session['role'] != 'admin':
            flash("❌ Acceso denegado")
            return redirect(url_for('login'))

        # 2. Verificar que usuario existe en DB
        user = obtener_usuario_por_email(session.get('email'))
        if not user:
            session.clear()
            flash("❌ Usuario no encontrado. Inicia sesión de nuevo.")
            return redirect(url_for('login'))

        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            flash("❌ Debes iniciar sesión primero.")
            return redirect(url_for('login'))
        
        user = obtener_usuario_por_id(user_id)
        if not user:
            flash("❌ Usuario no encontrado o inactivo.")
            session.pop('user_id', None)
            return redirect(url_for('login'))
        
        # Guardamos el usuario en g para que esté disponible en la ruta
        from flask import g
        g.current_user = user

        return f(*args, **kwargs)
    return decorated_function
@app.before_request
def check_session_timeout():
    now = datetime.utcnow().timestamp()  # float
    last_active = session.get('last_active')
    if last_active is not None:
        delta = now - last_active
        if delta > 3600:  # una hora
            session.clear()
            flash("⚠️ Tu sesión ha expirado.")
            return redirect(url_for('login'))
    session['last_active'] = now


# ---------- ERRORES ------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(405)
def page_not_found(e):
    return render_template('405.html'), 405


#------------- lOGUEO DE USUARIO E INICIO DE SESION ---------------------
@app.route("/")
@logout_required
def index():
    return render_template('inicio.html')
    

@app.route("/login", methods=["GET", "POST"])
@logout_required
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            flash("❌ Debes llenar todos los campos")
            return redirect(url_for('login'))
        
        user=obtener_usuario_por_email(email)
        if user and bcrypt.checkpw(password.encode('utf-8'), user[5].encode()):
            session['nombre'] = user[1]  # username
            session['email']=user[4]     #email
            session['role'] = user[9]    # role
            session['user_id'] = user[0]
            session.permanent = True
            flash("✅ Login exitoso")
            #return redirect(url_for(ROLE_DASHBOARDS.get(user[9], 'index')))
            return redirect(url_for('dashboard'))
        else:
            flash("❌ Login fallido")
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route("/register", methods=["GET", "POST"])
@logout_required
def register():
    if request.method == "POST":
        # Leer datos del formulario
        apellido_paterno = request.form.get('apellido_paterno')
        apellido_materno = request.form.get('apellido_materno')
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        # Validaciones
        if not correo_valido(email):
            flash("❌ Correo no válido")
            return redirect(url_for('register'))
        if obtener_usuario_por_email(email):
            flash("❌ El correo ya está registrado")
            return redirect(url_for('register'))
        if not contrasena_valida(password):
            flash("❌ La contraseña debe tener mínimo 8 caracteres, una letra mayúscula, un número")
            return redirect(url_for('register'))
        if password != confirm_password:
            flash("❌ Las contraseñas no coinciden")
            return redirect(url_for('register'))
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode()
        insertar_usuario(nombre,apellido_paterno,apellido_materno,email,hashed_password)
        flash("✅ Registro exitoso. Ahora puedes iniciar sesión.")
        return redirect(url_for('login'))
    return render_template("register.html")


@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash("✅ Has cerrado sesión correctamente")
    return redirect(url_for('index'))

def get_current_user():
    email = session.get('email')
    if not email:
        return None  # Usuario no logueado
    user = obtener_usuario_por_email(email)  # Trae todos los datos de la DB
    #print(user)
    if not user:
        return None  # Usuario no encontrado en la DB

    return {
        'id': user[0],
        'name': user[1],
        'apellido_paterno': user[2],
        'apellido_materno': user[3],
        'email': user[4],
        'role': user[9],  # Ajusta según la posición del rol en tu tabla
        'foto_perfil':user[6]
    }





#--------------------------- VENTANA PRINCIPAL ----------------------------------

@app.route('/dashboard')
@login_required
@role_required('admin', 'moderador', 'user')
def dashboard():

    user = get_current_user()

    user_obtenido = obtener_usuario_por_id(session['user_id'])
    if not user:
        session.clear()
        flash("⚠️ Tu sesión ha expirado.")
        return redirect(url_for('login'))


    if not user:
        flash("❌ Debes iniciar sesión")
        return redirect(url_for('login'))
    user_name=user['name'].capitalize()
    user_role=user['role']
    user_profile_pic=user['foto_perfil']

    return render_template('dashboard.html',user_name=user_name,user_role=user_role,user_profile_pic=user_profile_pic)


#--------------------------- RUTA PERFIL ----------------------------------
@app.route('/update_profile', methods=['POST'])
@role_required('admin', 'moderador', 'user')
@login_required
def update_profile():
    user_id = session.get("user_id")
    if not user_id:
        flash("⚠️ Debes iniciar sesión.")
        return redirect(url_for('login'))

    db = get_connection()
    cursor = db.cursor()

    updated = False

    # --- FOTO DE PERFIL ---
    file = request.files.get('foto_perfil')
    if file and allowed_file(file.filename):
        
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        pattern = os.path.join(app.config['UPLOAD_FOLDER'], f"user_{user_id}.*")
        for old_file in glob.glob(pattern):
            try:
                os.remove(old_file)
            except OSError:
                pass

        extension = file.filename.rsplit('.', 1)[1].lower()
        filename = secure_filename(f"user_{user_id}.{extension}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        relative_path = f"uploads/foto_perfil/{filename}"
        cursor.execute("UPDATE users SET foto_perfil = %s WHERE id = %s", (relative_path, user_id))
        flash("✅ Foto de perfil actualizada.")
        updated = True

    # --- FECHA DE NACIMIENTO ---
    fecha = request.form.get("fecha_nacimiento")
    if fecha:
        cursor.execute("UPDATE users SET fecha_nacimiento = %s WHERE id = %s", (fecha, user_id))
        flash("✅ Fecha de nacimiento actualizada.")
        updated = True
    # --- GÉNERO ---
    genero = request.form.get("genero")
    if genero:
        cursor.execute("UPDATE users SET genero = %s WHERE id = %s", (genero, user_id))
        flash("✅ Género actualizado.")
        updated = True
    if updated:
        db.commit()
    cursor.close()
    db.close()
    # Nunca redirijas a login, siempre al dashboard
    return redirect(url_for('perfil'))

@app.route('/delete_account', methods=['POST'])
@login_required
@role_required('admin', 'moderador', 'user')
def delete_account():
    user_id = session.get("user_id")
    if not user_id:
        flash("⚠️ Debes iniciar sesión para eliminar tu cuenta.")
        return redirect(url_for('login'))
    db = get_connection()
    cursor = db.cursor()
    # Cambiar estado a 0 (inactivo)
    cursor.execute("UPDATE users SET estado = 0 WHERE id = %s", (user_id,))
    db.commit()
    cursor.close()
    db.close()
    # Limpiar sesión
    session.clear()
    flash("✅ Tu cuenta ha sido desactivada. Puedes reactivarla más tarde.")
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
@role_required('admin', 'moderador', 'user')
def perfil():
    user = get_current_user()
    user_name=user['name'].capitalize()
    user_role=user['role']
    user_profile_pic=user['foto_perfil']

    return render_template('profile.html',user_name=user_name,user_profile_pic=user_profile_pic,user_role=user_role)

#--------------------------- SALAS ----------------------------------
@app.route('/Salas', methods=['GET', 'POST'])
@login_required
@admin_required
def salas():
    user = get_current_user()
    user_name=user['name'].capitalize()
    user_role=user['role']
    user_profile_pic=user['foto_perfil']

    if request.method == 'POST':
        nombre_salon = request.form['nombre_salon'].strip()
        ubicacion = request.form['ubicacion'].strip()
        estado = request.form['estado'].strip()
        descripcion = request.form['descripcion'].strip() 

        # Validaciones básicas
        #si el nombre de la sala esta vacio o es muy largo
        if not nombre_salon or len(nombre_salon) > 100:
            flash("❌ El nombre de la sala es inválido.")
            return render_template('salas.html', user_name=user_name, user_role=user_role, user_profile_pic=user_profile_pic)
        #si la ubicacion esta vacia o es muy larga
        if not ubicacion or len(ubicacion) > 150:
            flash("❌ La ubicación es inválida.")
            return render_template('salas.html', user_name=user_name, user_role=user_role, user_profile_pic=user_profile_pic)
        #si el estado no es uno de los permitidos
        if estado not in ('activo','mantenimiento','fuera de servicio'):
            flash("❌ Estado no válido.")
            return render_template('salas.html', user_name=user_name, user_role=user_role, user_profile_pic=user_profile_pic)
        #si la descripcion es muy larga
        if len(descripcion) > 500:  # opcional, límite de caracteres
            flash("❌ La descripción es demasiado larga.")
            return render_template('salas.html', user_name=user_name, user_role=user_role, user_profile_pic=user_profile_pic)
        agregar_salon(nombre_salon, ubicacion, estado, descripcion)
        flash("✅ Sala agregada exitosamente.")
    return render_template('salas.html',user_name=user_name,user_role=user_role,user_profile_pic=user_profile_pic)

@app.route('/Gestionar_Salas', methods=['GET', 'POST'])
@login_required
@admin_required
def gestionar_salas():
    user = get_current_user()
    user_name = user['name'].capitalize()
    user_role = user['role']
    user_profile_pic = user['foto_perfil']

    # Leer parámetros de filtro desde GET
    filtro_columna = request.args.get('filtro_columna', 'id_salon')
    orden = request.args.get('orden', 'ASC')
    search = request.args.get('search', '').strip()  # nuevo parámetro de búsqueda

    Salones = obtener_todos_Salas(filtro_columna=filtro_columna, orden=orden, search=search)

    return render_template('Gestionar_Salas.html',
        user_name=user_name,
        user_role=user_role,
        user_profile_pic=user_profile_pic,
        Salones=Salones,
        filtro_columna=filtro_columna,
        orden=orden,
        search=search
    )

@app.route('/actualizar_sala', methods=['POST'])
@login_required
@admin_required
def actualizar_sala():
    sala_id = request.form.get('sala_id')
    estado = request.form.get('estado')
    admin_password = request.form.get('admin_password')


    if not sala_id or not sala_id.isdigit():
        flash("❌ Primero debes seleccionar una sala de la tabla.")
        return redirect(url_for('gestionar_salas'))

    if not admin_password:
        flash("❌ Debes ingresar tu contraseña para actualizar la sala.")
        return redirect(url_for('gestionar_salas'))

    # Verificar contraseña admin
    admin = get_current_user()
    if not bcrypt.checkpw(admin_password.encode('utf-8'), obtener_usuario_por_email(admin['email'])[5].encode()):
        flash("❌ Contraseña incorrecta.")
        return redirect(url_for('gestionar_salas'))
    

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE Salones SET estado = %s, updated_at = NOW() WHERE id_salon = %s", (estado, sala_id))
    conn.commit()
    cursor.close()
    conn.close()

    flash("✅ Estado de la sala actualizado correctamente.")
    return redirect(url_for('gestionar_salas'))

@app.route('/eliminar_sala', methods=['POST'])
@login_required
@admin_required
def eliminar_sala():
    try:
        sala_id = int(request.form.get('sala_id'))
    except (TypeError, ValueError):
        flash("❌ ID de sala inválido.")
        return redirect(url_for('gestionar_salas'))

    admin_password = request.form.get('admin_password')
    if not admin_password:
        flash("❌ Debes ingresar tu contraseña para eliminar la sala.")
        return redirect(url_for('gestionar_salas'))

    # Verificar contraseña admin
    admin = get_current_user()
    if not bcrypt.checkpw(admin_password.encode('utf-8'), obtener_usuario_por_email(admin['email'])[5].encode()):
        flash("❌ Contraseña incorrecta.")
        return redirect(url_for('gestionar_salas'))

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Verificar existencia de la sala
        cursor.execute("SELECT id_salon FROM Salones WHERE id_salon = %s", (sala_id,))
        sala = cursor.fetchone()
        if not sala:
            flash("❌ La sala no existe.")
            return redirect(url_for('gestionar_salas'))

        # Obtener todas las computadoras y sus periféricos
        cursor.execute("""
            SELECT id_computadora, id_mouse, id_teclado, id_pantalla
            FROM Computadoras
            WHERE id_salon = %s
        """, (sala_id,))
        computadoras = cursor.fetchall()

        # 1️⃣ Eliminar las computadoras primero
        cursor.execute("DELETE FROM Computadoras WHERE id_salon = %s", (sala_id,))

        # 2️⃣ Eliminar periféricos asociados
        for comp in computadoras:
            _, id_mouse, id_teclado, id_pantalla = comp
            if id_mouse:
                cursor.execute("DELETE FROM Mouse WHERE id_mouse = %s", (id_mouse,))
            if id_teclado:
                cursor.execute("DELETE FROM Teclados WHERE id_teclado = %s", (id_teclado,))
            if id_pantalla:
                cursor.execute("DELETE FROM Pantallas WHERE id_pantalla = %s", (id_pantalla,))

        # 3️⃣ Finalmente eliminar la sala
        cursor.execute("DELETE FROM Salones WHERE id_salon = %s", (sala_id,))

        conn.commit()
        flash("✅ Sala y todos sus equipos y periféricos eliminados correctamente.")
        print(f"Sala {sala_id} eliminada con todos los equipos y periféricos.")
        return redirect(url_for('gestionar_salas'))

    except Exception as e:
        if conn:
            conn.rollback()
        print("Error al eliminar sala:", e)
        flash("❌ Error al eliminar la sala. Verifica que no haya restricciones en la base de datos.")
        return redirect(url_for('gestionar_salas'))

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

#--------------------------- USUARIOS ----------------------------------


@app.route('/Gestionar_Usuarios', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'moderador')
def gestionar_usuarios():


    user = get_current_user()
    user_name = user['name'].capitalize()
    user_role = user['role']
    user_profile_pic = user['foto_perfil']
   
    filtro_columna = request.args.get('filtro_columna', 'id')
    orden = request.args.get('orden', 'ASC')
    search = request.args.get('search', '').strip()  # nuevo parámetro de búsqueda
    usuarios = obtener_todos_usuarios(filtro_columna=filtro_columna, orden=orden, search=search)

    return render_template('Gestionar_Usuarios.html',
        user_name=user_name,
        user_role=user_role,
        user_profile_pic=user_profile_pic,
        usuarios=usuarios,
        filtro_columna=filtro_columna,
        orden=orden,
        search=search
    )

@app.route('/actualizar_usuario', methods=['POST'])
@login_required
@admin_required
def actualizar_usuario():
    user_id = request.form.get('user_id')
    nuevo_rol = request.form.get('rol')
    nuevo_estado = request.form.get('estado')
    admin_password = request.form.get('admin_password')


    if not user_id or not user_id.isdigit():
        flash("❌ Primero debes seleccionar un usuario de la tabla.")
        return redirect(url_for('gestionar_usuarios'))
    if not admin_password:
        flash("❌ Debes ingresar tu contraseña para cambiar el rol.")
        return redirect(url_for('gestionar_usuarios'))

    # Verificar contraseña del admin
    admin = get_current_user()
    if not bcrypt.checkpw(admin_password.encode('utf-8'), obtener_usuario_por_email(admin['email'])[5].encode()):
        flash("❌ Contraseña incorrecta.")
        return redirect(url_for('gestionar_usuarios'))
    if int(user_id) == session['user_id']:
        flash("❌ No puedes cambiar tu propia cuenta.")
        return redirect(url_for('gestionar_usuarios'))

    # Actualizar rol y estado en la base de datos
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET rol=%s, estado=%s WHERE id=%s", (nuevo_rol, nuevo_estado, user_id))
    conn.commit()
    cursor.close()
    conn.close()

    flash("✅ Usuario actualizado correctamente.")
    return redirect(url_for('gestionar_usuarios'))



#--------------------------- COMPUTADORAS ----------------------------------

@app.route('/Computadoras', methods=['GET', 'POST'])
@login_required
@admin_required
def computadoras():
    user = get_current_user()
    user_name=user['name'].capitalize()
    user_role=user['role']
    user_profile_pic=user['foto_perfil']

    salones = obtener_id_y_nombre_salones()



    if request.method == 'POST':
        mouse_marca = request.form.get('mouse_marca')
        mouse_tipo = request.form.get('mouse_tipo')
        mouse_estado = request.form.get('mouse_estado')

        # ================== TECLADO ==================
        teclado_marca = request.form.get('teclado_marca')
        teclado_tipo = request.form.get('teclado_tipo')
        teclado_estado = request.form.get('teclado_estado')

        # ================== PANTALLA ==================
        pantalla_marca = request.form.get('pantalla_marca')
        pantalla_estado = request.form.get('pantalla_estado')

        # ================== COMPUTADORA ==================
        matricula = request.form.get('matricula')
        marca = request.form.get('marca')
        sistema_operativo = request.form.get('sistema_operativo')
        estado_computadora = request.form.get('estado_computadora')
        id_salon = request.form.get('id_salon')
        

        #print(f"id_salon: {id_salon}")
        # Validaciones básicas
        if not matricula or len(matricula) > 50:
            flash("❌ Matrícula inválida.")
            return render_template('Computadoras.html', user_name=user_name, user_role=user_role, user_profile_pic=user_profile_pic)
        
        if existe_matricula(matricula):
            flash(f"❌ La matrícula '{matricula}' ya está registrada.")
            return render_template('Computadoras.html', user_name=user_name, user_role=user_role, user_profile_pic=user_profile_pic)


        if not marca or len(marca) > 100:
            flash("❌ Marca inválida.")
            return render_template('Computadoras.html', user_name=user_name, user_role=user_role, user_profile_pic=user_profile_pic)

        if not sistema_operativo or len(sistema_operativo) > 100:
            flash("❌ Sistema operativo inválido.")
            return render_template('Computadoras.html', user_name=user_name, user_role=user_role, user_profile_pic=user_profile_pic)

        if not estado_computadora or len(estado_computadora) > 50:
            flash("❌ Estado de la computadora inválido.")
            return render_template('Computadoras.html', user_name=user_name, user_role=user_role, user_profile_pic=user_profile_pic)
        if not id_salon or not id_salon.isdigit():
            flash("❌ Salón inválido.")
            return render_template('Computadoras.html', user_name=user_name, user_role=user_role, user_profile_pic=user_profile_pic)
        id_salon = int(id_salon)
        # Insertar periféricos y obtener sus IDs


        id_mouse = insertar_mouse(mouse_marca, mouse_tipo, mouse_estado)
        id_teclado = insertar_teclado(teclado_marca, teclado_tipo, teclado_estado)
        id_pantalla = insertar_pantalla(pantalla_marca, pantalla_estado)
        insertar_computadora(matricula, marca, sistema_operativo, estado_computadora,
                id_pantalla=id_pantalla, id_teclado=id_teclado,
                id_mouse=id_mouse, id_salon=id_salon)
        Cantidad_equipos(id_salon)
        flash("✅ Computadora agregada exitosamente.")
    return render_template('Computadoras.html',user_name=user_name,user_role=user_role,user_profile_pic=user_profile_pic,salones=salones)


@app.route('/Gestionar_Computadoras', methods=['GET', 'POST'])
@login_required
@admin_required
def gestionar_computadoras():
    user = get_current_user()
    user_name=user['name'].capitalize()
    user_role=user['role']
    user_profile_pic=user['foto_perfil']


    filtro_columna = request.args.get('filtro_columna', 'id_computadora')
    orden = request.args.get('orden', 'ASC')
    search = request.args.get('search', '').strip()  # nuevo parámetro de búsqueda
    computadoras = obtener_todas_computadoras(filtro_columna=filtro_columna, orden=orden, search=search)

    #for compu in computadoras:
        #print(f"Computadora: {compu}")

    return render_template(
    'Gestionar_Computadoras.html',
    user_name=user_name,
    user_role=user_role,
    user_profile_pic=user_profile_pic,
    computadoras=computadoras,
    filtro_columna=filtro_columna,
    orden=orden,
    search=search
)

@app.route('/actualizar_computadora', methods=['POST'])
@login_required
@admin_required
def actualizar_computadora():  
    # Datos del formulario
    id_computadora = request.form.get('id_computadora')
    sistema_operativo = request.form.get('sistema_operativo')
    estado_pc = request.form.get('estado_pc')
    estado_pantalla = request.form.get('estado_pantalla')
    estado_teclado = request.form.get('estado_teclado')
    estado_mouse = request.form.get('estado_mouse')
    admin_password = request.form.get('admin_password')
    
    if not id_computadora or not id_computadora.isdigit():
        flash("❌ Primero debes seleccionar una computadora de la tabla.")
        return redirect(url_for('gestionar_computadoras'))
    id_computadora = int(id_computadora)
    # Validar contraseña admin
    if not admin_password:
        flash("❌ Debes ingresar tu contraseña para actualizar la computadora.")
        return redirect(url_for('gestionar_computadoras'))

    admin = get_current_user()
    if not bcrypt.checkpw(admin_password.encode('utf-8'), obtener_usuario_por_email(admin['email'])[5].encode()):
        flash("❌ Contraseña incorrecta.")
        return redirect(url_for('gestionar_computadoras'))

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Actualizar la computadora
        cursor.execute("""
            UPDATE Computadoras
            SET sistema_operativo = %s,
                estado = %s,
                updated_at = NOW()
            WHERE id_computadora = %s
        """, (sistema_operativo, estado_pc, id_computadora))

        # Obtener los IDs de los periféricos asociados
        cursor.execute("SELECT id_pantalla, id_teclado, id_mouse FROM Computadoras WHERE id_computadora = %s", (id_computadora,))
        perif_ids = cursor.fetchone()
        id_pantalla, id_teclado, id_mouse = perif_ids

        # Actualizar periféricos si se reciben estados nuevos
        if id_pantalla and estado_pantalla:
            cursor.execute("UPDATE Pantallas SET estado = %s, updated_at = NOW() WHERE id_pantalla = %s", (estado_pantalla, id_pantalla))
        if id_teclado and estado_teclado:
            cursor.execute("UPDATE Teclados SET estado = %s, updated_at = NOW() WHERE id_teclado = %s", (estado_teclado, id_teclado))
        if id_mouse and estado_mouse:
            cursor.execute("UPDATE Mouse SET estado = %s, updated_at = NOW() WHERE id_mouse = %s", (estado_mouse, id_mouse))

        conn.commit()
        flash("✅ Computadora y periféricos actualizados correctamente.")

    except Exception as e:
        if conn:
            conn.rollback()
        print("Error al actualizar computadora:", e)
        flash("❌ Error al actualizar la computadora o periféricos.")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return redirect(url_for('gestionar_computadoras'))


@app.route('/eliminar_computadora', methods=['POST'])
@login_required
@admin_required
def eliminar_computadora():
    try:
        computadora_id = int(request.form.get('id_computadora'))
        id_salon = int(request.form.get('id_salon'))
    except (TypeError, ValueError):
        flash("❌ ID de computadora inválido.")
        return redirect(url_for('gestionar_computadoras'))

    admin_password = request.form.get('admin_password')
    if not admin_password:
        flash("❌ Debes ingresar tu contraseña para eliminar la computadora.")
        return redirect(url_for('gestionar_computadoras'))

    admin = get_current_user()
    usuario = obtener_usuario_por_email(admin['email'])
    if not usuario or not bcrypt.checkpw(admin_password.encode('utf-8'), usuario[5].encode()):
        flash("❌ Contraseña de administrador incorrecta.")
        return redirect(url_for('gestionar_computadoras'))

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Obtener IDs de los periféricos asociados
        cursor.execute("""
            SELECT id_pantalla, id_teclado, id_mouse
            FROM Computadoras
            WHERE id_computadora = %s
        """, (computadora_id,))
        perif_ids = cursor.fetchone()
        if not perif_ids:
            flash("❌ La computadora no existe.")
            return redirect(url_for('gestionar_computadoras'))

        id_pantalla, id_teclado, id_mouse = perif_ids
        # Eliminar la computadora
        cursor.execute("DELETE FROM Computadoras WHERE id_computadora = %s", (computadora_id,))
        # Eliminar periféricos si existen
        if id_pantalla:
            cursor.execute("DELETE FROM Pantallas WHERE id_pantalla = %s", (id_pantalla,))
        if id_teclado:
            cursor.execute("DELETE FROM Teclados WHERE id_teclado = %s", (id_teclado,))
        if id_mouse:
            cursor.execute("DELETE FROM Mouse WHERE id_mouse = %s", (id_mouse,))

        
        # Actualizar contador de computadoras en el salón
        if id_salon:
            cursor.execute("""
                UPDATE Salones
                SET cantidad_equipos = CASE
                    WHEN cantidad_equipos - 1 <= 0 THEN NULL
                    ELSE cantidad_equipos - 1
                END
                WHERE id_salon = %s
            """, (id_salon,))

        conn.commit()
        flash("✅ Computadora y periféricos eliminados correctamente.")
        print(f"Computadora {computadora_id} eliminada exitosamente.")
        return redirect(url_for('gestionar_computadoras'))

    except Exception as e:
        if conn:
            conn.rollback()
        print("Error al eliminar computadora:", e)
        flash("❌ Error al eliminar la computadora o sus periféricos.")
        return redirect(url_for('gestionar_computadoras'))

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


#--------------------------- PERIFERICOS ----------------------------------

@app.route('/Gestionar_perifericos', methods=['GET', 'POST'])
@login_required
@admin_required
def gestionar_perifericos():
    user = get_current_user()
    user_name=user['name'].capitalize()
    user_role=user['role']
    user_profile_pic=user['foto_perfil']


    filtro_columna = request.args.get('filtro_columna', 'id_computadora')
    orden = request.args.get('orden', 'ASC')
    search = request.args.get('search', '').strip()  # nuevo parámetro de búsqueda
    computadoras = obtener_todas_computadoras(filtro_columna=filtro_columna, orden=orden, search=search)


    return render_template(
    'Gestionar_Perifericos.html',
    user_name=user_name,
    user_role=user_role,
    user_profile_pic=user_profile_pic,
    computadoras=computadoras,
    filtro_columna=filtro_columna,
    orden=orden,
    search=search
)




@app.route('/Actualizar_Pantalla', methods=['GET', 'POST'])
@login_required
@admin_required
def actualizar_pantalla():
    if request.method == 'POST':
        id_computadora = request.form.get('id_computadora')
        id_salon = request.form.get('id_salon')
        id_pantalla = request.form.get('pantalla_id')
        marca_pantalla = request.form.get('marca_pantalla')
        estado_pantalla = request.form.get('estado_pantalla')
        foto_pantalla = request.files.get('foto_pantalla')
        admin_password = request.form.get('admin_password')


        if not id_computadora or not id_computadora.isdigit():
            flash("❌ Primero debes seleccionar una Computadora de la tabla.")
            return redirect(url_for('gestionar_perifericos'))
        id_computadora = int(id_computadora)
        
        if not id_pantalla or not id_pantalla.isdigit():
            flash("❌ Primero debes seleccionar una Computadora de la tabla.")
            return redirect(url_for('gestionar_perifericos'))
        id_pantalla=int(id_pantalla)

        if not admin_password:
            flash("❌ Debes ingresar tu contraseña para actualizar la pantalla.")
            return redirect(url_for('gestionar_perifericos'))

        # Verificar contraseña admin
        admin = get_current_user()
        if not bcrypt.checkpw(admin_password.encode('utf-8'), obtener_usuario_por_email(admin['email'])[5].encode()):
            flash("❌ Contraseña incorrecta.")
            return redirect(url_for('gestionar_perifericos'))
        
        a,foto_filename = procesar_foto(foto_pantalla,app.config['PANTALLAS_FOLDER'],'pantallas',id_pantalla)
        # Actualizar base de datos
        actualizar_pantalla_db(id_pantalla,marca_pantalla,estado_pantalla,foto_filename)

        flash("✅ Pantalla actualizada correctamente.")
    return redirect(url_for('gestionar_perifericos'))

@app.route('/Actualizar_Teclado', methods=['GET', 'POST'])
@login_required
@admin_required
def actualizar_teclado():
    
    if request.method == 'POST':
        id_computadora = request.form.get('id_computadora')
        id_salon = request.form.get('id_salon')

        id_teclado=request.form.get('teclado_id')
        marca_teclado = request.form.get('marca_teclado')
        tipo_teclado = request.form.get('tipo_teclado')
        estado_teclado = request.form.get('estado_teclado')
        foto_teclado = request.files.get('foto_teclado')
        admin_password = request.form.get('admin_password')

        print(id_computadora,id_salon,id_teclado,marca_teclado,tipo_teclado,estado_teclado,foto_teclado,admin_password)

        if not id_computadora or not id_computadora.isdigit():
            flash("❌ Debes seleccionar una computadora válida.")
            return redirect(url_for('gestionar_perifericos'))

        if not id_teclado or not id_teclado.isdigit():
            flash("❌ Debes seleccionar un teclado válido.")
            return redirect(url_for('gestionar_perifericos'))
        
        id_teclado = int(id_teclado)


        if not admin_password:
            flash("❌ Debes ingresar tu contraseña para actualizar El Teclado.")
            return redirect(url_for('gestionar_perifericos'))

        # Verificar contraseña admin
        admin = get_current_user()
        if not bcrypt.checkpw(admin_password.encode('utf-8'), obtener_usuario_por_email(admin['email'])[5].encode()):
            flash("❌ Contraseña incorrecta.")
            return redirect(url_for('gestionar_perifericos'))
        a,foto_filename = procesar_foto(foto_teclado,app.config['TECLADOS_FOLDER'],'teclados',id_teclado)
        actualizar_teclado_db(id_teclado,marca_teclado,tipo_teclado,estado_teclado,foto_filename)
        flash("✅ Teclado actualizado correctamente.")
    return redirect(url_for('gestionar_perifericos'))

@app.route('/Actualizar_Mouse', methods=['GET', 'POST'])
@login_required
@admin_required
def actualizar_mouse():
    if request.method == 'POST':
        id_computadora = request.form.get('id_computadora')
        id_salon = request.form.get('id_salon')

        id_mouse=request.form.get('mouse_id')
        marca_mouse = request.form.get('marca_mouse')
        tipo_mouse = request.form.get('tipo_mouse')
        estado_mouse = request.form.get('estado_mouse')
        foto_mouse = request.files.get('foto_mouse')
        admin_password = request.form.get('admin_password')

        if not id_computadora or not id_computadora.isdigit():
            flash("❌ Debes seleccionar una computadora válida.")
            return redirect(url_for('gestionar_perifericos'))
        if not id_mouse or not id_mouse.isdigit():
            flash("❌ Debes seleccionar una computadora válida.")
            return redirect(url_for('gestionar_perifericos'))
        id_mouse=int(id_mouse)
        
        if not admin_password:
            flash("❌ Debes ingresar tu contraseña para actualizar el mouse.")
            return redirect(url_for('gestionar_perifericos'))

        # Verificar contraseña admin
        admin = get_current_user()
        if not bcrypt.checkpw(admin_password.encode('utf-8'), obtener_usuario_por_email(admin['email'])[5].encode()):
            flash("❌ Contraseña incorrecta.")
            return redirect(url_for('gestionar_perifericos'))
        
        a,foto_filename = procesar_foto(foto_mouse,app.config['MOUSE_FOLDER'],'mouse',id_mouse)
        actualizar_mouse_db(id_mouse,marca_mouse,tipo_mouse,estado_mouse,foto_filename)
        flash("✅ Mouse actualizado correctamente.")
    return redirect(url_for('gestionar_perifericos'))

#--------------------------- PERMISOS  ----------------------------------
@app.route('/Permisos_Usuarios', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'moderador')
def permisos_usuarios():
    user = get_current_user()
    user_name = user['name'].capitalize()
    user_role = user['role']
    user_profile_pic = user['foto_perfil']

    filtro_columna_usuarios = request.args.get('filtro_columna_usuarios', 'id')
    orden_usuarios = request.args.get('orden_usuarios', 'ASC')
    search_usuarios = request.args.get('search_usuarios', '')
    usuarios = obtener_usuarios_basico(filtro_columna_usuarios, orden_usuarios, search_usuarios)

    filtro_columna_salones = request.args.get('filtro_columna_salones', 'id_salon')
    orden_salones = request.args.get('orden_salones', 'ASC')
    search_salones = request.args.get('search_salones', '')
    salones = obtener_salon_basico(filtro_columna_salones, orden_salones, search_salones)

    if request.method == 'POST':
        id_usuario = request.form.get('id_usuario')
        id_salon = request.form.get('id_salon')

        # Validaciones de presencia
        if not id_usuario and not id_salon:
            flash("❌ Debes seleccionar usuario y salón")
            return redirect(url_for('permisos_usuarios'))
        if not id_usuario:
            flash("❌ Debes seleccionar un usuario")
            return redirect(url_for('permisos_usuarios'))
        if not id_salon:
            flash("❌ Debes seleccionar un salón")
            return redirect(url_for('permisos_usuarios'))

        # Validar que los IDs sean números
        if not id_usuario.isdigit() or not id_salon.isdigit():
            flash("❌ IDs inválidos")
            return redirect(url_for('permisos_usuarios'))

        # Convertir a int
        id_usuario = int(id_usuario)
        id_salon = int(id_salon)

        # Validar que existan realmente en la DB
        usuario_valido = obtener_usuario_por_id(id_usuario)
        salon_valido = obtener_salon_por_id(id_salon)


        if not usuario_valido:
            flash("❌ Usuario no encontrado")
            return redirect(url_for('permisos_usuarios'))
        if not salon_valido:
            flash("❌ Salón no encontrado")
            return redirect(url_for('permisos_usuarios'))

        # Prevenir accesos duplicados
        if not permiso_existente(id_usuario, id_salon):
            insertar_acceso_salon(id_usuario, id_salon, user['id'])
            flash("✅ Acceso asignado correctamente")
        else:
            flash("⚠️ El usuario ya tiene acceso a ese salón")

        return redirect(url_for('permisos_usuarios'))

    return render_template('Permisos_Usuarios.html',
        user_name=user_name,
        user_role=user_role,
        user_profile_pic=user_profile_pic,
        usuarios=usuarios,
        salones=salones)


@app.route('/Gestionar_Permisos', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'moderador')
def gestionar_permisos():
    user = get_current_user()
    user_name = user['name'].capitalize()
    user_role = user['role']
    user_profile_pic = user['foto_perfil']

    # === OBTENER PARAMETROS DEL FILTRO ===
    filtro_columna = request.args.get('filtro_columna', 'id_permiso')
    orden = request.args.get('orden', 'ASC')
    search = request.args.get('search', '').strip()

    # === OBTENER PERMISOS FILTRADOS ===
    Permisos = obtener_permisos(filtro_columna, orden, search)

    return render_template(
        'Gestionar_Permisos.html',
        user_name=user_name,
        user_role=user_role,
        user_profile_pic=user_profile_pic,
        Permisos=Permisos,
        filtro_columna=filtro_columna,
        orden=orden,
        search=search
    )


@app.route('/Eliminar_Permisos', methods=['POST'])
@login_required
@role_required('admin', 'moderador')
def Eliminar_permiso():
    #gestionar_permisos
    try:
        permiso_id = int(request.form.get('permiso_id'))
    except (TypeError, ValueError):
        flash("❌ ID de Permiso inválido.")
        return redirect(url_for('gestionar_permisos'))

    admin_password = request.form.get('admin_password').strip()
    
    if not admin_password:
        flash("❌ Debes ingresar tu contraseña para eliminar la sala.")
        return redirect(url_for('gestionar_permisos'))

    # Verificar contraseña admin
    admin = get_current_user()
    if not bcrypt.checkpw(admin_password.encode('utf-8'), obtener_usuario_por_email(admin['email'])[5].encode()):
        flash("❌ Contraseña incorrecta.")
        return redirect(url_for('gestionar_permisos'))
    eliminar_permiso(permiso_id)
    flash("✅ Permiso eliminado correctamente")
    

    return redirect(url_for('gestionar_permisos'))

#--------------------------- REPORTES  ----------------------------------

@app.route('/reports', methods=['GET', 'POST'])
@login_required
def Reportes():
    user = get_current_user()
    user_name=user['name'].capitalize()
    user_role=user['role']
    user_profile_pic=user['foto_perfil']
    salones = obtener_id_y_nombre_salones()

    return render_template('Reportes.html',user_name=user_name,user_role=user_role,user_profile_pic=user_profile_pic,salones=salones)
@app.route('/obtener_computadoras/<int:id_salon>')
@login_required
def obtener_computadoras(id_salon):
    computadoras = obtener_computadora_por_salon(id_salon)
    return jsonify(computadoras)


@app.route('/guardar_reporte',methods=['POST'])
@login_required
def guardar_reporte():
    user = get_current_user()
    user_id = int(user['id'])

    id_salon = request.form.get('id_salon')
    id_computadora = request.form.get('computadora')

    foto_pantalla = request.files.get('foto_pantalla')
    foto_teclado = request.files.get('foto_teclado')
    foto_mouse = request.files.get('foto_mouse')

    comentarios = request.form.get('comentarios')

    if not id_salon or not id_salon.isdigit():
        flash("❌ Salón inválido.")
        return redirect(url_for('Reportes'))
    if not id_computadora or not id_computadora.isdigit():
        flash("❌ Computadora inválida.")
        return redirect(url_for('Reportes'))
    
    id_salon = int(id_salon)
    id_computadora = int(id_computadora)

    
    perifericos=obtener_ids_perifericos(id_computadora)
    id_pantalla=int(perifericos.get('pantalla'))
    id_teclado=int(perifericos.get('teclado'))
    id_mouse=int(perifericos.get('mouse'))


    score_pantalla, estado_pantalla, score_teclado, estado_teclado, score_mouse, estado_mouse=Realizar_reporte(foto_pantalla,id_pantalla,foto_teclado,id_teclado,foto_mouse,id_mouse )

    insertar_reporte(user_id,id_salon,id_computadora,id_pantalla,id_teclado,id_mouse, estado_pantalla, score_pantalla,estado_teclado, score_teclado,estado_mouse, score_mouse,comentarios)


    flash("✅ Reporte creado correctamente")
    return redirect(url_for('Reportes'))


def map_estado(label):
    return "operativa" if label == "bueno" else "dañada"


def Realizar_reporte(foto_pantalla,id_pantalla,
                    foto_teclado,id_teclado,
                    foto_mouse,id_mouse
                    ):
    
    pantalla_path,foto_filename_pantallas = procesar_foto(foto_pantalla,app.config['PANTALLAS_FOLDER'],'pantallas',id_pantalla)
    teclado_path,foto_filename_teclados = procesar_foto(foto_teclado,app.config['TECLADOS_FOLDER'],'teclados',id_teclado)
    mouse_path,foto_filename_mouse = procesar_foto(foto_mouse,app.config['MOUSE_FOLDER'],'mouse',id_mouse)

    if not foto_pantalla or not allowed_file(foto_pantalla.filename):
        flash("❌ Debes subir una foto válida de la pantalla.")
        return redirect(url_for('Reportes'))
    if not foto_teclado or not allowed_file(foto_teclado.filename):
        flash("❌ Debes subir una foto válida del teclado.")
        return redirect(url_for('Reportes'))
    if not foto_mouse or not allowed_file(foto_mouse.filename):
        flash("❌ Debes subir una foto válida del mouse.")
        return redirect(url_for('Reportes'))



    print("Archivo pantalla:", pantalla_path, os.path.exists(pantalla_path))
    print("Archivo teclado:", teclado_path, os.path.exists(teclado_path))
    print("Archivo mouse:", mouse_path, os.path.exists(mouse_path))

    resultados=clasificar_dispositivos(pantalla_path,teclado_path,mouse_path)

    print(resultados)


    score_pantalla = resultados['pantalla']['score_good']
    estado_pantalla = map_estado(resultados['pantalla']['label'])

    score_teclado = resultados['teclado']['score_good'] 
    estado_teclado = map_estado(resultados['teclado']['label'] )
    
    score_mouse = resultados['mouse']['score_good']
    estado_mouse = map_estado(resultados['mouse']['label'] )





    
    actualizar_estado_foto_pantalla(id_pantalla, estado_pantalla, foto_filename_pantallas)
    actualizar_estado_foto_teclado(id_teclado, estado_teclado, foto_filename_teclados)
    actualizar_estado_foto_mouse(id_mouse, estado_mouse, foto_filename_mouse)
    return (score_pantalla, estado_pantalla,
        score_teclado, estado_teclado,
        score_mouse, estado_mouse)


def procesar_foto(file, folder, prefijo, id_item):
    if file and allowed_file(file.filename):
        os.makedirs(folder, exist_ok=True)

        # Eliminar fotos anteriores
        pattern = os.path.join(folder, f"{prefijo}_{id_item}.*")
        for old_file in glob.glob(pattern):
            try:
                os.remove(old_file)
            except OSError:
                pass

        # Guardar la nueva foto
        extension = file.filename.rsplit('.', 1)[1].lower()
        filename = secure_filename(f"{prefijo}_{id_item}.{extension}")
        filepath = os.path.join(folder, filename)
        print(f"Guardando {filepath}...")
        file.save(filepath)
        return filepath, f"uploads/{prefijo}/{filename}"
    print("Archivo no válido o None:", file)
    return None, None






if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)