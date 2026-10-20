#!/usr/bin/env python3
"""Produce physically modelled (4cm) Alicante Explanada mosaic 3D LOD asset.

Not a surveyed reconstruction: color palette/tessera scale from authoritative
UA + Alicante tourism material, while wave phase, mosaic placement, geometry and
micro-roughness are artist reconstructions. Outputs local-only previews (no deploy).
Dependencies: Python, numpy, pillow, trimesh. Deterministic by design.
"""
import argparse, hashlib, json, math, struct
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
import trimesh
from trimesh.visual.material import PBRMaterial
from trimesh.visual.texture import TextureVisuals

SIZE_M=4.0
TESSERA_M=0.04  # Universidad de Alicante, approximate dimensions
N=int(round(SIZE_M/TESSERA_M))
GROUT_M=0.0011  # interpretation; field measurement unavailable
SEED=20261020
CITATIONS=[
 'https://web.ua.es/es/actualidad-universitaria/documentos/docs-anteriores/2020/noviembre2020/ruta-geologica-alicante.pdf',
 'https://alicanteturismo.com/jardines/la-explanada-de-espana/',
 'https://www.alicantefilmoffice.com/localizacion/explanada-espana/',
]
PALETTE=np.asarray([(215,193,146),(145,69,60),(208,185,149),(31,48,62),
                    (220,195,159),(32,45,55)],dtype=float) # cream, red, black
GROUT=np.array([76,72,70],dtype=np.uint8)


def kind(x,z):
    # S-shaped wave arcs over a repeatable 4m-periodic patch. Unmeasured phase.
    arc=z + .55*math.sin((2*math.pi/SIZE_M)*x)
    band=round(SIZE_M/12.0,12) # 12 bands/patch, six-hue periodic sequence
    return int(math.floor((arc+1e-9)/band))%len(PALETTE)


def color_at(i,j,corner=0):
    x=(i+.5)*TESSERA_M
    z=(j+.5)*TESSERA_M
    pal=PALETTE[kind(x,z)]
    u=((i*73856093)^(j*19349663)^SEED)&0xffffffff
    rand=((u*1664525+1013904223)&0xffffffff)/0xffffffff
    grain=(rand-.5)*24
    variations=(-3,2,-1,3)
    return np.clip(pal+grain+variations[corner%4],0,255).astype(np.uint8)


def near_geometry():
    verts=[]; normals=[]; colors=[]; faces=[]
    # Face vertices are deliberately duplicated: top marble vs vertical cut faces.
    def face4(corners, normal, col):
        off=len(verts)
        verts.extend(corners)
        normals.extend([normal]*4)
        colors.extend([[int(v) for v in col]+[255]]*4)
        faces.extend(((off,off+1,off+2),(off,off+2,off+3)))
    for j in range(N):
      for i in range(N):
        x0=i*TESSERA_M+GROUT_M/2; x1=(i+1)*TESSERA_M-GROUT_M/2
        z0=j*TESSERA_M+GROUT_M/2; z1=(j+1)*TESSERA_M-GROUT_M/2
        # Mild individual tessera height variance, under 0.5 mm: stylized.
        h=.0036 + .00035*math.sin(i*12.9898+j*78.233)
        lo=.00035
        base=color_at(i,j).tolist()
        top=[(x0,h,z0),(x0,h,z1),(x1,h,z1),(x1,h,z0)]
        face4(top,(0,1,0),base)
        face4([(x0,lo,z1),(x0,lo,z0),(x0,h,z0),(x0,h,z1)],(-1,0,0),[int(v*.74) for v in base])
        face4([(x1,lo,z0),(x1,lo,z1),(x1,h,z1),(x1,h,z0)],(1,0,0),[int(v*.74) for v in base])
        face4([(x0,lo,z0),(x1,lo,z0),(x1,h,z0),(x0,h,z0)],(0,0,-1),[int(v*.70) for v in base])
        face4([(x1,lo,z1),(x0,lo,z1),(x0,h,z1),(x1,h,z1)],(0,0,1),[int(v*.70) for v in base])
    return (np.array(verts,dtype=np.float32),np.array(faces,dtype=np.int32),
            np.array(normals,dtype=np.float32),np.array(colors,dtype=np.uint8))


