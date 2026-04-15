document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("formLogin");

    if (form) {
        form.addEventListener("submit", validarLogin);
    }

    const checkbox = document.getElementById("btn-modal");
    if (checkbox) checkbox.checked = false;
});

function mostrarModal(mensaje, titulo = "Aviso") {
    document.getElementById("modalTitulo").innerText = titulo;
    document.getElementById("modalMensaje").innerText = mensaje;
    document.getElementById("btn-modal").checked = true;
}

function validarEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

async function validarLogin(event) {
    event.preventDefault();

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    // VALIDACIONES
    if (!validarEmail(email)) {
        mostrarModal("Correo electrónico inválido", "Error");
        return;
    }

    if (password.length < 6) {
        mostrarModal("La contraseña debe tener mínimo 6 caracteres", "Error");
        return;
    }

    const boton = event.target.querySelector("button");
    const textoOriginal = boton.textContent;

    boton.textContent = "Ingresando...";
    boton.disabled = true;

    try {
        const respuesta = await fetch("http://127.0.0.1:8001/api/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ email, password })
        });

        const resultado = await respuesta.json();

        if (respuesta.ok) {
            mostrarModal("Ingreso exitoso", "Éxito");

            setTimeout(() => {
                window.location.href = "perfil.html"; // 🔥 CAMBIA A TU DASHBOARD
            }, 1500);

        } else {
            mostrarModal(resultado.detail || "Error al iniciar sesión", "Error");
        }

    } catch (error) {
        console.error(error);
        mostrarModal("Error de conexión con el servidor", "Error");
    } finally {
        boton.textContent = textoOriginal;
        boton.disabled = false;
    }
}