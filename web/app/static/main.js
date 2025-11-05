document.addEventListener('DOMContentLoaded', function() {

    // Função para atualizar o contador do carrinho no header
    function updateCartCounter() {
        fetch('/cart/count')
            .then(response => response.json())
            .then(data => {
                const cartCounter = document.getElementById('cart-counter');
                if (data.count > 0) {
                    cartCounter.textContent = data.count;
                    cartCounter.style.display = 'flex';
                } else {
                    cartCounter.style.display = 'none';
                }
            })
            .catch(error => console.error('Erro ao atualizar o contador do carrinho:', error));
    }

    // Função para mostrar uma notificação customizada (flash message)
    function showFlashMessage(message, category = 'success') {
        const container = document.getElementById('flash-messages');
        if (!container) return;

        let bgColor = 'bg-blue-100 text-blue-800 border-blue-200';
        if (category === 'success') {
            bgColor = 'bg-green-100 text-green-800 border-green-200';
        } else if (category === 'danger') {
            bgColor = 'bg-red-100 text-red-800 border-red-200';
        }

        const flashDiv = document.createElement('div');
        flashDiv.className = `p-4 mb-4 text-sm rounded-md shadow-lg animate-fade-in ${bgColor}`;
        flashDiv.setAttribute('role', 'alert');
        flashDiv.textContent = message;

        container.appendChild(flashDiv);

        // Remove a mensagem após 3 segundos
        setTimeout(() => {
            flashDiv.style.transition = 'opacity 0.5s ease';
            flashDiv.style.opacity = '0';
            setTimeout(() => flashDiv.remove(), 500);
        }, 3000);
    }

    // Lida com o formulário "Adicionar ao Carrinho" na página de detalhes do produto
    const addToCartForm = document.getElementById('add-to-cart-form');
    if (addToCartForm) {
        addToCartForm.addEventListener('submit', function(event) {
            event.preventDefault(); // Impede o recarregamento da página

            const formData = new FormData(this);
            const selectedColor = formData.get('color');
            const selectedSize = formData.get('size');

            if (!selectedColor || !selectedSize) {
                showFlashMessage('Por favor, selecione cor e tamanho.', 'danger');
                return;
            }

            fetch('/cart/add', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    showFlashMessage(data.message || 'Produto adicionado com sucesso!');
                    updateCartCounter();
                } else {
                    showFlashMessage(data.message || 'Ocorreu um erro.', 'danger');
                }
            })
            .catch(error => {
                console.error('Erro ao adicionar ao carrinho:', error);
                showFlashMessage('Erro de conexão.', 'danger');
            });
        });
    }

    // Atualiza o contador do carrinho assim que a página carrega
    updateCartCounter();
});