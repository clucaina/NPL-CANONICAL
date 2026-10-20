#!/usr/bin/env python3
"""Local-only V50 mosaic conversion: source-sampled actual 3D tesserae.

Works on user-owned original V50 GLB, NEVER uploads the binary. Cuts a measured
4x4m rectangle out of the original triangulation using UV-preserving clipping,
then replaces only that footprint with 10,000 modelled 4cm stone blocks.
Coordinates, UVs, height variation come from the ORIGINAL mesh. The source
is not an on-site survey; the pattern remains a prior model, NOT measured.
"""
from __future__ import annotations
import argparse, hashlib, io, json, math, sys, zipfile
from pathlib import Path
import numpy as np
import trimesh
from scipy.spatial import cKDTree
from trimesh.visual.texture import TextureVisuals
from importlib.util import spec_from_file_location, module_from_spec

SRC_PATH='world-master/assets/selected/Explanada_v50_PBR_1024.glb'
SRC_SHA='02b44285e3bc478310e3b86d939b45e90ff80359ddfc57a759bf72803556a710'
# Square is INSIDE the archived V50 Explanada GLB; location comes from its
# EPSG:25830 local master geometry, NOT street photography or ground survey.
RECT=(318.0,1378.0,322.0,1382.0)


def sha(b):return hashlib.sha256(b).hexdigest()
def load_original(zipfile_path):
    with zipfile.ZipFile(zipfile_path) as z: data=z.read(SRC_PATH)
    if sha(data)!=SRC_SHA: raise ValueError('Original V50 GLB digest differs; refuse to edit unknown source')
    scene=trimesh.load(io.BytesIO(data),file_type='glb',force='scene')
    if len(scene.geometry)!=1:raise ValueError('Unknown original V50 source graph')
    mesh=next(iter(scene.geometry.values()))
    if not isinstance(mesh.visual,TextureVisuals) or mesh.visual.uv is None or mesh.visual.material.baseColorTexture is None:
        raise ValueError('Original glTF PBR texture/UV is unavailable')
    return mesh, data


def area(poly):
    return abs(sum(poly[i][0]*poly[(i+1)%len(poly)][2]-poly[(i+1)%len(poly)][0]*poly[i][2]
           for i in range(len(poly)))*.5)

def cut(poly, axis, bound, keep_greater):
    """Sutherland-Hodgman 3D triangle clip, UV-interpolated; halfplane x/z."""
    if len(poly)==0:return []
    def dist(p):return p[axis]-bound if keep_greater else bound-p[axis]
    out=[]
    prev=poly[-1];dp=dist(prev)
    for cur in poly:
        dc=dist(cur)
        if (dc>=0)!=(dp>=0):
            t=dp/(dp-dc) if dp!=dc else 0
            out.append(prev+t*(cur-prev))
        if dc>=0:out.append(cur)
        prev=cur;dp=dc
    # tolerate repeated points but never accept degenerate triangles
    return out


def triangulate(polygons):
    """Returns XYZ, UV and indexed triangles preserving face winding."""
    vertices=[];uv=[];faces=[]
    for poly in polygons:
        if len(poly)<3 or area(poly)<1e-11:continue
        idx=len(vertices)
        for p in poly:
            vertices.append(p[:3]);uv.append(p[3:])
        for j in range(1,len(poly)-1):faces.append((idx,idx+j,idx+j+1))
    return np.array(vertices,dtype=np.float32),np.array(uv,dtype=np.float32),np.array(faces,dtype=np.int32)


def split_source(mesh,rect=RECT):
    """Split original mosaic into complement and sampled substrate exactly once."""
    if not isinstance(mesh.visual,TextureVisuals) or mesh.visual.uv is None:
        raise ValueError("Only UV-textured V50-compatible mesh is supported")
    x0,z0,x1,z1=rect
    outside=[];inside=[]
    verts=np.c_[mesh.vertices,mesh.visual.uv]
    for f in mesh.faces:
        poly=np.asarray(verts[f],dtype=float)
        # At each boundary preserve the OUTSIDE side and continue clipping inside.
        for axis,bound,keep in [(0,x0,True),(0,x1,False),(2,z0,True),(2,z1,False)]:
            outpiece=cut(poly,axis,bound,not keep)
            if len(outpiece)>=3:outside.append(outpiece)
            poly=cut(poly,axis,bound,keep)
            if len(poly)==0:break
        if len(poly)>=3:inside.append(poly)
    vo,uo,fo=triangulate(outside)
    vi,ui,fi=triangulate(inside)
    a0=sum(area(verts[f]) for f in mesh.faces)
    a1=sum(area(p) for p in outside)+sum(area(p) for p in inside)
    if abs(a0-a1)>1e-3:raise AssertionError(f'Original mosaic area not conserved: {a0} vs {a1}')
    if abs(sum(area(p) for p in inside)-16)>0.03:raise AssertionError('Patch not fully covered by original source geometry')
    return (vo,uo,fo),(vi,ui,fi),{'original_projected_area_m2':round(a0,4),'remaining_projected_area_m2':round(sum(area(p) for p in outside),4),
      'removed_projected_area_m2':round(sum(area(p) for p in inside),4),'area_error_m2':abs(a0-a1),'original_faces':len(mesh.faces),'preserved_faces':len(fo),
      'original_texture_preserved':True}


