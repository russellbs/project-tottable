function getCsrfToken() {
    return document.querySelector("[name=csrfmiddlewaretoken]").value;
}

document.addEventListener("DOMContentLoaded", function () {
    // Within-Week Preferences Elements
    const editWithinWeekBtn = document.getElementById("edit-within-week-preferences-btn");
    const withinWeekDisplay = document.getElementById("preferences-within-week-display");
    const withinWeekForm = document.getElementById("preferences-within-week-form");
    const cancelWithinWeekBtn = document.getElementById("cancel-within-week-preferences-btn");

    // Function to update the display dynamically
    function updateWithinWeekPreferenceDisplay(preferences) {
        const capitalize = (text) => text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
    
        withinWeekDisplay.innerHTML = `
            <h3>Within-Week Variety</h3>
            <p><strong>Breakfast:</strong> ${preferences.breakfast || "No Preference Selected"}</p>
            <p><strong>Lunch:</strong> ${preferences.lunch || "No Preference Selected"}</p>
            <p><strong>Dinner:</strong> ${preferences.dinner || "No Preference Selected"}</p>
            <p><strong>Snack:</strong> ${preferences.snack || "No Preference Selected"}</p>
            <button id="edit-within-week-preferences-btn" class="btn btn-primary">Edit Within-Week Preferences</button>
        `;
        rebindWithinWeekEditButton();
    
        // Pre-fill the form with the user's preferences
        withinWeekForm.innerHTML = `
            <h3>Update Within-Week Variety</h3>
            <div class="form-group">
                <label for="within_week_breakfast">Breakfast</label>
                <select name="breakfast" id="within_week_breakfast" class="form-control">
                    <option value="no" ${preferences.breakfast === "No Variety" ? "selected" : ""}>No Variety</option>
                    <option value="low" ${preferences.breakfast === "Low Variety" ? "selected" : ""}>Low Variety</option>
                    <option value="medium" ${preferences.breakfast === "Medium Variety" ? "selected" : ""}>Medium Variety</option>
                    <option value="high" ${preferences.breakfast === "High Variety" ? "selected" : ""}>High Variety</option>
                </select>
            </div>
            <div class="form-group">
                <label for="within_week_lunch">Lunch</label>
                <select name="lunch" id="within_week_lunch" class="form-control">
                    <option value="no" ${preferences.lunch === "No Variety" ? "selected" : ""}>No Variety</option>
                    <option value="low" ${preferences.lunch === "Low Variety" ? "selected" : ""}>Low Variety</option>
                    <option value="medium" ${preferences.lunch === "Medium Variety" ? "selected" : ""}>Medium Variety</option>
                    <option value="high" ${preferences.lunch === "High Variety" ? "selected" : ""}>High Variety</option>
                </select>
            </div>
            <div class="form-group">
                <label for="within_week_dinner">Dinner</label>
                <select name="dinner" id="within_week_dinner" class="form-control">
                    <option value="no" ${preferences.dinner === "No Variety" ? "selected" : ""}>No Variety</option>
                    <option value="low" ${preferences.dinner === "Low Variety" ? "selected" : ""}>Low Variety</option>
                    <option value="medium" ${preferences.dinner === "Medium Variety" ? "selected" : ""}>Medium Variety</option>
                    <option value="high" ${preferences.dinner === "High Variety" ? "selected" : ""}>High Variety</option>
                </select>
            </div>
            <div class="form-group">
                <label for="within_week_snack">Snack</label>
                <select name="snack" id="within_week_snack" class="form-control">
                    <option value="no" ${preferences.snack === "No Variety" ? "selected" : ""}>No Variety</option>
                    <option value="low" ${preferences.snack === "Low Variety" ? "selected" : ""}>Low Variety</option>
                    <option value="medium" ${preferences.snack === "Medium Variety" ? "selected" : ""}>Medium Variety</option>
                    <option value="high" ${preferences.snack === "High Variety" ? "selected" : ""}>High Variety</option>
                </select>
            </div>
            <button type="submit" class="btn btn-success">Save Within-Week Preferences</button>
            <button type="button" id="cancel-within-week-preferences-btn" class="btn btn-secondary">Cancel</button>
        `;
        rebindWithinWeekEditButton();
    }
    

    function handleWithinWeekFormSubmission() {
        withinWeekForm.addEventListener("submit", function (e) {
            e.preventDefault(); // Prevent page reload
            console.log("Within-Week form submitted.");

            const formData = new FormData(withinWeekForm);

            // Log the form data before sending
            console.log("Form Data Submitted:");
            for (let pair of formData.entries()) {
                console.log(pair[0] + ": " + pair[1]);
            }

            fetch(withinWeekForm.action, {
                method: "POST",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "X-CSRFToken": getCsrfToken(),
                },
                body: formData,
            })            
                .then((response) => {
                    if (!response.ok) {
                        throw new Error(`Failed to save preferences: ${response.statusText}`);
                    }
                    return response.json();
                })
                .then((data) => {
                    if (data.success) {
                        console.log("Within-Week preferences saved successfully:", data);
                        updateWithinWeekPreferenceDisplay(data.preferences);

                        // Switch back to the display view
                        withinWeekDisplay.style.display = "block";
                        withinWeekForm.style.display = "none";
                    } else {
                        console.error("Error saving Within-Week preferences:", data.error);
                        alert(data.error || "Failed to save preferences. Please try again.");
                    }
                })
                .catch((error) => {
                    console.error("Error saving Within-Week preferences:", error);
                    alert("An error occurred while saving preferences.");
                });
        });
    }

    // Function to rebind edit button
    function rebindWithinWeekEditButton() {
        const newEditWithinWeekBtn = document.getElementById("edit-within-week-preferences-btn");
        newEditWithinWeekBtn.addEventListener("click", function () {
            console.log("Edit Within-Week Preferences button clicked.");
            withinWeekDisplay.style.display = "none";
            withinWeekForm.style.display = "block";
        });
    }

    // Within-Week Preferences Handlers
    if (editWithinWeekBtn && withinWeekDisplay && withinWeekForm && cancelWithinWeekBtn) {
        editWithinWeekBtn.addEventListener("click", function () {
            console.log("Edit Within-Week Preferences button clicked.");
            withinWeekDisplay.style.display = "none";
            withinWeekForm.style.display = "block";
        });

        cancelWithinWeekBtn.addEventListener("click", function () {
            console.log("Cancel Within-Week Preferences button clicked.");
            withinWeekDisplay.style.display = "block";
            withinWeekForm.style.display = "none";
        });

        handleWithinWeekFormSubmission();
    }
});

document.addEventListener("DOMContentLoaded", function () {
    // Add event listeners to all regenerate buttons
    const regenerateButtons = document.querySelectorAll(".regenerate-meal-plan-btn");

    regenerateButtons.forEach((button) => {
        button.addEventListener("click", function () {
            const childId = button.getAttribute("data-child-id"); // Fetch the child ID

            if (!childId) {
                console.error("Child ID is missing.");
                alert("Failed to regenerate meal plan. Please try again.");
                return;
            }

            if (confirm(`Are you sure you want to regenerate ${button.innerText}?`)) {
                fetch(`/regenerate-meal-plan/${childId}/`, {
                    method: "POST",
                    headers: { "X-CSRFToken": getCsrfToken() },
                })
                    .then((response) => {
                        if (!response.ok) {
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }
                        return response.json();
                    })
                    .then((data) => {
                        if (data.success) {
                            alert(data.message);
                            location.reload(); // Reload the page to show the updated plan
                        } else {
                            console.error("Error in response data:", data);
                            alert(data.message || "Failed to regenerate meal plan.");
                        }
                    })
                    .catch((error) => {
                        console.error("Error regenerating meal plan:", error);
                        alert("An error occurred. Please try again later.");
                    });
            }
        });
    });

    
});
