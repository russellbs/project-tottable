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

        // Preserve swap_mode, meal_type, and day parameters from the current URL
        const currentParams = new URLSearchParams(window.location.search);
        if (currentParams.has('swap')) {
            queryString.set('swap', currentParams.get('swap'));
        }
        if (currentParams.has('day')) {
            queryString.set('day', currentParams.get('day'));
        }

        // Note: meal_type is included from the form, so we don't need to manually add it unless you suspect issues with the form.

        // Update the URL without reloading
        const newUrl = `${window.location.pathname}?${queryString.toString()}`;
        window.history.pushState({}, '', newUrl);

        // Fetch filtered results via AJAX
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

                // Update pagination controls
                const newPagination = doc.querySelector('.pagination');
                const oldPagination = document.querySelector('.pagination');
                if (newPagination && oldPagination) {
                    oldPagination.innerHTML = newPagination.innerHTML;
                }
            })
            .catch(error => {
                console.error("Error fetching filtered results:", error);
            });
    }

    // Handle browser's back/forward navigation
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

                // Update pagination controls
                const newPagination = doc.querySelector('.pagination');
                const oldPagination = document.querySelector('.pagination');
                if (newPagination && oldPagination) {
                    oldPagination.innerHTML = newPagination.innerHTML;
                }
            })
            .catch(error => {
                console.error("Error handling popstate:", error);
            });
    });
});
