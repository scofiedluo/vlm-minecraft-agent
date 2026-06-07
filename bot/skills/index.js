const { collectBlockSkill } = require('./collectBlock')
const { gotoSkill, exploreSkill } = require('./navigate')
const { craftSkill } = require('./craft')
const { attackNearestSkill, fleeSkill, eatSkill } = require('./combat')
const { huntSkill } = require('./hunt')


function pickState(bot) {
  const inventory = {}
  for (const item of bot.inventory.items()) {
    inventory[item.name] = (inventory[item.name] || 0) + item.count
  }
  const p = bot.entity?.position
  return {
    inventory,
    position: p ? { x: Number(p.x.toFixed(2)), y: Number(p.y.toFixed(2)), z: Number(p.z.toFixed(2)) } : null,
  }
}

function buildDiff(before, after) {
  const invDiff = {}
  const names = new Set([...Object.keys(before.inventory), ...Object.keys(after.inventory)])
  for (const name of names) {
    const delta = (after.inventory[name] || 0) - (before.inventory[name] || 0)
    if (delta !== 0) invDiff[name] = delta > 0 ? `+${delta}` : `${delta}`
  }
  return {
    inventory: invDiff,
    position:
      before.position && after.position
        ? `(${before.position.x},${before.position.y},${before.position.z}) -> (${after.position.x},${after.position.y},${after.position.z})`
        : 'unknown',
  }
}

async function dispatchSkill(bot, payload = {}) {
  const name = payload?.name
  const args = payload?.args || {}
  const timeoutMs = Number(payload?.timeoutMs || args?.timeoutMs || 30000)

  const skills = {
    collect_block: collectBlockSkill,
    goto: gotoSkill,
    craft: craftSkill,
    attack_nearest: attackNearestSkill,
    hunt: huntSkill,
    flee: fleeSkill,

    eat: eatSkill,
    look_at: async () => ({ success: false, reason: 'look_at not implemented yet' }),
    explore: exploreSkill,
  }

  if (!skills[name]) throw new Error(`unsupported skill: ${name}`)

  const stateBefore = pickState(bot)
  let timeoutId = null
  const timeoutPromise = new Promise((resolve) => {
    timeoutId = setTimeout(() => {
      try {
        bot.pathfinder?.stop?.()
      } catch (_) {
        // ignore
      }
      resolve({ success: false, reason: `skill timeout after ${timeoutMs}ms` })
    }, timeoutMs)
  })

  const skillPromise = Promise.resolve(skills[name](bot, args)).catch((err) => ({
    success: false,
    reason: err?.message || `skill ${name} failed`,
  }))

  const result = await Promise.race([skillPromise, timeoutPromise])
  if (timeoutId) {
    clearTimeout(timeoutId)
  }


  const stateAfter = pickState(bot)

  return {
    success: Boolean(result?.success),
    reason: result?.reason || '',
    stateBefore,
    stateAfter,
    diff: buildDiff(stateBefore, stateAfter),
  }
}


module.exports = {
  dispatchSkill,
}
