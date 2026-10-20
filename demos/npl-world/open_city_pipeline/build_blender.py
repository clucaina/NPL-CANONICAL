#!/usr/bin/env python3
"""Blender CPU: real OSM footprints + available PNOA orthophoto ground. NO invented landmark."""
import bpy, math, json, re, hashlib, xml.etree.ElementTree as ET
from mathutils.geometry import tessellate_polygon
from pathlib import Path
from mathutils import Vector
D=Path("input");O=Path("output");O.mkdir(exist_ok=True)
info=json.loads((D/"source_manifest.json").read_text())
R=6378137.;cx,cy=info["center_mercator"]
def local(lon,lat):
    return R*math.radians(lon)-cx,R*math.log(math.tan(math.pi/4+math.radians(lat)/2))-cy
doc=ET.parse(D/"alicante.osm").getroot()
nodes={n.attrib["id"]:local(float(n.attrib["lon"]),float(n.attrib["lat"])) for n in doc.findall("node")}
bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.render.engine="CYCLES";s.cycles.samples=10
s.render.resolution_x=1000;s.render.resolution_y=600;s.render.resolution_percentage=75
s.unit_settings.system="METRIC";s.world.color=(.52,.68,.84)
def material(name,c):
    v=bpy.data.materials.new(name);v.use_nodes=True
    p=v.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value=(*c,1);p.inputs["Roughness"].default_value=.82
    return v
wall=material("OSM_walls_NO_photo_facade",(.76,.72,.66))
roof=material("OSM_roofs_NO_photogrammetry",(.45,.34,.26))
ground=material("PNOA_real_ortho_ground",(.58,.59,.57))
ortho=D/"PNOA_ground.jpg"
if ortho.exists():
    n=ground.node_tree.nodes.new("ShaderNodeTexImage")
    n.image=bpy.data.images.load(str(ortho.resolve()),check_existing=True);n.image.pack()
    ground.node_tree.links.new(n.outputs["Color"],ground.node_tree.nodes.get("Principled BSDF").inputs["Base Color"])
x1,y1,x2,y2=info["bbox_local_m"]
me=bpy.data.meshes.new("PNOA_ground_mesh")
me.from_pydata([(x1,y1,-.1),(x2,y1,-.1),(x2,y2,-.1),(x1,y2,-.1)],[],[(0,1,2,3)])
me.update();uv=me.uv_layers.new(name="geographic_UVs")
for face in me.polygons:
 for li in face.loop_indices:
    pos=me.vertices[me.loops[li].vertex_index].co
    uv.data[li].uv=((pos.x-x1)/(x2-x1),(pos.y-y1)/(y2-y1))
ob=bpy.data.objects.new("ENV_Real_PNOA_Aerial_Not_Street_Facades",me)
s.collection.objects.link(ob);me.materials.append(ground)
wallvs=[];wallfs=[];roofvs=[];rooff=[];total=0;measured=0;skipped=0
cadastre_matches={};catastro_parts_drawn=0;catastro_replaced_osm=0;catastro_sha=None
source_gml=D/"catastro_building_parts.gml"
overlay_file=D/"catastro_building_parts.json"
# Optional official-source upgrade: no GML, no override. Never trust a loose
# JSON geometry file without its exact original official WFS bytes.
cadastre_source_count=0
cadastre_coverage_complete=False
if overlay_file.exists():
    source=json.loads(overlay_file.read_text(encoding="utf-8"))
    if (source.get("source")!="DG_CATASTRO_INSPIRE_BU_BUILDINGPART" or
        source.get("crs")!="EPSG:3857_local" or source.get("height_is_surveyed") is not False or
        source.get("height_method")!="official_floors_times_3m_ESTIMATE"):
        raise RuntimeError("Invalid cadastral provenance/height semantics")
    if source.get("schema")=="neurocity.catastro-building-parts.v1":
        if not source_gml.exists():raise RuntimeError("Original official GML required")
        if (not source.get("source_url","").startswith("https://ovc.catastro.meh.es/INSPIRE/wfsBU.aspx?") or
            hashlib.sha256(source_gml.read_bytes()).hexdigest()!=source.get("source_sha256")):
            raise RuntimeError("Official single-tile GML hash missing/mismatch")
        catastro_sha=source["source_sha256"]
        cadastre_source_count=1
    elif source.get("schema")=="neurocity.catastro-building-grid.v2":
        source_tiles=source.get("source_tiles")
        if not isinstance(source_tiles,list) or not 1<=len(source_tiles)<=9:
            raise RuntimeError("Missing bounded 3x3 official source grid")
        tile_names=set();digests=[]
        for tile in source_tiles:
            ident=tile.get("tile_id");name=tile.get("gml_name")
            if (not isinstance(ident,str) or not re.fullmatch(r"r[0-2]_c[0-2]",ident)
                or name!=ident+".gml" or ident in tile_names):
                raise RuntimeError("Unsafe or duplicated grid source tile")
            tile_names.add(ident)
            original=D/"catastro_grid_tiles"/name
            if (not original.is_file() or
                not str(tile.get("url","")).startswith("https://ovc.catastro.meh.es/INSPIRE/wfsBU.aspx?") or
                hashlib.sha256(original.read_bytes()).hexdigest()!=tile.get("sha256")):
                raise RuntimeError("Missing/unverified official grid tile")
            digests.append(tile["sha256"])
        cadastre_source_count=len(source_tiles)
        cadastre_coverage_complete=(cadastre_source_count==9)
        if source.get("coverage_complete") is not cadastre_coverage_complete:
            raise RuntimeError("Claimed grid completeness inconsistent with bytes")
        catastro_sha=hashlib.sha256("".join(sorted(digests)).encode()).hexdigest()
    else:
        raise RuntimeError("Unsupported official cadastral volume schema")
    for building in source.get("matched",[]):
        name=building.get("osm_way_id")
        if not isinstance(name,str) or not name.isdigit() or name in cadastre_matches:
            raise RuntimeError("Duplicate or invalid OSM match in cadastre")
        sections=building.get("sections")
        if not isinstance(sections,list) or not 1<=len(sections)<=75:
            raise RuntimeError("Invalid official multi-volume sections")
        prepared=[]
        for section in sections:
            floors=section.get("floors");height=section.get("height_estimated_m")
            pts=section.get("ring")
            if (type(floors) is not int or not 1<=floors<=30 or
                height!=floors*3.0 or not isinstance(pts,list) or not 3<=len(pts)<=160 or
                any(not isinstance(pt,list) or len(pt)!=2 or
                    not all(isinstance(v,(float,int)) and math.isfinite(v) for v in pt) or
                    not (x1-30<=pt[0]<=x2+30 and y1-30<=pt[1]<=y2+30) for pt in pts)):
                raise RuntimeError("Unsafe or unverified Catastro ring/height")
            prepared.append(([(float(a),float(b)) for a,b in pts],height))
        cadastre_matches[name]=prepared

