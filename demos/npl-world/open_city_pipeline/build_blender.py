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

# Physical positions sourced from mapped OSM tags. Dimensions and foliage
# remain illustrative: not surveyed, no ships invented, no fake marinas.
extra_counts={"pier_segments":0,"barrier_segments":0,"mapped_tree_nodes":0,
              "water_polygons":0,"scrub_polygons":0,
              "rounded_tree_canopy_lobes":0,"shrub_clusters_within_osm_polygon":0}
pierverts=[];pierfaces=[];fenceverts=[];fencefaces=[];waterverts=[];waterfaces=[]
scrubverts=[];scrubfaces=[];barkverts=[];barkfaces=[];leafverts=[];leaffaces=[]
bushverts=[];bushfaces=[]
piermat=material("OSM_mapped_piers_width_estimated",(.52,.49,.46))
fencemat=material("OSM_mapped_fences_height_estimated",(.29,.31,.31))
watermat=material("OSM_mapped_water_polygons_only",(.13,.31,.4))
leafmat=material("OSM_tree_positions_with_illustrative_foliage",(.23,.39,.24))
barkmat=material("OSM_tree_positions_with_illustrative_trunks",(.39,.27,.17))
scrubmat=material("OSM_mapped_scrub_polygons_only",(.31,.45,.29))
bushmat=material("OSM_scrub_mapped_region_round_bushes_illustrative",(.24,.40,.24))
def ellipsoid(verts,faces,center,radii,segments=10,rings=6):
    # Rounded foliage volume instead of the previous visual placeholder: a
    # square pyramid, which made every verified OSM tree look like Roblox.
    cx,cy,cz=center;rx,ry,rz=radii
    base=len(verts)
    for j in range(rings+1):
        v=math.pi*j/rings
        for k in range(segments):
            u=2*math.pi*k/segments
            verts.append((cx+rx*math.sin(v)*math.cos(u),
                          cy+ry*math.sin(v)*math.sin(u),
                          cz+rz*math.cos(v)))
    for j in range(rings):
        for k in range(segments):
            a=base+j*segments+k;b=base+j*segments+(k+1)%segments
            c=base+(j+1)*segments+k;d=base+(j+1)*segments+(k+1)%segments
            if j==0:faces.append((a,c,d))
            elif j==rings-1:faces.append((a,c,b))
            else:faces.append((a,c,d,b))
def inside_polygon(x,y,vertices):
    # Polygon shapes are actual mapped OSM areas. Individual bush placement
    # inside a polygon is artistic and not a surveyed shrub.
    hit=False;j=len(vertices)-1
    for i in range(len(vertices)):
        xi,yi=vertices[i];xj,yj=vertices[j]
        if (yi>y)!=(yj>y) and x<(xj-xi)*(y-yi)/(yj-yi)+xi:
            hit=not hit
        j=i
    return hit
def strip_geom(targetv,targetf,a,b,width,z0,z1):
    dx,dy=b[0]-a[0],b[1]-a[1]
    L=math.hypot(dx,dy)
    if L<.5:return False
    nx,ny=-dy/L*width*.5,dx/L*width*.5
    base=len(targetv)
    for x,y in [(a[0]+nx,a[1]+ny),(a[0]-nx,a[1]-ny),
                (b[0]-nx,b[1]-ny),(b[0]+nx,b[1]+ny)]:
        targetv.extend([(x,y,z0),(x,y,z1)])
    targetf.extend([(base+1,base+3,base+5,base+7),
                    (base,base+2,base+4,base+6),
                    (base,base+1,base+3,base+2),
                    (base+4,base+5,base+7,base+6)])
    return True
def flat_mapped_area(verts,faces,pts,height):
    if len(pts)<4 or pts[0]!=pts[-1]:return False
    pts=pts[:-1]
    if len(pts)<3:return False
    base=len(verts)
    verts.extend((x,y,height) for x,y in pts)
    faces.append(tuple(range(base,base+len(pts))))
    return True
