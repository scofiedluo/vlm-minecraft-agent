const { isHostile } = require('../entities')

async function attackNearestSkill(bot, args = {}) {

  const mobType = args.mobType || null
  const maxDistance = Number(args.maxDistance || 12)

  const mobs = Object.values(bot.entities)
    .filter((e) => e && e.position)
    .filter((e) => (mobType ? e.name === mobType : isHostile(e)))

    .map((e) => ({ entity: e, distance: bot.entity.position.distanceTo(e.position) }))
    .filter((x) => x.distance <= maxDistance)
    .sort((a, b) => a.distance - b.distance)

  if (mobs.length === 0) {
    return { success: false, reason: 'no target mob nearby' }
  }

  const target = mobs[0].entity
  try {
    await bot.attack(target)
    return { success: true, reason: `attacked ${target.name}` }
  } catch (err) {
    return { success: false, reason: `attack failed: ${err?.message || err}` }
  }
}

async function fleeSkill(bot, args = {}) {
  const distance = Number(args.distance || 8)
  const pos = bot.entity.position
  const tx = pos.x + (Math.random() > 0.5 ? distance : -distance)
  const tz = pos.z + (Math.random() > 0.5 ? distance : -distance)

  try {
    await bot.pathfinder.goto(new (require('mineflayer-pathfinder').goals.GoalNear)(tx, pos.y, tz, 2))
    return { success: true, reason: `fled about ${distance} blocks` }
  } catch (err) {
    return { success: false, reason: `flee failed: ${err?.message || err}` }
  }
}

async function eatSkill(bot, args = {}) {
  if ((bot.food ?? 20) >= 20) {
    return { success: true, reason: 'food already full, skip eating' }
  }

  const foodName = args.foodName || null
  try {

    const foodItem = bot.inventory
      .items()
      .find((it) => (foodName ? it.name === foodName : /bread|beef|pork|chicken|apple|potato/.test(it.name)))
    if (!foodItem) return { success: false, reason: 'no edible item found' }

    await bot.equip(foodItem, 'hand')
    await bot.consume()
    return { success: true, reason: `ate ${foodItem.name}` }
  } catch (err) {
    return { success: false, reason: `eat failed: ${err?.message || err}` }
  }
}

module.exports = {
  attackNearestSkill,
  fleeSkill,
  eatSkill,
}
