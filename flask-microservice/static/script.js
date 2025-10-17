// /micro02/static/script.js

// --- GESTIÓN DE TOKENS Y PETICIONES ---

// Función "envoltorio" para fetch que maneja la autenticación y el refresh de tokens
async function fetchWithAuth(url, options = {}) {
    let accessToken = localStorage.getItem('access_token');
    
    options.headers = {
        ...options.headers,
        'Authorization': `Bearer ${accessToken}`
    };

    let response = await fetch(url, options);

    if (response.status === 401) { // Token expirado
        console.log("Access token expirado. Intentando refrescar...");
        const refreshed = await refreshToken();
        if (refreshed) {
            // Si el refresh fue exitoso, reintentamos la petición original con el nuevo token
            accessToken = localStorage.getItem('access_token');
            options.headers['Authorization'] = `Bearer ${accessToken}`;
            response = await fetch(url, options);
        } else {
            // Si el refresh falla, deslogueamos
            logout();
            return null;
        }
    }
    return response;
}

// Función para refrescar el access token
async function refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) return false;

    try {
        const response = await fetch('/auth/refresh', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${refreshToken}` }
        });

        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('access_token', data.access_token);
            console.log("Access token refrescado exitosamente.");
            return true;
        } else {
            console.error("Falló el refresh token.");
            return false;
        }
    } catch (error) {
        console.error("Error en refresh token:", error);
        return false;
    }
}

// --- LÓGICA DE LA PÁGINA ---

// Se ejecuta cuando la página del catálogo se carga
document.addEventListener('DOMContentLoaded', () => {
    // Si no hay token, se redirige al login
    if (!localStorage.getItem('access_token')) {
        window.location.href = '/';
        return;
    }

    loadBooks();

    // Evento para el botón de logout
    document.getElementById('logout-btn').addEventListener('click', logout);
});

// Cargar y mostrar los libros en la tabla
async function loadBooks() {
    const response = await fetchWithAuth('/api/books/json');
    if (response && response.ok) {
        const books = await response.json();
        const tableBody = document.getElementById('books-table-body');
        tableBody.innerHTML = ''; // Limpiar la tabla
        books.forEach(book => {
            const row = `
                <tr>
                    <td>${book.isbn}</td>
                    <td>${book.title}</td>
                    <td>${book.year}</td>
                    <td>${book.price}</td>
                    <td>${book.stock}</td>
                    <td class="actions">
                        <button onclick="editBook('${book.isbn}')">Editar</button>
                        <button onclick="deleteBook('${book.isbn}')">Eliminar</button>
                    </td>
                </tr>
            `;
            tableBody.innerHTML += row;
        });
    } else {
        console.error("No se pudieron cargar los libros.");
    }
}

// Función de Logout
async function logout() {
    await fetchWithAuth('/auth/logout', { method: 'POST' });
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/';
}

// Funciones CRUD (placeholders, necesitas implementar la lógica de los modales/formularios)
function editBook(isbn) {
    alert(`Lógica para editar el libro con ISBN: ${isbn}`);
    // Aquí abrirías un modal/formulario para editar los datos y luego harías una petición PUT a /api/books/update/<isbn>
}

async function deleteBook(isbn) {
    if (confirm(`¿Estás seguro de que quieres eliminar el libro con ISBN ${isbn}?`)) {
        const response = await fetchWithAuth(`/api/books/delete/${isbn}`, { method: 'DELETE' });
        if (response && response.ok) {
            alert('Libro eliminado exitosamente.');
            loadBooks(); // Recargar la lista de libros
        } else {
            alert('Error al eliminar el libro.');
        }
    }
}