def append_building(pts,h):
    # Keep authentic source footprint vertices. Non-convex OSM and Catastro
    # roof N-gons must be tessellated rather than rendered as arbitrary fans.
    if len(pts)<3:raise RuntimeError("Insufficient footprint vertices")
    area=sum(pts[i][0]*pts[(i+1)%len(pts)][1]-pts[(i+1)%len(pts)][0]*pts[i][1] for i in range(len(pts)))
    if abs(area)<3:raise RuntimeError("Invalid building footprint area")
    if area<0:pts=list(reversed(pts))
    k=len(wallvs)
    for x,y in pts:wallvs.extend([(x,y,0),(x,y,h)])
    for j in range(len(pts)):
        a=k+2*j;b=k+2*((j+1)%len(pts));wallfs.append((a,b,b+1,a+1))
    polygon=[Vector((x,y,h)) for x,y in pts]
    roof_triangles=tessellate_polygon([polygon])
    if len(roof_triangles)<1:raise RuntimeError("Building roof cannot be tessellated")
    for tri in roof_triangles:
        # Blender 4.0 returns vertex indices; previous Blender APIs also
        # documented Vector triangles. Handle either without silent wrong roofs.
        vertices=[polygon[v] if isinstance(v,int) else v for v in tri]
        if len(vertices)!=3:raise RuntimeError("Non-triangular tessellation")
        q=len(roofvs);roofvs.extend([(v.x,v.y,v.z) for v in vertices])
        rooff.append((q,q+1,q+2))
def height(tags):
    try:
        val=float(re.sub(r"[^0-9.]","",tags.get("height","")))
        if 2<=val<=150:return val,True
    except ValueError:pass
    try:
        levels=int(float(tags.get("building:levels","3")))
        return (min(max(levels,1),30)*3.0,False)
    except ValueError:return (9.0,False)
for way in doc.findall("way"):
    tags={t.attrib["k"]:t.attrib["v"] for t in way.findall("tag")}
    if tags.get("building") in (None,"no"):continue
    refs=[nd.attrib["ref"] for nd in way.findall("nd")]
    if len(refs)<4 or refs[0]!=refs[-1] or any(n not in nodes for n in refs):
        skipped+=1;continue
    pts=[nodes[n] for n in refs[:-1]]
    area=sum(pts[i][0]*pts[(i+1)%len(pts)][1]-pts[(i+1)%len(pts)][0]*pts[i][1] for i in range(len(pts)))
    if abs(area)<3:skipped+=1;continue
    if area<0:pts.reverse()
    override=cadastre_matches.get(way.attrib["id"])
    if override:
        for ring,h_estimated in override:append_building(ring,h_estimated)
        catastro_parts_drawn+=len(override)
        catastro_replaced_osm+=1
    else:
        h,realheight=height(tags);measured+=int(realheight)
        append_building(pts,h)
    total+=1
