function getSafetySignal(bot) {
  const health = bot.health ?? 20
  if (health <= 6) {
    return { danger: true, reason: 'low_health' }
  }

  const hostileNearby = Object.values(bot.entities)
    .filter((e) => e && e.type === 'mob' && e.position)
    .some((e) => bot.entity.position.distanceTo(e.position) <= 6)

  if (hostileNearby) {
    return { danger: true, reason: 'hostile_nearby' }
  }

  return { danger: false, reason: 'safe' }
}

module.exports = {
  getSafetySignal,
}
