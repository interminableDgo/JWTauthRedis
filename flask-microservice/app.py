# /micro02/app.py

import pymysql
import redis
from datetime import timedelta
from flask import Flask, request, jsonify, Response, render_template
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt, JWTManager

# --- INICIALIZACIÓN Y CONFIGURACIÓN ---
app = Flask(__name__)
bcrypt = Bcrypt(app)

# =================================================================
# ▼▼▼ CONFIGURACIÓN CLAVE PARA LA NUBE ▼▼▼
# =================================================================

app.config["JWT_SECRET_KEY"] = "una-clave-secreta-muy-larga-y-dificil-de-adivinar" 
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=15)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
jwt = JWTManager(app)

DB_CONFIG = {
    'host': 'localhost',
    'user': 'hoonigans',
    'password': 'Hoonigans_Pass_666!', # ¡Tu contraseña fuerte!
    'cursorclass': pymysql.cursors.DictCursor
}

try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    print("Conexión con Redis exitosa.")
except redis.exceptions.ConnectionError as e:
    print(f"Error al conectar con Redis: {e}")
    redis_client = None

# =================================================================
# ▲▲▲ FIN DE LA CONFIGURACIÓN CLAVE ▲▲▲
# =================================================================

# --- GESTIÓN DE TOKENS REVOCADOS (LOGOUT) ---
@jwt.token_in_blocklist_loader
def check_if_token_is_revoked(jwt_header, jwt_payload: dict):
    if not redis_client: return True
    jti = jwt_payload["jti"]
    token_in_redis = redis_client.get(jti)
    return token_in_redis is not None

# --- ENDPOINTS DE PÁGINAS WEB (FRONTEND) ---
@app.route('/')
def serve_login_page():
    return render_template('login.html')

@app.route('/catalogue')
def serve_catalogue_page():
    return render_template('catalogue.html')

# --- ENDPOINTS DE AUTENTICACIÓN ---

@app.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email', f"{username}@example.com")

    if not all([username, password]):
        return jsonify({"msg": "Faltan datos"}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    
    conn = pymysql.connect(db='JWT', **DB_CONFIG)
    try:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)", (username, email, hashed_password))
        conn.commit()
    except pymysql.err.IntegrityError:
        return jsonify({"msg": "El usuario o email ya existe"}), 409
    finally:
        conn.close()
        
    return jsonify({"msg": "Usuario registrado exitosamente"}), 201

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = pymysql.connect(db='JWT', **DB_CONFIG)
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
    finally:
        conn.close()

    if user and bcrypt.check_password_hash(user['password_hash'], password):
        identity = user['id'] 
        access_token = create_access_token(identity=identity)
        refresh_token = create_refresh_token(identity=identity)
        return jsonify(access_token=access_token, refresh_token=refresh_token)

    return jsonify({"msg": "Credenciales incorrectas"}), 401

@app.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify(access_token=access_token)

@app.route('/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    if not redis_client: return jsonify({"msg": "Servicio no disponible"}), 503
    jti = get_jwt()["jti"]
    redis_client.set(jti, "", ex=app.config["JWT_ACCESS_TOKEN_EXPIRES"])
    return jsonify({"msg": "Sesión cerrada exitosamente"})

# --- ENDPOINTS CRUD DE LIBROS (TODOS PROTEGIDOS) ---

@app.route('/api/books', methods=['GET'])
@jwt_required()
def get_all_books_xml():
    conn = pymysql.connect(db='libros', **DB_CONFIG)
    try:
        with conn.cursor() as cursor:
            sql = "SELECT b.isbn, b.title, b.year, b.price, a.author_name, g.genre_name, f.format_name FROM books b JOIN authors a ON b.author_id = a.author_id JOIN genres g ON b.genre_id = g.genre_id JOIN formats f ON b.format_id = f.format_id"
            cursor.execute(sql)
            books = cursor.fetchall()
    finally:
        conn.close()
    
    base_url = request.url_root
    xml_output = f'<?xml-stylesheet type="text/xsl" href="{base_url}static/books.xsl"?>\n<books>\n'
    for book in books:
        xml_output += '  <book>\n'
        for key, value in book.items():
            xml_output += f'    <{key}>{value}</{key}>\n'
        xml_output += '  </book>\n'
    xml_output += '</books>'
    return Response(xml_output, mimetype='application/xml')

@app.route('/api/books/json', methods=['GET'])
@jwt_required()
def get_all_books_json():
    conn = pymysql.connect(db='libros', **DB_CONFIG)
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM books")
            books = cursor.fetchall()
    finally:
        conn.close()
    return jsonify(books)

@app.route('/api/books/<string:isbn>', methods=['GET'])
@jwt_required()
def get_book_by_isbn(isbn):
    conn = pymysql.connect(db='libros', **DB_CONFIG)
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM books WHERE isbn = %s", (isbn,))
            book = cursor.fetchone()
    finally:
        conn.close()
    return jsonify(book) if book else (jsonify({"msg": "Libro no encontrado"}), 404)

@app.route('/api/books/create', methods=['POST'])
@jwt_required()
def create_book():
    data = request.get_json()
    try:
        conn = pymysql.connect(db='libros', **DB_CONFIG)
        with conn.cursor() as cursor:
            sql = "INSERT INTO books (isbn, title, year, price, stock, author_id, genre_id, format_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (data['isbn'], data['title'], data['year'], data['price'], data['stock'], data['author_id'], data['genre_id'], data['format_id']))
        conn.commit()
    except Exception as e:
        return jsonify({"msg": "Error al crear el libro", "error": str(e)}), 500
    finally:
        conn.close()
    return jsonify({"msg": "Libro creado exitosamente"}), 201

@app.route('/api/books/update/<string:isbn>', methods=['PUT'])
@jwt_required()
def update_book(isbn):
    data = request.get_json()
    conn = pymysql.connect(db='libros', **DB_CONFIG)
    try:
        with conn.cursor() as cursor:
            sql = "UPDATE books SET title=%s, year=%s, price=%s, stock=%s, author_id=%s, genre_id=%s, format_id=%s WHERE isbn=%s"
            rows_affected = cursor.execute(sql, (data['title'], data['year'], data['price'], data['stock'], data['author_id'], data['genre_id'], data['format_id'], isbn))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"msg": "Libro actualizado"}) if rows_affected > 0 else (jsonify({"msg": "Libro no encontrado"}), 404)

@app.route('/api/books/delete/<string:isbn>', methods=['DELETE'])
@jwt_required()
def delete_book(isbn):
    conn = pymysql.connect(db='libros', **DB_CONFIG)
    try:
        with conn.cursor() as cursor:
            rows_affected = cursor.execute("DELETE FROM books WHERE isbn = %s", (isbn,))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"msg": "Libro eliminado"}) if rows_affected > 0 else (jsonify({"msg": "Libro no encontrado"}), 404)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)