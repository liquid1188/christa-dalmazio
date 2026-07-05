module.exports = function (eleventyConfig) {
  // Assets and the existing hand-coded pages pass through untouched
  // until each page is migrated to a template. This keeps the live
  // design pixel-identical while we add new data-driven pages.
  eleventyConfig.addPassthroughCopy("assets");
  eleventyConfig.addPassthroughCopy({ "src/CNAME": "CNAME" });
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

  // Endorser roles: keep each segment whole and let the line break at the · separator,
  // so a secondary institution falls cleanly onto the second line.
  eleventyConfig.addFilter("roleBreak", (role) => {
    if (!role) return role;
    const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    return role
      .split(" \u00b7 ")
      .map((seg) => `<span class="en-seg">${esc(seg)}</span>`)
      .join("&#160;\u00b7 ");
  });

  return { dir: { input: "src", includes: "_includes", data: "_data", output: "_site" } };
};
