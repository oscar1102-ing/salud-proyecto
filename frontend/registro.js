document.addEventListener("DOMContentLoaded", () => {

    const checkbox = document.getElementById("btn-modal");
    if (checkbox) checkbox.checked = false;

    const form = document.getElementById("formRegistro");
    if (form) {
        form.addEventListener("submit", validarRegistro);
    }
});

function mostrarModal(mensaje, titulo = "Aviso") {

    const tituloEl = document.getElementById("modalTitulo");
    const mensajeEl = document.getElementById("modalMensaje");
    const checkbox = document.getElementById("btn-modal");

    if (!tituloEl || !mensajeEl || !checkbox) {
        console.error("El modal no está bien definido en el HTML");
        return;
    }

    tituloEl.innerText = titulo;
    mensajeEl.innerText = mensaje;

    checkbox.checked = true; 
}

// Validar email
function validarEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

// Registro
async function validarRegistro(event) {
    event.preventDefault();

    const nombre = document.getElementById("nombre").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const edad = document.getElementById("edad").value;
    const tipoUsuario = document.getElementById("tipoUsuario").value;
    const nivelCarga = document.getElementById("nivelCarga").value;
    const horasTrabajo = document.getElementById("horasTrabajo").value;
    const horasDescanso = document.getElementById("horasDescanso").value;

    // Validaciones
    if (nombre.length < 3) {
        mostrarModal(" El nombre debe tener al menos 3 caracteres", "error");
        return;
    }
    
    if (!/^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/.test(nombre)) {
        mostrarModal("El nombre solo puede contener letras", "Error");
        return;
    }

    if (!validarEmail(email)) {
        mostrarModal(" Correo electrónico inválido", "error");
        return;
    }

    if (password.length < 6) {
        mostrarModal(" La contraseña debe tener mínimo 6 caracteres", "error");
        return;
    }

    if (!tipoUsuario) {
        mostrarModal(" Selecciona un tipo de usuario", "error");
        return;
    }

    if (!nivelCarga) {
        mostrarModal(" Selecciona un nivel de carga", "error");
        return;
    }

    if (horasTrabajo < 0 || horasTrabajo > 24) {
        mostrarModal(" Horas de trabajo deben estar entre 0 y 24", "error");
        return;
    }

    if (horasDescanso < 0 || horasDescanso > 24) {
        mostrarModal(" Horas de descanso deben estar entre 0 y 24", "error");
        return;
    }
    
    if (horasTrabajo === "" || parseInt(horasTrabajo) < 0) {
        mostrarModal("Horas de trabajo no pueden ser negativas", "Error");
        return;
    }
    if (horasDescanso === "" || parseInt(horasDescanso) < 0) {
        mostrarModal("Horas de descanso no pueden ser negativas", "Error");
        return;
    }

    // Botón cargando
    const boton = event.target.querySelector('button[type="submit"]');
    const textoOriginal = boton.textContent;
    boton.textContent = " Registrando...";
    boton.disabled = true;

    const datosRegistro = {
        nombre_completo: nombre,
        email: email,
        password: password,
        edad: edad ? parseInt(edad) : null,
        tipo_usuario: tipoUsuario,
        nivel_carga: nivelCarga,
        horas_trabajo: parseInt(horasTrabajo) || 0,
        horas_descanso: parseInt(horasDescanso) || 0
    };

    try {
        const respuesta = await fetch('/api/registro', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(datosRegistro)
        });

        const resultado = await respuesta.json();

        if (respuesta.ok) {
            mostrarModal("¡Registro exitoso!");
            document.getElementById("formRegistro").reset();

            setTimeout(() => {
                window.location.href = "login.html";
            }, 2000);
        } else {
            mostrarModal(" " + (resultado.detail || "Error al registrarse"), "error");
        }

    } catch (error) {
        console.error(error);
        mostrarModal(" Error de conexión con el servidor", "error");
    } finally {
        boton.textContent = textoOriginal;
        boton.disabled = false;
    }
}

// Inicializar
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("formRegistro");
    if (form) {
        form.addEventListener("submit", validarRegistro);
    }
});
