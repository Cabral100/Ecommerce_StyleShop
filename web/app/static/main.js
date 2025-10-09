// app/static/js/main.js

document.addEventListener('DOMContentLoaded', function() {
    // Lógica para todos os carrosséis da página
    const carousels = document.querySelectorAll('.carousel');

    carousels.forEach(carousel => {
        const items = carousel.querySelectorAll('.carousel-item');
        const prevBtn = carousel.nextElementSibling; // O botão 'prev'
        const nextBtn = prevBtn.nextElementSibling; // O botão 'next'
        let currentIndex = 0;

        function showItem(index) {
            items.forEach((item, i) => {
                item.style.display = i === index ? 'block' : 'none';
            });
        }

        prevBtn.addEventListener('click', () => {
            currentIndex = (currentIndex > 0) ? currentIndex - 1 : items.length - 1;
            showItem(currentIndex);
        });

        nextBtn.addEventListener('click', () => {
            currentIndex = (currentIndex < items.length - 1) ? currentIndex + 1 : 0;
            showItem(currentIndex);
        });

        // Inicia mostrando o primeiro item
        showItem(currentIndex);
    });
});