def export_near(path):
    verts,faces,normals,colors=near_geometry()
    mesh=trimesh.Trimesh(vertices=verts, faces=faces, vertex_normals=normals,
                         process=False, validate=False)
    mesh.visual.vertex_colors=colors
    # Add a dark mortar plane underneath *real separated tesserae*.
    base=trimesh.Trimesh(vertices=[(0,0,0),(0,0,SIZE_M),(SIZE_M,0,SIZE_M),(SIZE_M,0,0)],
                        faces=[(0,1,2),(0,2,3)],process=False)
    base.visual.vertex_colors=[80,74,69,255]
    scene=trimesh.Scene()
    scene.add_geometry(base,geom_name='real_grout_plane')
    scene.add_geometry(mesh,geom_name='tesserae_4cm_individual_extruded')
    path.write_bytes(scene.export(file_type='glb'))
    return dict(tesserae=N*N,marble_triangles=len(faces),source_approximate_tessera_m=TESSERA_M,
                bounds_m=[SIZE_M,SIZE_M],marble_vertices=len(verts),vertex_color=True)


def texture_image(pixels):
    if pixels%N:raise ValueError('texture resolution must be a multiple of tile count')
    image=Image.new('RGB',(pixels,pixels),tuple(GROUT.tolist()))
    d=ImageDraw.Draw(image)
    pitch=pixels//N
    gap=max(1,round(GROUT_M/TESSERA_M*pitch))
    # Bottom of PNG corresponds to near geometry +z; glTF UV corrected later.
    for j in range(N):
      for i in range(N):
        val=color_at(i,j)
        d.rectangle([i*pitch+gap,j*pitch+gap,(i+1)*pitch-gap,(j+1)*pitch-gap],
                    fill=tuple(int(x) for x in val))
        # Subtle marble grain lines. Procedurally synthetic—not photographic.
        if (i*11+j*13)%9==0 and pitch>=12:
            lighter=tuple(int(min(255,q+16)) for q in val)
            d.line([(i*pitch+gap+2,j*pitch+pitch//3),
                    ((i+1)*pitch-gap-2,j*pitch+2*pitch//3)],fill=lighter,width=1)
    return image


def export_far(path,texture_path,pixels):
    img=texture_image(pixels)
    img.save(texture_path,optimize=True)
    mat=PBRMaterial(baseColorTexture=img,metallicFactor=0.,roughnessFactor=.83,
                    doubleSided=True,baseColorFactor=[1.,1.,1.,1.])
    # glTF standard UV origin bottom-left, image Y originates top-left.
    uvs=np.array([[0,1],[0,0],[1,0],[1,1]],dtype=float)
    mesh=trimesh.Trimesh(vertices=[(0,.003,0),(0,.003,SIZE_M),
                                   (SIZE_M,.003,SIZE_M),(SIZE_M,.003,0)],
                          faces=[[0,1,2],[0,2,3]],process=False)
    mesh.visual=TextureVisuals(uv=uvs, material=mat)
    path.write_bytes(mesh.export(file_type='glb'))
    return {'far_triangles':2,'texture_pixels':pixels,'basecolor_png_sha256':hashlib.sha256(texture_path.read_bytes()).hexdigest()}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,default=Path('mosaic_out'))
    p.add_argument('--texture-pixels',type=int,default=2400)
    a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True)
    if a.texture_pixels%N or a.texture_pixels>4096:raise ValueError('texture-pixels multiple of 100 and <=4096')
    near=a.out/'explanada_4x4m_near_real_geometry.glb'
    far=a.out/'explanada_4x4m_far_textured.glb'
    texture=a.out/'explanada_diffuse_original_generated.png'
    n=export_near(near)
    f=export_far(far,texture,a.texture_pixels)
    report={'name':'Alicante Explanada 4mx4m 3D mosaic LOD experimental',
      'asset_type':'MODELLED_3D_TESSERAE_AND_TEXTURED_LOD_NOT_VERIFIED_IN_GAME',
      'original_master_overwritten':False,'publish_allowed':False,
      'original_historical_mosaic_geometry_measured':False,
      'visual_fidelity_approved':False,'world_master_georeference_verified':False,
      'vertical_datum_verified':False,'local_sample_origin_m':[0,0,0],
      'repeat_period_m':4.0,'does_not_include_real_businesses':True,
      'external_images_copied':False,'color_and_pattern':'interpretive from original photographs',
      'source_citations':CITATIONS,'near':n,'far':f,
      'files':{s.name:{'bytes':s.stat().st_size,'sha256':hashlib.sha256(s.read_bytes()).hexdigest()} for s in (near,far,texture)},
      'integration_requirements':['Load as OPTIONAL visual LOD over G19 after measured anchor','Disable G19 original mosaic mesh in replaced footprint to prevent Z fighting','Preserve physical grid authority, no collision overrides','Compare WebGL in original gameplay with reference photo before acceptance']}
    (a.out/'mosaic_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'tesserae':n['tesserae'],'near_triangles':n['marble_triangles'],
                      'far_triangles':f['far_triangles'],'files':report['files']},indent=2))

if __name__=='__main__':main()