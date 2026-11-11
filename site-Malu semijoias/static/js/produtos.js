document.addEventListener("DOMContentLoaded", () => {
    // --- GERENCIADOR DE NAVEGAÇÃO ENTRE ABAS ---
    const tabButtons = document.querySelectorAll(".tab-cat-btn");
    const tabContents = document.querySelectorAll(".tab-cat-content");

    tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            // Remove estado ativo de todos os botões e conteúdos
            tabButtons.forEach(b => b.classList.remove("active"));
            tabContents.forEach(c => c.classList.remove("active"));

            // Ativa a aba selecionada
            btn.classList.add("active");
            const categoryId = btn.getAttribute("data-category");
            const activeContent = document.getElementById(categoryId);

            if (activeContent) {
                activeContent.classList.add("active");
            }
        });
    });
});

// --- FUNÇÃO PARA ADICIONAR PRODUTOS AO CARRINHO (LOCALSTORAGE) ---
function adicionarAoCarrinho(id, nome, preco, imagem_url) {
    let carrinho = JSON.parse(localStorage.getItem("carrinho_malu")) || [];

    const itemExistente = carrinho.find(item => item.id === id);

    if (itemExistente) {
        itemExistente.quantidade += 1;
    } else {
        carrinho.push({
            id: id,
            nome: nome,
            preco: preco,
            imagem_url: imagem_url,
            quantidade: 1
        });
    }

    localStorage.setItem("carrinho_malu", JSON.stringify(carrinho));

    // Notificação sutil e rápida
    alert(`✨ "${nome}" foi adicionado ao seu carrinho com sucesso!`);
}