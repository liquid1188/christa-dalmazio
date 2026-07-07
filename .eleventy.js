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

  // Image dimensions at build time (JPEG/PNG header read, no dependencies).
  // Gives every gallery <img> width/height attributes so the masonry columns
  // are laid out before the photos load — no reflow scramble.
  const fs = require("fs");
  const path = require("path");
  const dimCache = {};
  function readDims(rel) {
    if (rel in dimCache) return dimCache[rel];
    let out = null;
    try {
      const p = path.join(__dirname, rel.replace(/^\//, ""));
      const buf = fs.readFileSync(p);
      if (buf[0] === 0x89 && buf[1] === 0x50) {
        // PNG: IHDR at fixed offset
        out = { w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) };
      } else if (buf[0] === 0xff && buf[1] === 0xd8) {
        // JPEG: scan markers for SOF0/1/2
        let i = 2;
        while (i < buf.length - 9) {
          if (buf[i] !== 0xff) { i++; continue; }
          const m = buf[i + 1];
          if (m >= 0xc0 && m <= 0xc2) { out = { h: buf.readUInt16BE(i + 5), w: buf.readUInt16BE(i + 7) }; break; }
          if (m === 0xd8 || (m >= 0xd0 && m <= 0xd9)) { i += 2; continue; }
          i += 2 + buf.readUInt16BE(i + 2);
        }
      }
    } catch (e) { out = null; }
    dimCache[rel] = out;
    return out;
  }
  eleventyConfig.addFilter("imgDims", readDims);

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
