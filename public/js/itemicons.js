// Item pictures rendered from the real models where there is one (the grenade, the duck, the smoke bomb, the popper,
// the reverse card, the instant camera, the calculator, the goggles); the drawn ones (medkit, shield bubble, bubble wand)
// stay drawn. Cached like every other icon.
import { ITEMS } from '/shared/weapons.js';
import { weaponIcon, objIcon, itemIcon } from './icons.js';
import { buildProjectile } from './models.js';
import { instantCamera, calculator, lcdTexture, nvGoggles } from './gearmodels.js';

const GEAR = { camera: () => instantCamera(), quiz: () => calculator(lcdTexture(['80085', ''])), nvg: () => nvGoggles() };
export function itemPic(id, skin) {
  const it = ITEMS[id];
  if (!it) return itemIcon(id);
  try {
    let u = '';
    if (it.w) u = weaponIcon(it.w, skin);
    else if (it.proj) u = objIcon('item:' + id, () => { const g = buildProjectile(it.proj); g.rotation.set(0.4, -0.7, 0); g.scale.setScalar(3); return g; });
    else if (GEAR[id]) u = objIcon('item:' + id, () => { const g = GEAR[id](); g.rotation.set(0.3, -0.6, 0); return g; });
    return u || itemIcon(id);
  } catch (e) { return itemIcon(id); }
}
