/** Local owner-only worldmaster activation. The query never bypasses asset integrity. */
export function wantsRecoveredWorldmaster(search){
 if(typeof search!=='string'||search.length>2048)throw new TypeError('Invalid local query');
 return new URLSearchParams(search.startsWith('?')?search.slice(1):search).get('worldmaster')==='1';
}
export function shouldLoadOwnerArchive(publicPreview,search){
 if(typeof publicPreview!=='boolean')throw new TypeError('Invalid preview flag');
 return !publicPreview && wantsRecoveredWorldmaster(search);
}
