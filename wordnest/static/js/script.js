// Configuration
const burgerMenuSelector = "#burger-menu";
const navigationSelector = "#navigation";

/**
 * Toggles the 'active' class for each given element.
 *
 * @param {...Element} elements - The elements to toggle the 'active' class for.
 */
function toggleActiveClass(...elements) {
    elements.forEach((element) => element.classList.toggle("active"));
}

// Event listeners
let burgerMenu = document.querySelector(burgerMenuSelector);

burgerMenu.addEventListener("click", function () {
    toggleActiveClass(this, document.querySelector(navigationSelector));
});