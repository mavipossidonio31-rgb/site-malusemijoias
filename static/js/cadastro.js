document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("form");
    if (form) {
        form.addEventListener("submit", () => {
            alert("Cadastro realizado com sucesso!");
        });
    }
});