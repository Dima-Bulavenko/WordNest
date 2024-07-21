const fs = require("fs");
const path = require("path");
const { JSDOM } = require("jsdom");
const html = fs.readFileSync(path.resolve(__dirname, "test.html"), "utf-8");
const dom = new JSDOM(html);
global.document = dom.window.document;

beforeEach(() => {
    const dom = new JSDOM(html);
    global.document = dom.window.document;
});

const { toggleActiveClass } = require("../script");

describe("Test toggleActiveClass function", () => {
    test("Test with one passed element", () => {
        const element = document.createElement("div");
        toggleActiveClass(element);

        expect(element.classList.contains("active")).toBe(true);
    });

    test("Test with multiple passed elements", () => {
        const element1 = document.createElement("div");
        const element2 = document.createElement("div");
        toggleActiveClass(element1, element2);

        expect(element1.classList.contains("active")).toBe(true);
        expect(element2.classList.contains("active")).toBe(true);
    });

    test("Test with no passed elements", () => {
        // Check that the function won't throw an error if no elements are passed
        expect(() => toggleActiveClass()).not.toThrow();
    });

    test("Test non-element type passed", () => {
        // Check that the function won't throw an error if a non-element is passed
        expect(() => toggleActiveClass("element")).toThrow(TypeError);
    });
});
