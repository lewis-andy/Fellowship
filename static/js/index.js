document.addEventListener('DOMContentLoaded', function() {
    const slides = document.querySelectorAll('.slide');
    const slideWrapper = document.querySelector('.slide-wrapper');
    let index = 0;

    function showSlide() {
        slideWrapper.style.transition = 'transform 0.5s ease-in-out';
        slideWrapper.style.transform = `translateX(-${index * 100}%)`;
    }

    function nextSlide() {
        index = (index + 1) % slides.length;
        showSlide();
    }

    setInterval(nextSlide, 5000); // Change slide every 5 seconds
});
