document.addEventListener('DOMContentLoaded', () => {
    const weekLabel = document.getElementById('week-label');
    const prevWeekBtn = document.getElementById('prev-week');
    const nextWeekBtn = document.getElementById('next-week');
    const mealPlan = document.getElementById('meal-plan');

    // Example week data (replace with dynamic backend data)
    const weeks = [
        { week: 'Nov 20, 2024', days: [{ name: 'Monday', breakfast: 'Pancakes', lunch: 'Salad', dinner: 'Pizza' }] },
        { week: 'Nov 27, 2024', days: [{ name: 'Monday', breakfast: 'Smoothie', lunch: 'Sandwich', dinner: 'Pasta' }] }
    ];
    let currentWeekIndex = 0;

    // Function to update meal plan view
    const updateMealPlan = () => {
        const weekData = weeks[currentWeekIndex];
        weekLabel.textContent = `Week of ${weekData.week}`;
        mealPlan.innerHTML = weekData.days.map(day => `
            <div class="col-md-4 mb-4">
                <div class="card shadow-sm h-100">
                    <div class="card-body">
                        <h3 class="card-title">${day.name}</h3>
                        <ul class="list-group list-group-flush">
                            <li class="list-group-item">
                                Breakfast: ${day.breakfast}
                                <button class="btn btn-sm btn-outline-primary float-end">Edit</button>
                            </li>
                            <li class="list-group-item">
                                Lunch: ${day.lunch}
                                <button class="btn btn-sm btn-outline-primary float-end">Edit</button>
                            </li>
                            <li class="list-group-item">
                                Dinner: ${day.dinner}
                                <button class="btn btn-sm btn-outline-primary float-end">Edit</button>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        `).join('');
    };

    // Event listeners for week navigation
    prevWeekBtn.addEventListener('click', () => {
        currentWeekIndex = Math.max(0, currentWeekIndex - 1); // Prevent going below first week
        updateMealPlan();
    });

    nextWeekBtn.addEventListener('click', () => {
        currentWeekIndex = Math.min(weeks.length - 1, currentWeekIndex + 1); // Prevent going past last week
        updateMealPlan();
    });

    // Initial render
    updateMealPlan();
});
