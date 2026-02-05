document.addEventListener('DOMContentLoaded', function () {
    const containers = document.querySelectorAll('.comparison-container');

    containers.forEach(container => {
        const overlay = container.querySelector('.comparison-overlay');
        const handle = container.querySelector('.comparison-handle');
        const topImage = overlay.querySelector('img');

        let isDragging = false;

        // Function to update widths
        function updateSlider(x) {
            const rect = container.getBoundingClientRect();
            let position = ((x - rect.left) / rect.width) * 100;

            // Accessibitlity limits (0% to 100%)
            position = Math.max(0, Math.min(100, position));

            overlay.style.width = `${position}%`;
            handle.style.left = `${position}%`;
        }

        // Mouse Events
        container.addEventListener('mousedown', () => isDragging = true);
        window.addEventListener('mouseup', () => isDragging = false);

        container.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            updateSlider(e.clientX);
        });

        // Touch Events (Mobile)
        container.addEventListener('touchstart', () => isDragging = true);
        window.addEventListener('touchend', () => isDragging = false);

        container.addEventListener('touchmove', (e) => {
            if (!isDragging) return;
            // Prevent scrolling while dragging slider on mobile
            // e.preventDefault(); 
            updateSlider(e.touches[0].clientX);
        });

        // Sync inner image width with container
        function syncImageWidth() {
            topImage.style.width = `${container.offsetWidth}px`;
        }

        window.addEventListener('resize', syncImageWidth);
        syncImageWidth(); // Initial sync
    });
});
