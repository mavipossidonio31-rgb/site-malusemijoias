let valorFreteCalculado = 0;
let subtotalGlobal = 0;
let pedidoIdPendente = null;

document.addEventListener("DOMContentLoaded", () => {
    renderizarCarrinho();
    carregarPedidosCliente();
});

function alternarAba(aba) {
    document.getElementById("btn-aba-carrinho").classList.toggle("active", aba === "carrinho");
    document.getElementById("btn-aba-status").classList.toggle("active", aba === "status");
    document.getElementById("secao-carrinho").classList.toggle("active", aba === "carrinho");
    document.getElementById("secao-status").classList.toggle("active", aba === "status");
}

function renderizarCarrinho() {
    const carrinho = JSON.parse(localStorage.getItem("carrinho_malu")) || [];
    const container = document.getElementById("container-itens");

    if (carrinho.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 40px 0; color: #5C436E;">
                <p>Seu carrinho está vazio.</p>
                <a href="/produtos" style="color: #C5A059; font-weight: bold;">Explorar peças do catálogo</a>
            </div>
        `;
        atualizarTotais(0);
        return;
    }

    container.innerHTML = "";
    subtotalGlobal = 0;

    carrinho.forEach((item, index) => {
        const itemTotal = item.preco * item.quantidade;
        subtotalGlobal += itemTotal;

        container.innerHTML += `
            <div class="item-carrinho-card">
                <img src="${item.imagem_url}" alt="${item.nome}" class="item-carrinho-foto">
                <div class="item-carrinho-detalhes">
                    <h4>${item.nome}</h4>
                    <span class="item-carrinho-preco">R$ ${item.preco.toFixed(2)}</span>
                    <div class="controles-qtd">
                        <button class="btn-qtd" onclick="alterarQuantidade(${index}, -1)">-</button>
                        <span class="qtd-valor">${item.quantidade}</span>
                        <button class="btn-qtd" onclick="alterarQuantidade(${index}, 1)">+</button>
                    </div>
                </div>
                <button class="btn-remover-item" onclick="removerItem(${index})" title="Remover item">🗑️</button>
            </div>
        `;
    });

    atualizarTotais(subtotalGlobal);
}

function alterarQuantidade(index, alteracao) {
    let carrinho = JSON.parse(localStorage.getItem("carrinho_malu")) || [];
    if (carrinho[index]) {
        carrinho[index].quantidade += alteracao;
        if (carrinho[index].quantidade <= 0) {
            carrinho.splice(index, 1);
        }
        localStorage.setItem("carrinho_malu", JSON.stringify(carrinho));
        renderizarCarrinho();
    }
}

function removerItem(index) {
    let carrinho = JSON.parse(localStorage.getItem("carrinho_malu")) || [];
    carrinho.splice(index, 1);
    localStorage.setItem("carrinho_malu", JSON.stringify(carrinho));
    renderizarCarrinho();
}

function calcularFrete() {
    const cep = document.getElementById("cep-destino").value.trim();
    const info = document.getElementById("resultado-frete");

    if (cep.length < 8) {
        info.style.color = "#b33939";
        info.innerText = "Por favor, digite um CEP válido.";
        return;
    }

    valorFreteCalculado = 15.90;
    info.style.color = "#27ae60";
    info.innerText = `Frete estimado: R$ ${valorFreteCalculado.toFixed(2)} (Entrega em até 3 dias úteis)`;

    renderizarCarrinho();
}

function atualizarTotais(subtotal) {
    document.getElementById("subtotal-valor").innerText = `R$ ${subtotal.toFixed(2)}`;
    document.getElementById("frete-valor").innerText = `R$ ${valorFreteCalculado.toFixed(2)}`;
    const total = subtotal + valorFreteCalculado;
    document.getElementById("total-valor").innerText = `R$ ${total.toFixed(2)}`;
}

// --- FINALIZAR PEDIDO ENVIANDO AO FLASK ---
function finalizarPedido() {
    const carrinho = JSON.parse(localStorage.getItem("carrinho_malu")) || [];
    if (carrinho.length === 0) {
        alert("Adicione peças ao seu carrinho antes de finalizar!");
        return;
    }

    const formaPagamento = document.getElementById("forma-pagamento").value;

    fetch("/finalizar_pedido", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            itens: carrinho,
            forma_pagamento: formaPagamento
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            pedidoIdPendente = data.pedido_id;
            const totalCompra = subtotalGlobal + valorFreteCalculado;

            if (formaPagamento === "Pix") {
                abrirModalPix(totalCompra);
            } else {
                alert(`✨ Pedido #${data.pedido_id} realizado com sucesso!`);
                limparECarregar();
            }
        } else {
            alert(data.message || "Faça login para finalizar a compra.");
        }
    })
    .catch(err => {
        console.error(err);
        alert("Erro ao conectar com o servidor.");
    });
}

// --- LÓGICA DO MODAL PIX ---
function abrirModalPix(valorTotal) {
    document.getElementById("valor-total-modal").innerText = `R$ ${valorTotal.toFixed(2)}`;

    // Gerador automático de QR Code Pix usando a API grátis da qrserver
    const payloadPix = `00020126580014br.gov.bcb.pix0136malusemijoias2026-pix5204000053039865405${valorTotal.toFixed(2)}5802BR5920Malu Semijoias6009SAO PAULO62070503REC6304`;
    const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(payloadPix)}`;

    document.getElementById("img-qrcode-pix").src = qrUrl;
    document.getElementById("modal-pix").classList.add("active");
}

function fecharModalPix() {
    document.getElementById("modal-pix").classList.remove("active");
}

function copiarChavePix() {
    const inputChave = document.getElementById("chave-pix-copia");
    inputChave.select();
    document.execCommand("copy");
    alert("📋 Chave Pix copiada com sucesso!");
}

function confirmarPagamentoPix() {
    alert(`✓ Pagamento do Pedido #${pedidoIdPendente} confirmado! Estamos preparando a sua encomenda.`);
    fecharModalPix();
    limparECarregar();
}

function limparECarregar() {
    localStorage.removeItem("carrinho_malu");
    renderizarCarrinho();
    carregarPedidosCliente();
    alternarAba("status");
}

function carregarPedidosCliente() {
    const container = document.getElementById("lista-pedidos-cliente");

    const pedidosExemplo = [
        { id: 1024, data: "11/11/2026", status: "Sendo Preparado", badge: "preparo", total: 289.00 },
        { id: 1018, data: "08/11/2026", status: "Em Andamento (Em trânsito)", badge: "andamento", total: 170.90 },
        { id: 1002, data: "01/11/2026", status: "Está Chegando (Saiu para entrega)", badge: "chegando", total: 320.00 }
    ];

    container.innerHTML = "";
    pedidosExemplo.forEach(ped => {
        container.innerHTML += `
            <div class="card-status-pedido">
                <div class="header-status-pedido">
                    <strong>Pedido #${ped.id}</strong>
                    <span class="badge-status ${ped.badge}">${ped.status}</span>
                </div>
                <p style="font-size: 0.9rem; color: #5C436E;">Data: ${ped.data}</p>
                <p style="font-size: 1rem; color: #C5A059; font-weight: bold; margin-top: 5px;">Total: R$ ${ped.total.toFixed(2)}</p>
            </div>
        `;
    });
}