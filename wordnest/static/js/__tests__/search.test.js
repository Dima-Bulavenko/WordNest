/**
 * @jest-environment jsdom
 */
global.tippy = jest.fn();
document.getElementById = jest.fn();

describe("showRunButton", () => {
    let runButton;
    let showRunButton;

    beforeEach(() => {
        jest.resetModules();
        runButton = { style: { display: "none" } };
        document.getElementById.mockReturnValue(runButton);

        // Import search.js after document.getElementById is mocked
        showRunButton = require("../search").showRunButton;
    });

    afterEach(() => {
        document.getElementById.mockRestore();
    });

    test("showRunButton displays the run button when input value is not empty", () => {
        const event = { target: { value: "Not empty" } };

        showRunButton(event);

        expect(runButton.style.display).toBe("block");
    });

    test("showRunButton hides the run button when input value is empty", () => {
        const event = { target: { value: "" } };

        showRunButton(event);

        expect(runButton.style.display).toBe("none");
    });
});
