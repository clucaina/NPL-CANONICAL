"""Conservative official-only building volumes missing from the OSM base.

A verified Catastro BU footprint that is safely distant from ANY OSM building
may supplement, not replace, the navigable map. Never publish GML, parcel IDs,
addresses, owners or source building identifiers.
"""
import math

from shapely.geometry import box
from shapely.strtree import STRtree

from catastro_parts import R

CLEARANCE_M=4.0
BOUNDARY_MARGIN_M=3.0
MAX_NATIVE_PARTS=350
MIN_STANDALONE_AREA_M2=20

def collect_native_parts(parts,buildings,origin,lonlat_bbox,max_parts=MAX_NATIVE_PARTS):
    if (not isinstance(max_parts,int) or max_parts<0 or max_parts>MAX_NATIVE_PARTS):
        raise ValueError('Unsafe native geometry budget')
    west,south,east,north=lonlat_bbox
    limits=box(
        R*math.radians(west)-origin[0]+BOUNDARY_MARGIN_M,
        R*math.log(math.tan(math.pi/4+math.radians(south)/2))-origin[1]+BOUNDARY_MARGIN_M,
        R*math.radians(east)-origin[0]-BOUNDARY_MARGIN_M,
        R*math.log(math.tan(math.pi/4+math.radians(north)/2))-origin[1]-BOUNDARY_MARGIN_M
    )
    osm_polys=[p for _,p in buildings]
    osm_tree=STRtree(osm_polys) if osm_polys else None
    eligible=[]
    stats={'candidate_official_parts':len(parts),'outside_public_city_bounds':0,
           'too_small':0,'near_or_overlapping_osm':0,
           'overlapping_other_official_sections':0,'render_budget_deferred':0}
    for part in parts:
        g=part['poly']
        if g.area<MIN_STANDALONE_AREA_M2:
            stats['too_small']+=1;continue
        if not limits.covers(g):
            stats['outside_public_city_bounds']+=1;continue
        if osm_tree is not None:
            search=g.buffer(CLEARANCE_M)
            if any(osm_polys[int(i)].intersects(search) for i in osm_tree.query(search)):
                stats['near_or_overlapping_osm']+=1;continue
        eligible.append(part)
    # Official BU may represent stacked storeys with overlapping footprints.
    # Reject *all* sections with substantial area overlap; do not draw false
    # double roofs or stacked opaque towers.
    geo=[v['poly'] for v in eligible]
    tree=STRtree(geo) if geo else None
    forbidden=set()
    for i,g in enumerate(geo):
        for index in tree.query(g):
            j=int(index)
            if i>=j:continue
            other=geo[j]
            intersection=g.intersection(other).area
            if intersection>min(g.area,other.area)*.025:
                forbidden.update((i,j))
    stats['overlapping_other_official_sections']=len(forbidden)
    selected=[part for i,part in enumerate(eligible) if i not in forbidden]
    # Stable, bounded priority around the playable Explanada. Full-city
    # streaming must eventually replace this local draw budget.
    selected.sort(key=lambda v:(
        (v['poly'].centroid.x+10.664)**2+(v['poly'].centroid.y-113.546)**2,
        -v['poly'].area,
        v['poly'].wkb_hex
    ))
    stats['render_budget_deferred']=max(0,len(selected)-max_parts)
    selected=selected[:max_parts]
    result=[]
    for item in selected:
        ring=[[round(x,4),round(y,4)] for x,y in list(item['poly'].exterior.coords)[:-1]]
        result.append({'floors':item['floors'],
           'height_estimated_m':item['floors']*3.,
           'ring':ring})
    stats['accepted_native_parts']=len(result)
    stats['rendering_limit']=max_parts
    stats['metric_height_verified']=False
    return result,stats
