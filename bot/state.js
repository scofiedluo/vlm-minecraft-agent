const { isHostile } = require('./entities')

function getTimeOfDay(bot) {
  if (!bot.time || typeof bot.time.timeOfDay !== 'number') return 'unknown'
  const t = bot.time.timeOfDay
  return t >= 0 && t < 13000 ? 'day' : 'night'
}

function toDirLabel(dx, dz) {
  const angle = Math.atan2(dx, dz)
  const dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
  const idx = Math.round(((angle + Math.PI) / (2 * Math.PI)) * 8) % 8
  return dirs[idx]
}

function summarizeNearbyBlocks(bot, radius = 8, limit = 16) {

  const map = new Map()
  const pos = bot.entity?.position
  if (!pos) return []

  for (let dx = -radius; dx <= radius; dx += 1) {
    for (let dy = -3; dy <= 8; dy += 1) {

      for (let dz = -radius; dz <= radius; dz += 1) {
        const p = pos.offset(dx, dy, dz)
        const block = bot.blockAt(p)
        if (!block || !block.name || block.name === 'air') continue
        const key = block.name
        const dist = Math.sqrt(dx * dx + dy * dy + dz * dz)
        const existing = map.get(key)
        if (!existing) {
          map.set(key, {
            name: key,
            count: 1,
            nearest: { x: block.position.x, y: block.position.y, z: block.position.z },
            distance: Number(dist.toFixed(2)),
            dir: toDirLabel(dx, dz),
          })
        } else {
          existing.count += 1
          if (dist < existing.distance) {
            existing.nearest = { x: block.position.x, y: block.position.y, z: block.position.z }
            existing.distance = Number(dist.toFixed(2))
            existing.dir = toDirLabel(dx, dz)
          }
        }
      }
    }
  }

  return Array.from(map.values())
    .sort((a, b) => a.distance - b.distance)
    .slice(0, limit)
}

function summarizeNearbyEntities(bot, radius = 24) {
  const pos = bot.entity?.position
  if (!pos) return []

  return Object.values(bot.entities)
    .filter((e) => e && e !== bot.entity && e.position)
    .map((e) => {
      const dx = e.position.x - pos.x
      const dz = e.position.z - pos.z
      const dy = e.position.y - pos.y
      const distance = Math.sqrt(dx * dx + dy * dy + dz * dz)
      return {
        name: e.name || e.displayName || e.type || 'unknown',
        kind: isHostile(e) ? 'hostile' : (e.type === 'player' ? 'player' : 'passive'),

        distance,
        dir: toDirLabel(dx, dz),
      }
    })
    .filter((e) => e.distance <= radius)
    .sort((a, b) => a.distance - b.distance)
    .slice(0, 20)
    .map((e) => ({ ...e, distance: Number(e.distance.toFixed(2)) }))
}

function getInventory(bot) {
  if (!bot.inventory || !Array.isArray(bot.inventory.items())) return []
  const grouped = new Map()
  for (const item of bot.inventory.items()) {
    const prev = grouped.get(item.name) || 0
    grouped.set(item.name, prev + item.count)
  }
  return Array.from(grouped.entries()).map(([name, count]) => ({ name, count }))
}

function getStateSnapshot(bot, lastSkillResult = null) {
  const entity = bot.entity
  return {
    ok: true,
    tick: bot.time?.age || 0,
    health: bot.health ?? null,
    food: bot.food ?? null,
    position: entity
      ? {
          x: Number(entity.position.x.toFixed(2)),
          y: Number(entity.position.y.toFixed(2)),
          z: Number(entity.position.z.toFixed(2)),
        }
      : null,
    yaw: entity ? Number(entity.yaw.toFixed(4)) : 0,
    pitch: entity ? Number(entity.pitch.toFixed(4)) : 0,
    onGround: entity ? Boolean(entity.onGround) : false,
    timeOfDay: getTimeOfDay(bot),
    lightLevel: entity ? bot.blockAt(entity.position)?.light ?? null : null,
    inventory: getInventory(bot),
    heldItem: bot.heldItem?.name || null,
    nearbyBlocks: summarizeNearbyBlocks(bot),
    nearbyEntities: summarizeNearbyEntities(bot),
    lastSkillResult,
  }
}

module.exports = {
  getStateSnapshot,
}
