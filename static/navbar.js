document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ Navbar JS Loaded!");

    let dropdownTrigger = document.getElementById("userDropdown");
    let dropdownMenu = document.getElementById("userDropdownMenu");

    if (!dropdownTrigger || !dropdownMenu) {
        console.log("❌ Dropdown elements not found.");
        return;
    }

    console.log("✅ Dropdown elements found.");

    // Toggle dropdown when clicking on the profile circle
    dropdownTrigger.addEventListener("click", function (event) {
        event.preventDefault(); // Prevent navigation
        console.log("✅ Click detected on userDropdown");

        // Toggle the show class
        dropdownMenu.classList.toggle("show");

        // Log visibility status
        console.log("Dropdown is now", dropdownMenu.classList.contains("show") ? "VISIBLE" : "HIDDEN");
    });

    // Close dropdown when clicking outside
    document.addEventListener("click", function (event) {
        if (!dropdownTrigger.contains(event.target) && !dropdownMenu.contains(event.target)) {
            dropdownMenu.classList.remove("show");
            console.log("✅ Clicked outside, dropdown hidden.");
        }
    });
});
