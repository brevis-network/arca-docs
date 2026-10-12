(async () => {
    const blocks = document.querySelectorAll("code.language-mermaid");
    if (blocks.length === 0) return;

    try {
        const { default: mermaid } = await import(
            "https://cdn.jsdelivr.net/npm/mermaid@12.1.0/dist/mermaid.esm.min.mjs"
        );
        mermaid.initialize({ startOnLoad: false, securityLevel: "strict" });

        const diagrams = Array.from(blocks, (block) => {
            const diagram = document.createElement("div");
            diagram.className = "mermaid";
            diagram.textContent = block.textContent;
            block.parentElement.replaceWith(diagram);
            return diagram;
        });
        await mermaid.run({ nodes: diagrams });
    } catch (error) {
        console.error("Unable to render Mermaid diagrams", error);
    }
})();
