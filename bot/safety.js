const { isHostile } = require('./entities')

function getSafetySignal(bot) {
  const health = bot.health ?? 20
  if (health <= 6) {
    return { danger: true, reason: 'low_health' }
  }

  const pos = bot.entity?.position
  const hostileNearby = pos && Object.values(bot.entities)
    .filter((e) => e && e.position && isHostile(e))
    .some((e) => pos.distanceTo(e.position) <= 6)

  if (hostileNearby) {
    return { danger: true, reason: 'hostile_nearby' }
  }

  return { danger: false, reason: 'safe' }
}


module.exports = {
  getSafetySignal,
}
