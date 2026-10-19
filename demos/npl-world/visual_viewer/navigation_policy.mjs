/** Pure, testable fallback navigation policy. Public scenes never require a private avatar. */
export function nextCameraMode(current, hasAvatar) {
  if (!hasAvatar) return current === 'first' ? 'back' : 'first';
  return current === 'back' ? 'face' : current === 'face' ? 'first' : 'back';
}
export function canNavigate(city) { return Boolean(city); }