for way in doc.findall("way"):
    tags={t.attrib["k"]:t.attrib["v"] for t in way.findall("tag")}
    refs=[q.attrib["ref"] for q in way.findall("nd")]
    if not refs or any(ref not in nodes for ref in refs):continue
    pts=[nodes[ref] for ref in refs]
    if tags.get("man_made") in ("pier","quay","breakwater"):
        # Width from OSM when present; otherwise explicit aesthetic estimate.
        width=surface_width(tags,"service")
        for a,b in zip(pts,pts[1:]):
            if strip_geom(pierverts,pierfaces,a,b,width,.07,.30):
                extra_counts["pier_segments"]+=1
    if tags.get("barrier") in ("fence","wall","guard_rail","handrail"):
        for a,b in zip(pts,pts[1:]):
            if strip_geom(fenceverts,fencefaces,a,b,.09,.03,1.12):
                extra_counts["barrier_segments"]+=1
    if tags.get("natural")=="water" or tags.get("water") in ("sea","basin","harbour"):
        extra_counts["water_polygons"]+=int(flat_mapped_area(waterverts,waterfaces,pts,.045))
    if tags.get("natural")=="scrub" or tags.get("landuse") in ("grass","forest"):
        valid=flat_mapped_area(scrubverts,scrubfaces,pts,.025)
        extra_counts["scrub_polygons"]+=int(valid)
        if valid:
            # Only a few procedural shrubs per mapped landuse polygon. Hard
            # limit avoids turning giant polygons into tens of thousands of props.
            poly=pts[:-1]
            minx,maxx=min(p[0] for p in poly),max(p[0] for p in poly)
            miny,maxy=min(p[1] for p in poly),max(p[1] for p in poly)
            for ix in range(min(50,math.ceil((maxx-minx)/4.8))):
                if extra_counts["shrub_clusters_within_osm_polygon"]>=240:break
                for iy in range(min(50,math.ceil((maxy-miny)/4.8))):
                    if extra_counts["shrub_clusters_within_osm_polygon"]>=240:break
                    xx=minx+(ix+.5)*4.8;yy=miny+(iy+.5)*4.8
                    if not inside_polygon(xx,yy,poly):continue
                    seed=(ix*11+iy*17)%13
                    ellipsoid(bushverts,bushfaces,(xx,yy,.70),
                              (.67+seed*.021,.72+seed*.015,.54))
                    extra_counts["shrub_clusters_within_osm_polygon"]+=1
for n in doc.findall("node"):
    tags={t.attrib["k"]:t.attrib["v"] for t in n.findall("tag")}
    if tags.get("natural")!="tree":continue
    pos=nodes.get(n.attrib.get("id"))
    if pos is None:continue
    x,y=pos
    extra_counts["mapped_tree_nodes"]+=1
    # Every OSM tree point stays georeferenced. Height, trunk and 3D lobe
    # shapes remain illustrative (NOT a survey or a species identification).
    serial=int(n.attrib.get("id","0"))%97
    tall=4.6+serial*.021
    radius=.16+serial*.00035
    stem=tall*.60
    base=len(barkverts);segments=9
    for k in range(segments):
        a=2*math.pi*k/segments
        barkverts.extend([(x+radius*math.cos(a),y+radius*math.sin(a),.12),
                          (x+radius*.83*math.cos(a),y+radius*.83*math.sin(a),stem)])
    for k in range(segments):
        v=base+k*2;v2=base+((k+1)%segments)*2
        barkfaces.append((v,v2,v2+1,v+1))
    ellipsoid(leafverts,leaffaces,(x,y,tall*.82),(1.65,1.45,1.55))
    ellipsoid(leafverts,leaffaces,(x-0.72,y+.25,tall*.73),(1.15,1.16,1.12))
    ellipsoid(leafverts,leaffaces,(x+.68,y-.19,tall*.73),(1.20,1.13,1.14))
    extra_counts["rounded_tree_canopy_lobes"]+=3
add("OSM_REAL_pier_segments_width_illustrative",pierverts,pierfaces,piermat)
add("OSM_REAL_barrier_segments_height_illustrative",fenceverts,fencefaces,fencemat)
add("OSM_REAL_water_polygon_source_only",waterverts,waterfaces,watermat)
add("OSM_REAL_scrub_boundary_flat_illustrative",scrubverts,scrubfaces,scrubmat)
add("OSM_REAL_scrub_polygon_bush_cluster_illustrative",bushverts,bushfaces,bushmat)
add("OSM_REAL_tree_locations_trunk_illustrative",barkverts,barkfaces,barkmat)
add("OSM_REAL_tree_locations_canopy_illustrative",leafverts,leaffaces,leafmat)
print("Coastal and greenery OSM-bound visual layer",extra_counts,flush=True)

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
result={"real_osm_buildings":total,"heights_directly_measured":measured,"omitted":skipped,"road_segments_from_OSM":roadcounts,"coastal_and_vegetation_visual_objects":extra_counts,"actual_boat_models":0,
"pnoa_ground":info["real_orthophoto"],"facades_photogrammetric":False,
"private_avatar_included":False,"blender_version":list(bpy.app.version)}
(O/"QA_source_report.json").write_text(json.dumps(result,indent=2))
print("SCENE QA",json.dumps(result),flush=True)
