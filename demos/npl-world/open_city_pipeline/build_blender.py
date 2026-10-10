#!/usr/bin/env python3
"""Blender CPU: real OSM footprints + available PNOA orthophoto ground. NO invented landmark."""
import bpy, math, json, re, xml.etree.ElementTree as ET
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
    h,realheight=height(tags);measured+=int(realheight)
    k=len(wallvs)
    for x,y in pts:wallvs.extend([(x,y,0),(x,y,h)])
    for j in range(len(pts)):
        a=k+2*j;b=k+2*((j+1)%len(pts));wallfs.append((a,b,b+1,a+1))
    k=len(roofvs);roofvs.extend([(x,y,h) for x,y in pts])
    rooff.append(tuple(range(k,k+len(pts))));total+=1
def add(name,verts,faces,mat):
    if not faces:return
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    o=bpy.data.objects.new(name,mesh);s.collection.objects.link(o);mesh.materials.append(mat)
add("OSM_Real_Building_Walls_UNTEXTURED",wallvs,wallfs,wall)
add("OSM_Real_Building_Roofs",roofvs,rooff,roof)
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
result={"real_osm_buildings":total,"heights_directly_measured":measured,"omitted":skipped,
"pnoa_ground":info["real_orthophoto"],"facades_photogrammetric":False,
"private_avatar_included":False,"blender_version":list(bpy.app.version)}
(O/"QA_source_report.json").write_text(json.dumps(result,indent=2))
print("SCENE QA",json.dumps(result),flush=True)
