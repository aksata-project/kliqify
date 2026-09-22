const fs = require('fs');
const code = fs.readFileSync('dashboard.xml', 'utf8');
const scripts = [...code.matchAll(/<script[\s\S]*?>([\s\S]*?)<\/script>/gi)];

for (let i = 0; i < scripts.length; i++) {
    const scriptContent = scripts[i][1];
    try {
        new Function(scriptContent);
    } catch (e) {
        console.log(`Script Block ${i + 1} has error: ${e.message}`);

        // Let's find exactly which line
        const lines = scriptContent.split('\n');
        for (let l = 0; l < lines.length; l++) {
            try {
                // progressive parse
                new Function(lines.slice(0, l + 1).join('\n'));
            } catch (err) {
                if (err.message.includes("Unexpected token ';'")) {
                    console.log(`Error near line ${l + 1}: ${lines[l]}`);
                    const context = lines.slice(Math.max(0, l - 2), l + 3).join('\n');
                    console.log('-- Context --\n' + context);
                    break;
                }
            }
        }
    }
}
