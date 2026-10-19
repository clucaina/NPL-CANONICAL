# NeuroCity observatory review

This draft adds a local-only data panel above the existing public 3D city. It supports versioned public aggregate JSON files from NPL and CONFLICTOMETRO, year filters and source links. No source databases are modified.

Build the public city using the existing review workflow. Copy observatory.html, observatory.css, observatory.mjs and public_layers.mjs into the generated dist folder. Serve dist with a local HTTP server and open observatory.html.

Run node --test tests/*.test.mjs from visual_viewer. The repository has no verified public NPL/Conflictometro exports. Test data is synthetic. No production data integration or photorealism is claimed.