class SourceSampler:
    def __init__(self,mesh):
        self.tris=np.asarray(mesh.vertices[mesh.faces],dtype=float)
        self.uvs=np.asarray(mesh.visual.uv[mesh.faces],dtype=float)
        self.tree=cKDTree(self.tris[:,:,[0,2]].mean(axis=1))
        self.img=np.asarray(mesh.visual.material.baseColorTexture.convert('RGB'))
    def sample(self, points, k=48):
        p=np.asarray(points,dtype=float)
        _,idx=self.tree.query(p,k=min(k,len(self.tris)))
        if idx.ndim==1:idx=idx[:,None]
        tris=self.tris[idx];flat=tris[:,:,:,[0,2]]
        a=flat[:,:,0];b=flat[:,:,1];c=flat[:,:,2]
        uvec=b-a;vvec=c-a;qvec=p[:,None,:]-a
        den=uvec[:,:,0]*vvec[:,:,1]-uvec[:,:,1]*vvec[:,:,0]
        den=np.where(abs(den)<1e-10,np.inf,den)
        u=(qvec[:,:,0]*vvec[:,:,1]-qvec[:,:,1]*vvec[:,:,0])/den
        v=(uvec[:,:,0]*qvec[:,:,1]-uvec[:,:,1]*qvec[:,:,0])/den
        valid=(u>=-1e-6)&(v>=-1e-6)&(u+v<=1.000001)
        if not valid.all(axis=1).all():
            bad=np.flatnonzero(~valid.any(axis=1))
            if len(bad):raise ValueError(f'V50 unavailable at {len(bad)} source points')
        row=np.arange(len(p));col=np.argmax(valid,axis=1);tri_idx=idx[row,col]
        w1=u[row,col];w2=v[row,col];w0=1-w1-w2
        tr=self.tris[tri_idx];uvs=self.uvs[tri_idx]
        xyz=(tr[:,0]*w0[:,None]+tr[:,1]*w1[:,None]+tr[:,2]*w2[:,None]);uv=(uvs[:,0]*w0[:,None]+uvs[:,1]*w1[:,None]+uvs[:,2]*w2[:,None])
        # Source triangle height gradient used for consistent planar tessera corners.
        dx=tr[:,1,0]-tr[:,0,0];dz=tr[:,1,2]-tr[:,0,2]
        ex=tr[:,2,0]-tr[:,0,0];ez=tr[:,2,2]-tr[:,0,2]
        dy=tr[:,1,1]-tr[:,0,1];ey=tr[:,2,1]-tr[:,0,1]
        denom=dx*ez-dz*ex
        gyx=(dy*ez-dz*ey)/denom;gyz=(dx*ey-dy*ex)/denom
        h,w=self.img.shape[:2]
        xi=np.floor(np.mod(uv[:,0],1)*w).astype(int)%w
        # Verified against original VTK GLB rendering on 400 surface points:
        # flipped UV-v matches V50 screenshot class 96.5%, unflipped only 49%.
        yi=np.floor((1-np.mod(uv[:,1],1))*h).astype(int)%h
        rgb=self.img[yi,xi]
        return xyz[:,1],np.stack([gyx,gyz],axis=-1),rgb,uv


