/**
 * @jest-environment jsdom
 */
const fs = require("fs");
const path = require("path");
const html = fs.readFileSync(path.resolve(__dirname, "test.html"), "utf-8");
document = html;

const { addClickListenersToInfoIcons } = require("../auth");

describe("Test addClickListenersToInfoIcons function", () => {
    beforeEach(() => {
        // Mock the toggleActiveClass function and make it globally available
        // to substitute the original function in addClickListenersToInfoIcons func.
        const toggleActiveClass = jest.fn();
        global.toggleActiveClass = toggleActiveClass;
    });

    test("Test with one icon", () => {
        document.body.innerHTML = `
            <div class="info_icon" data-help-text-id="help_text_1"></div>
            <div id="help_text_1"></div>
        `;
        addClickListenersToInfoIcons();
        document.querySelector(".info_icon").click();
        expect(toggleActiveClass).toHaveBeenCalledTimes(1);
    });

    test("Test with multiple icons", () => {
        document.body.innerHTML = `
            <div class="info_icon" data-help-text-id="help_text_1"></div>
            <div class="info_icon" data-help-text-id="help_text_2"></div>
            <div id="help_text_1"></div>
            <div id="help_text_2"></div>
        `;
        addClickListenersToInfoIcons();
        document.querySelectorAll(".info_icon").forEach((icon) => icon.click());
        expect(toggleActiveClass).toHaveBeenCalledTimes(2);
    });

    test("Test first icon does not have associated help_text", () => {
        document.body.innerHTML = `
            <div class="info_icon" data-help-text-id="help_text_1"></div>
            <div class="info_icon" data-help-text-id="help_text_2"></div>
            <div id="help_text_1"></div>
        `;
        addClickListenersToInfoIcons();
        document.querySelectorAll(".info_icon").forEach((icon) => icon.click());
        expect(toggleActiveClass).toHaveBeenCalledTimes(1);
    });
});
