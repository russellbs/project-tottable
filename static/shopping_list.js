// Toggle cross-off state and save it in localStorage
function toggleCrossOff(button) {
    const item = button.closest('li').querySelector('span'); // More reliable selection
    if (item) {
        item.classList.toggle("text-decoration-line-through");

        const itemId = item.getAttribute("data-id") || item.textContent.trim();
        const isCrossedOff = item.classList.contains("text-decoration-line-through");
        saveCrossOffState(itemId, isCrossedOff);
    } else {
        console.error("Item not found for button:", button);
    }
}

// Save the cross-off state to localStorage
function saveCrossOffState(itemId, isCrossedOff) {
    try {
        const crossedOffItems = JSON.parse(localStorage.getItem("crossedOffItems")) || {};
        crossedOffItems[itemId] = isCrossedOff;
        localStorage.setItem("crossedOffItems", JSON.stringify(crossedOffItems));
    } catch (error) {
        console.error("Error saving cross-off state:", error);
    }
}

// Restore the cross-off state when the page loads
function restoreCrossOffState() {
    try {
        const crossedOffItems = JSON.parse(localStorage.getItem("crossedOffItems")) || {};
        document.querySelectorAll("#shopping-list li span").forEach(item => {
            const itemId = item.getAttribute("data-id") || item.textContent.trim();
            if (crossedOffItems[itemId]) {
                item.classList.add("text-decoration-line-through");
            }
        });
    } catch (error) {
        console.error("Error restoring cross-off state:", error);
    }
}

// Shared function to get uncrossed items
function getUncrossedItems() {
    return Array.from(document.querySelectorAll("#shopping-list li span"))
        .filter(item => !item.classList.contains("text-decoration-line-through"))
        .map(item => item.textContent)
        .join("\n");
}

// Email List (Only Non-Crossed Items)
document.getElementById("email-list-btn").addEventListener("click", function () {
    const items = getUncrossedItems();
    const subject = encodeURIComponent("My Tottable Shopping List");
    const body = encodeURIComponent(items);
    window.location.href = `mailto:?subject=${subject}&body=${body}`;
});

// Export to Notes (Only Non-Crossed Items)
document.getElementById("export-notes-btn").addEventListener("click", function () {
    const items = getUncrossedItems();

    if (navigator.share) {
        navigator.share({
            title: "Tottable Shopping List",
            text: items,
        }).catch((error) => console.error("Error sharing:", error));
    } else {
        alert("This feature is not supported on your device.");
    }
});

// Restore crossed-off state on page load
document.addEventListener("DOMContentLoaded", restoreCrossOffState);
