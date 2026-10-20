# NeuroCity 3D Alicante — Evidence chain (20 October 2026)

STATUS: independent DRAFT branches, no merger, no deployment, no raw GML or real-world GLB distributed. Keep this permanent engineering note so that actual results do not vanish between iterations.

## Measured progress on the same public OSM geometry

- Phase A — PR #32: one official Catastro WFS tile, 21 OSM buildings with 109 official BuildingPart volumes. Proof: https://github.com/clucaina/NPL-CANONICAL/actions/runs/39412818252
- Phase B — PR #34: nine-sector Catastro grid with six WFS tiles initially available: 38 OSM buildings and 155 official BuildingPart volumes. Proof: https://github.com/clucaina/NPL-CANONICAL/actions/runs/39413848074
- Phase C — PR #34: nine of nine tiles independently retrieved: 3,946 unique official parts and still 38 matched OSM buildings and 155 matched volumes. This proves the remaining mismatch is geometrical rather than simply a lack of downloaded sources. Proof: https://github.com/clucaina/NPL-CANONICAL/actions/runs/39414183545
- Phase D — PR #36: nine of nine official WFS tiles, 38 OSM buildings safely replaced by 155 part-volumes, PLUS 52 non-overlapping official source parts added to the map as separate geometry. Total 207 real Catastro-derived 3D PART VOLUMES. Proof: https://github.com/clucaina/NPL-CANONICAL/actions/runs/39414824483

The original 614 OSM buildings remain the base cartography. 52 added source parts are NOT automatically 52 distinct complete buildings. None of the 207 parts constitute photogrammetric facades.

## Last real Blender output

Official WFS source candidate parts: 6,672. Unique geometries: 3,945. Duplicates removed: 2,727. Reliable matches: 155 parts in 38 OSM buildings. Additional source geometry with a safe clearance of more than 4 meters from ANY mapped OSM building: 52 parts. Spatial exclusions: 798 outside useful map bounds, 1,192 too small, 1,903 colliding/near OSM. Ambiguous OSM-to-Catastro associations rejected: 394.

Real Blender-created but ephemeral GLB: 1,277,900 bytes. SHA256: 7735640b2e797aef8f5273559fe4dd2dd427882ca747555ee96d0e71f128e9d3. Source GML and derived GLB deleted from temporary job directory, not committed, published or deployed. Audit records contain only metadata and aggregate counts.

## The verified dependency chain

PR #29: Mediterranean WebGL and quality switch in Alicante visor.
PR #32: official bounded Catastro BuildingPart to conservative 3D OSM replacement.
PR #34: nine-zone official grid, cross-tile canonical deduplication, incomplete-source rejection and bounded retry.
PR #36: official source parts genuinely absent from OSM, independent 3D volumes and strict geographic clearance.

The PRs are interdependent DRAFTs. Do not cherry-pick numbers into production or merge them independently without integrating their code and checking all test evidence.

## Scientific and safety boundaries

The official floor count is converted to an ESTIMATED physical volume using floors multiplied by three meters. This is NOT LiDAR measured height. A verified horizontal coordinate is NOT a surveyed facade, authentic shop interior, real-world merchant sign, employee or roof height.

The derived Catastro GLB was NOT yet wired into the playable city. Next priority: run a private, no-deploy WebGL visual acceptance test with the real 3D city assembled on one machine. Then independently obtain LiDAR-PNOA surface and ground elevations with matching CRS, datum, acquisition dates and outlier controls. After that, improve facade sources, shopfront attribution and spatial LOD without inventing details.

No original NPL or Conflictometro database was changed. Do not use patient data, property owner names, personal addresses or private avatars.

Source links: https://www.catastro.hacienda.gob.es/webinspire/ ; https://www.openstreetmap.org/copyright ; https://pnoa.ign.es/web/portal/pnoa-lidar/productos-a-descarga ; https://www.catastro.hacienda.gob.es/webinspire/documentos/Licencia.pdf

DO NOT present these experimental building volumes as a finished photorealistic Alicante game.
