document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.navItem').forEach((item, idx) => {
        item.addEventListener('click', () => {
            const routes = document.querySelector('.routes');

            // Calculate the offset based on index (0, 1, 2)
            const offset = idx * (100 / 3); // Each route is 1/3 of total width

            routes.style.transform = `translateX(-${offset}%)`;
            console.log("clicked:", idx, "offset:", offset + "%");
        });
    });
});