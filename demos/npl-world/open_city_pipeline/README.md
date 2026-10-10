# NPL WORLD – city build from public source data

This is a real georeferenced model-building pipeline for a section of Alicante. It does NOT produce photogrammetric building facades or a GTA-quality scene. Its purpose is to solve the execution blockade using a free public GitHub Actions standard CPU runner.

Sources: OpenStreetMap building footprints (ODbL, © contributors) and PNOA orthophotography (© IGN). The height of buildings is only directly measured where OSM has the height tag; otherwise the program makes a rough estimate from OSM building levels.

Run at GitHub > NPL-CANONICAL > Actions > NPL Alicante 3D - open city on free CPU > Run workflow. When complete download the artifact NPL_Alicante_real_OSM_PNOA_only_NO_FACE. It includes an editable .blend and a GLB with OSM building footprints and optionally a genuine PNOA image on the ground, as well as a data report.

NEVER UPLOAD private photographs, avatar face meshes, personalized GLB or textures to this public repository. Do not use larger or private runners as they can incur usage fees. Public standard runners are free but artifact storage allowances apply. The pipeline never calls paid geodata APIs.
