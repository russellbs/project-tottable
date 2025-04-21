document.addEventListener('DOMContentLoaded', function () {
    const filterForm = document.getElementById('filter-form');

    // Attach change event listeners to form inputs
    const filterInputs = filterForm.querySelectorAll('input, select');
    filterInputs.forEach(input => {
        input.addEventListener('change', () => {
            applyFilters();
        });
    });

    function applyFilters() {
        // Collect filter data from the form
        const formData = new FormData(filterForm);
        const queryString = new URLSearchParams(formData);

        // Preserve swap_mode and day parameters
        const currentParams = new URLSearchParams(window.location.search);
        if (currentParams.has('swap')) {
            queryString.set('swap', currentParams.get('swap'));
        }
        if (currentParams.has('day')) {
            queryString.set('day', currentParams.get('day'));
        }

        const newUrl = `${window.location.pathname}?${queryString.toString()}`;
        window.history.pushState({}, '', newUrl);

        fetch(newUrl, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.text();
        })
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');

            // Update the recipe grid
            const newGrid = doc.querySelector('.recipe-grid');
            const oldGrid = document.querySelector('.recipe-grid');
            if (newGrid && oldGrid) {
                oldGrid.innerHTML = newGrid.innerHTML;
            }

            // Update pagination
            const newPagination = doc.querySelector('.pagination');
            const oldPagination = document.querySelector('.pagination');
            if (newPagination && oldPagination) {
                oldPagination.innerHTML = newPagination.innerHTML;
            }

            // Update allergen alert
            const newAlert = doc.querySelector('.alert.alert-warning');
            const oldAlert = document.querySelector('.alert.alert-warning');
            const header = document.querySelector('.library-header');

            if (newAlert) {
                if (oldAlert) {
                    oldAlert.replaceWith(newAlert);
                } else if (header) {
                    header.insertAdjacentElement('afterend', newAlert);
                }
            } else if (oldAlert) {
                oldAlert.remove();
            }
        })
        .catch(error => {
            console.error("Error fetching filtered results:", error);
        });
    }

    // Handle browser back/forward buttons
    window.addEventListener('popstate', () => {
        fetch(window.location.href, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.text();
        })
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');

            // Update the recipe grid
            const newGrid = doc.querySelector('.recipe-grid');
            const oldGrid = document.querySelector('.recipe-grid');
            if (newGrid && oldGrid) {
                oldGrid.innerHTML = newGrid.innerHTML;
            }

            // Update pagination
            const newPagination = doc.querySelector('.pagination');
            const oldPagination = document.querySelector('.pagination');
            if (newPagination && oldPagination) {
                oldPagination.innerHTML = newPagination.innerHTML;
            }

            // Update allergen alert
            const newAlert = doc.querySelector('.alert.alert-warning');
            const oldAlert = document.querySelector('.alert.alert-warning');
            const filterForm = document.querySelector('filter-form');

            if (newAlert) {
                if (oldAlert) {
                    oldAlert.replaceWith(newAlert);
                } else if (filterForm) {
                    filterForm.insertAdjacentElement('afterend', newAlert);
                }
            } else if (oldAlert) {
                oldAlert.remove();
            }
        })
        .catch(error => {
            console.error("Error handling popstate:", error);
        });
    });
});
