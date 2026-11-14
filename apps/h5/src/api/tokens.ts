export type Identity = 'public' | 'visitor' | 'staff'
const keys = { visitor: 'shuke.visitor.token', staff: 'shuke.staff.token' } as const
export function getToken(identity: Identity) { return identity === 'public' ? '' : localStorage.getItem(keys[identity]) || '' }
export function setToken(identity: Exclude<Identity, 'public'>, token: string) { localStorage.setItem(keys[identity], token) }
export function clearToken(identity: Exclude<Identity, 'public'>) { localStorage.removeItem(keys[identity]) }
