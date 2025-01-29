document.addEventListener("DOMContentLoaded", function () {
    // Within-Week Preferences Elements
    const editWithinWeekBtn = document.getElementById("edit-within-week-preferences-btn");
    const withinWeekDisplay = document.getElementById("preferences-within-week-display");
    const withinWeekForm = document.getElementById("preferences-within-week-form");
    const cancelWithinWeekBtn = document.getElementById("cancel-within-week-preferences-btn");

    // Function to update the display dynamically
    function updateWithinWeekPreferenceDisplay(preferences) {
        withinWeekDisplay.innerHTML = `
            <h3>Within-Week Variety</h3>
            <p><strong>Breakfast:</strong> ${preferences.breakfast || "No preference selected"}</p>
            <p><strong>Lunch:</strong> ${preferences.lunch || "No preference selected"}</p>
            <p><strong>Dinner:</strong> ${preferences.dinner || "No preference selected"}</p>
            <p><strong>Snack:</strong> ${preferences.snack || "No preference selected"}</p>
            <button id="edit-within-week-preferences-btn" class="btn btn-primary">Edit Within-Week Preferences</button>
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
                headers: { "X-Requested-With": "XMLHttpRequest" },
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
