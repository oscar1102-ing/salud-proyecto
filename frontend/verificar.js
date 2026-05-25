// Leer parámetros de la URL
const params     = new URLSearchParams(window.location.search);
const usuarioId  = params.get("id");
const tipo       = params.get("tipo"); // 'registro' o 'login'

// Configurar textos según el tipo
document.addEventListener("DOMContentLoaded", () => {
    if (!usuarioId || !tipo) {
        window.location.href = "login.html";
        return;
    }

    if (tipo === "registro") {
        document.getElementById("mfa-titulo").textContent = "Verifica tu cuenta";
        document.getElementById("mfa-subtitulo").textContent =
            "Te enviamos un código de 6 dígitos a tu correo para activar tu cuenta.";
    } else {
        document.getElementById("mfa-titulo").textContent = "Código de acceso";
        document.getElementById("mfa-subtitulo").textContent =
            "Te enviamos un código de 6 dígitos a tu correo para confirmar tu identidad.";
    }

    document.getElementById("d1").focus();
});

// Avanzar al siguiente input automáticamente
function avanzar(actual, siguienteId) {
    actual.value = actual.value.replace(/[^0-9]/g, "");
    if (actual.value.length === 1 && siguienteId) {
        document.getElementById(siguienteId).focus();
    }
}

// Retroceder con backspace
function retroceder(event, actual, anteriorId) {
    if (event.key === "Backspace" && actual.value === "" && anteriorId) {
        document.getElementById(anteriorId).focus();
    }
}

// Verificar automáticamente al llenar el último dígito
function verificarAuto() {
    document.getElementById("d6").value = document.getElementById("d6").value.replace(/[^0-9]/g, "");
    const codigo = obtenerCodigo();
    if (codigo.length === 6) {
        setTimeout(() => verificarCodigo(), 200);
    }
}

function obtenerCodigo() {
    return ["d1","d2","d3","d4","d5","d6"]
        .map(id => document.getElementById(id).value)
        .join("");
}

function limpiarInputs() {
    ["d1","d2","d3","d4","d5","d6"].forEach(id => {
        document.getElementById(id).value = "";
        document.getElementById(id).classList.remove("correcto", "error");
    });
    document.getElementById("d1").focus();
}

function marcarError() {
    ["d1","d2","d3","d4","d5","d6"].forEach(id => {
        document.getElementById(id).classList.add("error");
    });
    setTimeout(limpiarInputs, 600);
}

function marcarExito() {
    ["d1","d2","d3","d4","d5","d6"].forEach(id => {
        document.getElementById(id).classList.add("correcto");
    });
}

async function verificarCodigo() {
    const codigo = obtenerCodigo();
    if (codigo.length < 6) {
        document.getElementById("mfa-error").textContent = "Ingresa los 6 dígitos";
        return;
    }

    document.getElementById("mfa-error").textContent = "";
    document.getElementById("mfa-exito").textContent = "";

    try {
        const res = await fetch(`/api/mfa/verificar/${usuarioId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ codigo, tipo })
        });

        const data = await res.json();

        if (res.ok) {
            marcarExito();
            document.getElementById("mfa-exito").textContent = "✅ Verificado correctamente";

            setTimeout(() => {
                if (tipo === "registro") {
                    window.location.href = "login.html";
                } else {
                    // Para login, el usuario_id ya está guardado en localStorage
                    window.location.href = "perfil.html";
                }
            }, 1000);

        } else {
            marcarError();
            document.getElementById("mfa-error").textContent =
                data.detail || "Código incorrecto";
        }

    } catch (error) {
        console.error(error);
        document.getElementById("mfa-error").textContent = "Error de conexión";
    }
}

// Reenviar código con contador de 60 segundos
async function reenviarCodigo() {
    const btnReenviar  = document.getElementById("btn-reenviar");
    const contador     = document.getElementById("contador-reenvio");

    btnReenviar.disabled = true;
    btnReenviar.style.display = "none";
    contador.style.display = "block";

    try {
        await fetch(`/api/mfa/enviar/${usuarioId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ tipo })
        });
        document.getElementById("mfa-error").textContent = "";
        document.getElementById("mfa-exito").textContent = "Código reenviado a tu correo";
    } catch (e) {
        document.getElementById("mfa-error").textContent = "Error al reenviar";
    }

    // Contador regresivo de 60 segundos
    let segundos = 60;
    const intervalo = setInterval(() => {
        segundos--;
        contador.textContent = `Puedes reenviar en ${segundos}s`;
        if (segundos <= 0) {
            clearInterval(intervalo);
            contador.style.display = "none";
            btnReenviar.style.display = "inline";
            btnReenviar.disabled = false;
            document.getElementById("mfa-exito").textContent = "";
        }
    }, 1000);
}