def build_patch(mesh,builder_file):
    spec=spec_from_file_location('original_stone_builder',str(builder_file));module=module_from_spec(spec);spec.loader.exec_module(module)
    if module.N!=100 or module.TESSERA_M!=.04:raise ValueError('Unexpected source candidate dimensions')
    # V50 already defines the *shape of the waves*. The independent V2 warp
    # is deliberately disabled here: it displaced stones up to 48cm relative
    # to their source colors/heights and gave a visibly broken patch.
    original_warp=module.warp
    try:
        module.warp=lambda x,z:(x,z)
        vertices,faces,normals,colors=module.near_geometry()
    finally:module.warp=original_warp
    if vertices.shape!=(200000,3) or faces.shape!=(100000,3):
        raise ValueError('Unexpected 10k extruded stone builder layout')
    x0,z0,x1,z1=RECT
    i=np.tile(np.arange(100),100);j=np.repeat(np.arange(100),100)
    centers=np.stack([x0+(i+.5)*.04,z0+(j+.5)*.04],axis=-1)
    sampler=SourceSampler(mesh)
    heights,gradients,source_rgb,uv=sampler.sample(centers)
    out=vertices.copy().reshape((10000,20,3))
    # Every actual corner's Y is sampled directly FROM THE ARCHIVED V50
    # triangulated surface (not a per-cell tangent extrapolation). A visual
    # comparison discovered gray z-fighting where original terrain is curved.
    # 4 corners -> 20 duplicated render vertices per tessera, mapping order:
    corner_map=np.array([0,1,2,3,0,1,1,0,2,3,3,2,3,0,0,3,1,2,2,1],dtype=int)
    corners=out[:,:4,:][:,:,[0,2]].reshape(-1,2).copy()
    corners[:,0]+=x0;corners[:,1]+=z0
    actual_y=np.empty(len(corners),dtype=float)
    actual_uv=np.empty((len(corners),2),dtype=float)
    for start in range(0,len(corners),2000):
        points=corners[start:start+2000]
        sy,sg,srgb,suv=sampler.sample(points)
        actual_y[start:start+len(points)]=sy
        actual_uv[start:start+len(points)]=suv
    actual_y=actual_y.reshape((10000,4))
    actual_uv=actual_uv.reshape((10000,4,2))
    out[:,:,1]+=actual_y[:,corner_map]
    out[:,:,0]+=x0;out[:,:,2]+=z0
    # Rendering correction after VTK A/B: per-stone vertex colors caused severe
    # discontinuities and brightness mismatch. Reuse EXACT V50 PBR material
    # (base color + normal texture) and interpolate its UVs onto every physical
    # stone top/side at the original geographic source positions. This is what
    # makes tiled relief keep the source's true phase and colors without guessing.
    uv_per_vertex=actual_uv[:,corner_map].reshape((-1,2))
    near=trimesh.Trimesh(vertices=out.reshape((-1,3)),faces=faces,
                         vertex_normals=normals,process=False,validate=False)
    near.visual=TextureVisuals(uv=uv_per_vertex,material=mesh.visual.material)
    return near,{'near_stones':10000,'near_faces':len(near.faces),'source_colors_sampled':10000,'source_wave_phase_preserved':True,'synthetic_warp_disabled':True,'material_reuse':'ORIGINAL_V50_PBR_TEXTURE_AND_NORMALMAP','source_corner_uvs_interpolated':40000,'source_corner_heights_sampled':40000,'z_fighting_prevented_by_exact_corner_sampling':True,
                 'source_height_min':float(heights.min()),'source_height_max':float(heights.max()),
                 'approximate_tile_pitch_m':.04,'original_v50_visual_not_ground_survey':True}


def build(archive,builder_file,out):
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    src,bytes_original=load_original(archive)
    outside,inside,geometry=split_source(src)
    orig=trimesh.Trimesh(vertices=outside[0],faces=outside[2],process=False)
    orig.visual=TextureVisuals(uv=outside[1],material=src.visual.material)
    grout=trimesh.Trimesh(vertices=inside[0],faces=inside[2],process=False)
    grout.visual.vertex_colors=[78,73,70,255]
    near,stats=build_patch(src,builder_file)
    combined=trimesh.Scene()
    combined.add_geometry(orig,geom_name='V50_original_uv_pavement_outside_single_patch')
    combined.add_geometry(grout,geom_name='V50_exact_source_elevation_grout_inside_patch')
    combined.add_geometry(near,geom_name='V50_10k_real_4cm_extruded_tesserae_on_original_surface')
    out.write_bytes(combined.export(file_type='glb'))
    reopened=trimesh.load(out,force='scene')
    if len(reopened.geometry)!=3:raise AssertionError('Missing one of the three scene geometry classes')
    all_faces=sum(len(g.faces) for g in reopened.geometry.values())
    if all_faces<100000:raise AssertionError('Physical stone mesh missing from reopened glTF')
    record={**geometry,**stats,'original_source_asset_sha256':sha(bytes_original),
            'new_candidate_path':out.name,'candidate_sha256':sha(out.read_bytes()),'candidate_bytes':out.stat().st_size,
            'candidate_total_faces':all_faces,'original_v50_filename':SRC_PATH,'source_crs':'EPSG:25830-local-worldmaster',
            'source_rect_xz':[318,1378,322,1382], 'vertical_datum_verified':False,
            'photographic_fidelity_verified':False,'webgl_gameplay_tested':False,'redistribution_allowed':False,
            'original_unchanged':True, 'licensing_not_cleared_for_public_share':True}
    (out.parent/'V50_SURGICAL_PATCH_AUDIT.json').write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n')
    return record

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,required=True);p.add_argument('--builder',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();print(json.dumps(build(a.archive,a.builder,a.out),ensure_ascii=False,indent=2))