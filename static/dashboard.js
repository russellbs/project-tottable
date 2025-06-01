document.addEventListener('DOMContentLoaded', () => {
    console.log('Dashboard JS loaded.');

    document.querySelectorAll('.remove-meal-link').forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault();

            if (!confirm("Are you sure you want to remove this meal?")) return;

            const mealId = this.dataset.mealId;
            const mealType = this.dataset.mealType;
            const url = this.dataset.url;

            console.log('Clicked remove for:', mealId, mealType, url);

            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

            if (!csrfToken) {
                console.error('CSRF token not found');
                alert('CSRF token missing');
                return;
            }

            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: new URLSearchParams({
                    'meal_id': mealId,
                    'meal_type': mealType
                })
            })
            .then(response => {
                if (!response.ok) throw new Error('Request failed');
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    console.log('Meal removed successfully.');
                    location.reload();
                } else {
                    console.error('Failed to remove meal:', data.error);
                    alert('Error removing meal: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(err => {
                console.error('Error during removal:', err);
                alert('Something went wrong.');
            });
        });
    });
});
