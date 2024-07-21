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

describe("createSearchResults", () => {
    let createSearchResults;
    createSearchResults = require("../search").createSearchResults;

    test("createSearchResults creates a div element with search results", () => {
        const translations = [
            { text: "Translation 1" },
            { text: "Translation 2" },
        ];

        const searchResults = createSearchResults(translations);

        expect(searchResults.id).toBe("search_results");
        expect(searchResults.children.length).toBe(3);

        for (let i = 0; i < translations.length; i++) {
            const resultElement = searchResults.children[i];
            expect(resultElement.className).toBe("search_result");
            expect(resultElement.innerText).toBe(translations[i].text);
        }
    });

    test("createSearchResults creates a div element with no results found", () => {
        const translations = [{ text: "" }, { text: "" }];

        const searchResults = createSearchResults(translations);

        expect(searchResults.id).toBe("search_results");
        expect(searchResults.children.length).toBe(1);
        expect(searchResults.innerText).toBe("No results found");
    });
});
