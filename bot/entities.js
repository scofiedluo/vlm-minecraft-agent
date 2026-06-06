const HOSTILE_NAMES = new Set([
  'zombie', 'husk', 'drowned', 'zombie_villager',
  'skeleton', 'stray', 'wither_skeleton',
  'creeper', 'spider', 'cave_spider', 'witch',
  'enderman', 'slime', 'magma_cube', 'phantom',
  'pillager', 'vindicator', 'evoker', 'ravager',
  'blaze', 'ghast', 'silverfish', 'endermite', 'vex',
  'zombified_piglin', 'piglin', 'piglin_brute', 'hoglin', 'zoglin',
  'warden', 'breeze', 'bogged',
])

function isHostile(entity) {
  if (!entity) return false
  if (entity.kind && /hostile/i.test(entity.kind)) return true
  return HOSTILE_NAMES.has(entity.name)
}

module.exports = {
  HOSTILE_NAMES,
  isHostile,
}
