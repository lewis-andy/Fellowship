// JavaScript for slider animation

let currentIndex = 0;
const slides = document.querySelectorAll('.slide');
const totalSlides = slides.length;

function showSlide(index) {
    slides.forEach(slide => {
        slide.style.display = 'none';
    });

    slides[index].style.display = 'block';
}

function nextSlide() {
    currentIndex++;
    if (currentIndex >= totalSlides) {
        currentIndex = 0;
    }
    showSlide(currentIndex);
}

function prevSlide() {
    currentIndex--;
    if (currentIndex < 0) {
        currentIndex = totalSlides - 1;
    }
    showSlide(currentIndex);
}

document.addEventListener('DOMContentLoaded', function () {
    showSlide(currentIndex);
    setInterval(nextSlide, 5000); // Change slide every 5 seconds
});
