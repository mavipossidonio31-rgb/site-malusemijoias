/* ==========================================================================
   INTERATIVIDADE DA PÁGINA DE CONTATO - MALU SEMIJOIAS
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
    const inputTelefone = document.getElementById("telefone");
    const formContato = document.querySelector(".box-formulario-contato form");

    // 1. MÁSCARA AUTOMÁTICA DE TELEFONE EM TEMPO REAL ((XX) XXXXX-XXXX)
    if (inputTelefone) {
        inputTelefone.addEventListener("input", (e) => {
            let valor = e.target.value.replace(/\D/g, ""); // Remove caracteres não numéricos
            if (valor.length > 11) valor = valor.slice(0, 11);

            if (valor.length > 6) {
                valor = `(${valor.slice(0, 2)}) ${valor.slice(2, 7)}-${valor.slice(7)}`;
            } else if (valor.length > 2) {
                valor = `(${valor.slice(0, 2)}) ${valor.slice(2)}`;
            } else if (valor.length > 0) {
                valor = `(${valor}`;
            }

            e.target.value = valor;
        });
    }

    // 2. ENVIO DE FORMULÁRIO COM FEEDBACK DE CARREGAMENTO E ANIMAÇÃO
    if (formContato) {
        formContato.addEventListener("submit", (e) => {
            e.preventDefault();

            const btnEnviar = formContato.querySelector(".btn-enviar-mensagem");
            const nomeCliente = document.getElementById("nome").value;
            const textoOriginal = btnEnviar.innerHTML;

            // Altera botão para estado de carregamento
            btnEnviar.disabled = true;
            btnEnviar.innerHTML = "⌛ Enviando...";

            setTimeout(() => {
                // Altera botão para estado de sucesso
                btnEnviar.style.background = "linear-gradient(135deg, #27ae60 0%, #219653 100%)";
                btnEnviar.style.color = "#FFFFFF";
                btnEnviar.innerHTML = "✓ Mensagem Enviada!";

                alert(`✨ Obrigada pelo contacto, ${nomeCliente}!\nSua mensagem foi recebida e a nossa equipa responderá em breve.`);

                // Reseta o formulário
                formContato.reset();

                // Restaura o botão após 3 segundos
                setTimeout(() => {
                    btnEnviar.disabled = false;
                    btnEnviar.style.background = "";
                    btnEnviar.style.color = "";
                    btnEnviar.innerHTML = textoOriginal;
                }, 3000);
            }, 1200);
        });
    }
});