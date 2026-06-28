module.exports = function (eleventyConfig) {
  // Assets and the existing hand-coded pages pass through untouched
  // until each page is migrated to a template. This keeps the live
  // design pixel-identical while we add new data-driven pages.
  eleventyConfig.addPassthroughCopy("assets");
  ["about","contact","directing","gallery","index","performing","teaching","weddings"]
    .forEach(p => eleventyConfig.addPassthroughCopy(`${p}.html`));
  eleventyConfig.addPassthroughCopy("robots.txt");
  eleventyConfig.addPassthroughCopy("sitemap.xml");

  // Sveltia editor: copied verbatim, never templated
  eleventyConfig.addPassthroughCopy({ "src/admin": "admin" });
  eleventyConfig.ignores.add("src/admin/**");

  // Date helper for the updates feed
  eleventyConfig.addFilter("prettyDate", (d) => {
    const dt = new Date(d + "T12:00:00");
    return dt.toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" });
  });

  return { dir: { input: "src", includes: "_includes", data: "_data", output: "_site" } };
};
