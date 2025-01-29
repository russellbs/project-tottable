document.addEventListener("DOMContentLoaded", () => {
    const posts = document.querySelectorAll(".featured-post");
    const dots = document.querySelectorAll(".dot");
    let currentIndex = 0;
    const intervalTime = 5000;
    let interval;

    const showSlide = (index) => {
        posts.forEach((post, idx) => {
            post.style.transform = `translateX(-${index * 100}%)`;
        });
        dots.forEach(dot => dot.classList.remove("active"));
        dots[index].classList.add("active");
    };

    const nextSlide = () => {
        currentIndex = (currentIndex + 1) % posts.length;
        showSlide(currentIndex);
    };

    const startCarousel = () => {
        interval = setInterval(nextSlide, intervalTime);
    };

    const stopCarousel = () => {
        clearInterval(interval);
    };

    startCarousel();

    document.querySelector(".featured-posts").addEventListener("mouseover", stopCarousel);
    document.querySelector(".featured-posts").addEventListener("mouseout", startCarousel);

    dots.forEach(dot => {
        dot.addEventListener("click", () => {
            currentIndex = parseInt(dot.getAttribute("data-index"));
            showSlide(currentIndex);
            stopCarousel();
        });
    });
});
