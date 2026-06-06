const { goals } = require('mineflayer-pathfinder')

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function countInventory(bot, itemName) {
  return bot.inventory
    .items()
    .filter((it) => it.name === itemName)
    .reduce((acc, it) => acc + it.count, 0)
}

function findTargetBlock(bot, blockName, maxDistance) {
  const registry = bot.registry?.blocksByName || {}
  const blockDef = registry[blockName]
  if (!blockDef) return null
  return bot.findBlock({
    matching: blockDef.id,
    maxDistance,
  })
}

async function gotoAndDig(bot, target) {
  await bot.pathfinder.goto(new goals.GoalGetToBlock(target.position.x, target.position.y, target.position.z))
  const block = bot.blockAt(target.position)
  if (!block) throw new Error('target block vanished before dig')
  await bot.dig(block)
}

async function collectBlockSkill(bot, args = {}) {
  const block = args.block || 'oak_log'
  const count = Number(args.count || 1)
  const maxDistance = Number(args.maxDistance || 32)

  if (count <= 0) {
    return { success: true, reason: 'count <= 0, nothing to do' }
  }

  const before = countInventory(bot, block)
  const targetTotal = before + count
  const startAt = Date.now()
  const timeoutMs = Number(args.timeoutMs || 30000)

  while (Date.now() - startAt < timeoutMs) {
    const now = countInventory(bot, block)
    if (now >= targetTotal) {
      return { success: true, reason: `collected ${now - before} ${block}` }
    }

    const target = findTargetBlock(bot, block, maxDistance)
    if (!target) {
      return { success: false, reason: `nearby no ${block} in ${maxDistance} blocks` }
    }

    try {
      await gotoAndDig(bot, target)
      await wait(300)
    } catch (err) {
      return { success: false, reason: `collect failed: ${err?.message || err}` }
    }
  }

  const after = countInventory(bot, block)
  if (after > before) {
    return { success: true, reason: `timeout but still got ${after - before} ${block}` }
  }
  return { success: false, reason: `timeout collecting ${block}` }
}

module.exports = {
  collectBlockSkill,
}