def add(name,verts,faces,mat):
    if not faces:return
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    o=bpy.data.objects.new(name,mesh);s.collection.objects.link(o);mesh.materials.append(mat)
add("OSM_Real_Building_Walls_UNTEXTURED",wallvs,wallfs,wall)
add("OSM_Real_Building_Roofs",roofvs,rooff,roof)
# Additional OSM way geometry: road/pedestrian corridor centerlines come from the real map.
# Width is a design estimate unless OSM has explicit width; no claim of surveyed kerbs.
roadverts={k:[] for k in ("vehicular","pedestrian","service")}
roadfaces={k:[] for k in roadverts}
roadcounts={k:0 for k in roadverts}
def surface_width(tags, kind):
    try:
        w=float(re.sub(r"[^0-9.]","",tags.get("width","")))
        if .8<=w<=35:return w
    except (ValueError,TypeError):pass
    return 8.5 if kind=="vehicular" else (5.0 if kind=="pedestrian" else 4.2)
for way in doc.findall("way"):
    tags={t.attrib["k"]:t.attrib["v"] for t in way.findall("tag")}
    highway=tags.get("highway")
    if not highway or tags.get("area")=="yes":continue
    if highway in ("motorway","trunk","primary","secondary","tertiary","unclassified","residential","living_street"):
        group="vehicular"
    elif highway in ("footway","pedestrian","path","steps","cycleway"):
        group="pedestrian"
    elif highway in ("service",):group="service"
    else:continue
    refs=[q.attrib["ref"] for q in way.findall("nd")]
    pts=[nodes[r] for r in refs if r in nodes]
    if len(pts)<2:continue
    width=surface_width(tags,group)
    ybase=.015 if group=="vehicular" else (.03 if group=="pedestrian" else .018)
    for j in range(len(pts)-1):
        a,b=pts[j],pts[j+1]
        dx,dy=b[0]-a[0],b[1]-a[1]
        L=math.hypot(dx,dy)
        if L<.5:continue
        nx,ny=-dy/L*width*.5,dx/L*width*.5
        v=roadverts[group];faces=roadfaces[group];base=len(v)
        v.extend([(a[0]+nx,a[1]+ny,ybase),(a[0]-nx,a[1]-ny,ybase),
                  (b[0]-nx,b[1]-ny,ybase),(b[0]+nx,b[1]+ny,ybase)])
        faces.append((base,base+1,base+2,base+3))
        roadcounts[group]+=1
roadmat={
 "vehicular":material("OSM_Real_Road_Centerlines_width_estimated",(.24,.245,.25)),
 "pedestrian":material("OSM_Real_Pedestrian_Centerlines_width_estimated",(.74,.70,.61)),
 "service":material("OSM_Service_Road",(.39,.37,.35))
}
for k in roadverts:
    if not roadfaces[k]:continue
    # Blender Z vertical. export to GLB uses Y up, same as building meshes.
    add("OSM_REAL_"+k+"_ways_not_surveyed_width",roadverts[k],roadfaces[k],roadmat[k])
print("Road OSM segments",roadcounts,flush=True)

if total==0:raise RuntimeError("NO REAL OSM BUILDING FOOTPRINTS RECEIVED; abort")
bpy.ops.object.light_add(type="SUN",location=(-45,20,180))
sun=bpy.context.object;sun.data.energy=2.1;sun.rotation_euler=(.55,-.25,-.25)
bpy.ops.object.camera_add(location=(80,-270,235))
camera=bpy.context.object
camera.rotation_euler=(Vector((0,0,0))-camera.location).to_track_quat("-Z","Y").to_euler()
camera.data.lens=30;s.camera=camera
bpy.ops.wm.save_as_mainfile(filepath=str((O/"Alicante_REAL_OSM_PNOA.blend").resolve()))
bpy.ops.export_scene.gltf(filepath=str((O/"Alicante_REAL_OSM_PNOA.glb").resolve()),export_format="GLB")
# Visual QA render is a separate optional workflow step, never blocks successful GLB export.
result={"real_osm_buildings":total,"heights_directly_measured":measured,"omitted":skipped,"road_segments_from_OSM":roadcounts,
"pnoa_ground":info["real_orthophoto"],"facades_photogrammetric":False,
"private_avatar_included":False,"blender_version":list(bpy.app.version),
"cadastre_building_parts_geometry":catastro_parts_drawn,
"cadastre_original_osm_footprints_replaced":catastro_replaced_osm,
"cadastre_source_gml_sha256":catastro_sha,
"cadastre_verified_source_tiles":cadastre_source_count,
"cadastre_coverage_complete":cadastre_coverage_complete,
"cadastre_floor_based_height_not_measured":True,
"original_osm_file_modified":False,
"roof_triangulation":"Blender tessellate_polygon nonconvex_safe"}
(O/"QA_source_report.json").write_text(json.dumps(result,indent=2))
print("SCENE QA",json.dumps(result),flush=True)
