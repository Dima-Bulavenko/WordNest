/**
 * Adds a click event listener to each icon. When an icon is clicked, it toggles the active class
 * for the associated help text.
 *
 * @param {NodeListOf<Element>} infoIcons - A list of elements with the class 'info_icon'.
 */
function addClickListenersToInfoIcons(infoIcons) {
    infoIcons.forEach(function(icon) {
        icon.addEventListener('click', function() {
            const helpTextId = this.dataset.helpTextId;
            const helpText = document.getElementById(helpTextId);
            if (helpText !== null) {
                toggleActiveClass(this, helpText);
            }
        });
    });
}

window.onload = function() {
    var infoIcons = document.querySelectorAll('.info_icon');
    addClickListenersToInfoIcons(infoIcons);
};