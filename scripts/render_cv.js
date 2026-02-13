/**
 * Custom CV Renderer Script
 * 
 * Renders JSON Resume to HTML using a specified theme (local or npm).
 * This replaces resume-cli for better control over module resolution and error handling.
 * 
 * Usage:
 *   node render_cv.js <theme_path> <json_path> <output_path>
 * 
 * Arguments:
 *   theme_path  - Path to theme directory or npm package name
 *   json_path   - Path to resume JSON file
 *   output_path - Destination path for generated HTML
 * 
 * @author CV Generator Build System
 * @version 1.0.0
 */

const fs = require('fs');
const path = require('path');

// Parse arguments: node render_cv.js <theme_path> <json_path> <output_path>
const args = process.argv.slice(2);
if (args.length < 3) {
    console.error("\n❌ Error: Missing required arguments");
    console.error("Usage: node render_cv.js <theme_path> <json_path> <output_path>");
    console.error("\nExample:");
    console.error("  node render_cv.js ./theme/stackoverflow temp_resume_de.json dist/latest/Web/de/index.html\n");
    process.exit(1);
}

const themePath = path.resolve(args[0]);
const jsonPath = path.resolve(args[1]);
const outputPath = path.resolve(args[2]);

// Validate inputs exist
if (!fs.existsSync(jsonPath)) {
    console.error(`\n❌ Error: JSON file not found: ${jsonPath}\n`);
    process.exit(1);
}


console.log(`Rendering CV...`);
console.log(`  Theme: ${themePath}`);
console.log(`  JSON:  ${jsonPath}`);

try {
    // Load Resume JSON
    const resume = JSON.parse(fs.readFileSync(jsonPath, 'utf-8'));

    // Load Theme
    // We try to require the theme path directly. 
    // Node will look for package.json main or index.js
    const theme = require(themePath);

    // Render
    const html = theme.render(resume);

    // Valid HTML?
    if (!html || typeof html !== 'string') {
        throw new Error("Theme returned empty or invalid HTML.");
    }

    // Write Output
    fs.writeFileSync(outputPath, html, 'utf-8');
    console.log(`  Success! Output written to: ${outputPath}`);

} catch (e) {
    console.error("Error rendering CV:");
    console.error(e);
    process.exit(1);
}
