document.addEventListener("DOMContentLoaded", () => {
    const initialSignupButton = document.querySelector("#signup-form button");

    if (initialSignupButton) {
        initialSignupButton.addEventListener("click", showAdditionalFields);
    } else {
        console.error("Initial signup button not found!");
    }
});

function showAdditionalFields() {
    const signupFormContainer = document.querySelector("#signup-form");
    const csrfToken = document.querySelector("#csrf-token").value;

    if (signupFormContainer) {
        signupFormContainer.innerHTML = `
            <form id="signupForm">
                <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                <div class="dob-fields">
                    <label>Child's date of birth:</label>
                    <div class="dob-inputs">
                        <select name="day" required>
                            <option value="">DD</option>
                            ${Array.from({ length: 31 }, (_, i) => `<option value="${i + 1}">${i + 1}</option>`).join('')}
                        </select>
                        <select name="month" required>
                            <option value="">MM</option>
                            ${Array.from({ length: 12 }, (_, i) => `<option value="${i + 1}">${i + 1}</option>`).join('')}
                        </select>
                        <select name="year" required>
                            <option value="">YYYY</option>
                            ${Array.from({ length: 18 }, (_, i) => `<option value="${new Date().getFullYear() - i}">${new Date().getFullYear() - i}</option>`).join('')}
                        </select>
                    </div>
                </div>
                <div class="email-field">
                    <input type="email" name="email" placeholder="Your email address" required>
                </div>
                <button type="submit">Sign Me Up</button>
            </form>
        `;

        const signupForm = document.querySelector("#signupForm");
        signupForm.addEventListener("submit", function (event) {
            event.preventDefault();  // Prevent the default form submission

            // Get form data
            const day = signupForm.querySelector('select[name="day"]').value;
            const month = signupForm.querySelector('select[name="month"]').value;
            const year = signupForm.querySelector('select[name="year"]').value;
            const email = signupForm.querySelector('input[name="email"]').value;

            // Log the form data to the console
            console.log("Form submitted with the following data:");
            console.log(`DOB: ${day}-${month}-${year}`);
            console.log(`Email: ${email}`);

            // Display a success message in place of the form
            signupFormContainer.innerHTML = `
                <p>Thank you for signing up! Your details have been submitted successfully.</p>
            `;
        });
    } else {
        console.error("Signup form container not found!");
    }
}
