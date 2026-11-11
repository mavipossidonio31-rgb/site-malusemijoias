document.addEventListener("DOMContentLoaded", () => {
    // --- CONTROLO DAS ABAS ---
    const tabButtons = document.querySelectorAll(".tab-btn");
    const tabContents = document.querySelectorAll(".tab-content");

    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            tabButtons.forEach(b => b.classList.remove("active"));
            tabContents.forEach(c => c.classList.remove("active"));

            btn.classList.add("active");
            const targetTab = btn.getAttribute("data-tab");
            const activeContent = document.getElementById(`tab-${targetTab}`);

            if (activeContent) {
                activeContent.classList.add("active");
            }
        });
    });

    // --- ENVIAR ALTERAÇÃO DE STATUS DO PEDIDO PARA A BASE DE DADOS ---
    const selectsStatus = document.querySelectorAll(".select-status-admin");

    selectsStatus.forEach(select => {
        select.addEventListener("change", (e) => {
            const pedidoId = e.target.getAttribute("data-id");
            const novoStatus = e.target.value;

            fetch("/admin/atualizar_status", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    pedido_id: pedidoId,
                    status: novoStatus
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(`Status do Pedido #${pedidoId} guardado com sucesso na base de dados!`);
                    location.reload(); // Recarrega para atualizar os valores de faturação e badges
                } else {
                    alert("Erro ao guardar na base de dados: " + data.message);
                }
            })
            .catch(error => {
                console.error("Erro na ligação com o servidor:", error);
                alert("Erro ao comunicar com o servidor Flask.");
            });
        });
    });
});