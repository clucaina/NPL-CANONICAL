/** Optional local-only patch viewer. Does not alter authoritative G19 physics. */
export function createExplanadaLOD({scene, loader, nearUrl, farUrl, localAnchor, preview=false, projection}) {
  if (!scene || typeof scene.add !== 'function' || typeof scene.remove !== 'function') throw new TypeError('scene required');
  if (!loader || typeof loader.loadAsync !== 'function') throw new TypeError('GLTFLoader instance required');
  if (typeof nearUrl !== 'string' || typeof farUrl !== 'string') throw new TypeError('local source URLs required');
  if (!preview && (localAnchor?.verified !== true || localAnchor?.verticalDatumVerified !== true ||
      !Number.isFinite(localAnchor?.x) || !Number.isFinite(localAnchor?.z) ||
      !Number.isFinite(localAnchor?.y) || typeof projection !== 'function')) {
    throw new Error('G19 position and vertical datum verification required for real-world integration');
  }
  if (preview && localAnchor && (localAnchor.x !== 0 || localAnchor.z !== 0)) {
    throw new Error('Preview uses origin only; never invent real-world coordinates');
  }
  let active = null; let near = null; let far = null; let cancelled = false;
  const anchor = preview ? { x:0, y:0, z:0 } : projection(localAnchor);
  if (![anchor.x,anchor.y,anchor.z].every(Number.isFinite)) throw new Error('Invalid projection');
  async function preload(){
    [near,far] = await Promise.all([loader.loadAsync(nearUrl),loader.loadAsync(farUrl)]);
    if (cancelled) return;
    for (const model of [near,far]) {
      if (!model?.scene?.position?.set) throw new Error('Invalid glTF scene');
      model.scene.position.set(anchor.x,anchor.y,anchor.z);
    }
  }
  function update(distanceMeters){
    if(cancelled || !near || !far) return null;
    if(!Number.isFinite(distanceMeters) || distanceMeters<0) throw new RangeError('Invalid distance');
    const candidate = distanceMeters <= 11 ? near.scene : far.scene;
    if (active!==candidate){
      if(active) scene.remove(active);
      scene.add(candidate);
      active=candidate;
    }
    return distanceMeters <= 11 ? 'physical_4cm_tesserae' : 'textured_far_2_triangles';
  }
  function dispose(){
    cancelled=true;
    if(active){scene.remove(active);active=null;}
    // A caller sharing source texture objects retains ownership of GPU disposal.
  }
  return {preload,update,dispose,get ready(){return !!near && !!far && !cancelled;}};
}