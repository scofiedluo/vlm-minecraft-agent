const { goals } = require('mineflayer-pathfinder')

async function gotoSkill(bot, args = {}) {
  const maxDistance = Number(args.maxDistance || 2)

  if (typeof args.x === 'number' && typeof args.y === 'number' && typeof args.z === 'number') {
    await bot.pathfinder.goto(new goals.GoalNear(args.x, args.y, args.z, maxDistance))
    return { success: true, reason: `arrived near (${args.x}, ${args.y}, ${args.z})` }
  }

  const entityName = args.entity
  if (entityName) {
    const entity = Object.values(bot.entities).find((e) => e && (e.name === entityName || e.username === entityName))
    if (!entity) {
      return { success: false, reason: `entity not found: ${entityName}` }
    }
    await bot.pathfinder.goto(new goals.GoalNear(entity.position.x, entity.position.y, entity.position.z, maxDistance))
    return { success: true, reason: `arrived near entity ${entityName}` }
  }

  return { success: false, reason: 'goto requires x,y,z or entity' }
}

async function exploreSkill(bot, args = {}) {
  const radius = Number(args.radius || 8)
  const pos = bot.entity.position
  const tx = pos.x + (Math.random() > 0.5 ? radius : -radius)
  const tz = pos.z + (Math.random() > 0.5 ? radius : -radius)
  await bot.pathfinder.goto(new goals.GoalNear(tx, pos.y, tz, 2))
  return { success: true, reason: `explored around radius ${radius}` }
}

module.exports = {
  gotoSkill,
  exploreSkill,
}
