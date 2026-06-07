const { goals } = require('mineflayer-pathfinder')
const { Vec3 } = require('vec3')

const EXTRA_LOG_TO_PLANK = {
  crimson_stem: 'crimson_planks',
  warped_stem: 'warped_planks',
}

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function countByPredicate(bot, predicate) {

  return bot.inventory.items().filter(predicate).reduce((sum, it) => sum + it.count, 0)
}

function totalPlanks(bot) {
  return countByPredicate(bot, (it) => it?.name?.endsWith('_planks'))
}

function guessPlankFromLogName(logName) {
  if (!logName) return null
  if (EXTRA_LOG_TO_PLANK[logName]) return EXTRA_LOG_TO_PLANK[logName]
  if (logName.endsWith('_log')) return logName.replace(/_log$/, '_planks')
  return null
}

async function craftPlanksFromLogs(bot, needAtLeast = 4) {
  if (totalPlanks(bot) >= needAtLeast) return true

  const logItems = bot.inventory
    .items()
    .filter((it) => it?.name?.endsWith('_log') || it?.name === 'crimson_stem' || it?.name === 'warped_stem')

  for (const logItem of logItems) {
    const plankName = guessPlankFromLogName(logItem.name)
    if (!plankName) continue

    const plankDef = bot.registry.itemsByName[plankName]
    if (!plankDef) continue

    const neededPlanks = Math.max(0, needAtLeast - totalPlanks(bot))
    if (neededPlanks <= 0) return true

    const maxCraftTimes = Math.min(logItem.count, Math.ceil(neededPlanks / 4))
    if (maxCraftTimes <= 0) continue

    const plankRecipes = bot.recipesFor(plankDef.id, null, 1, null)
    if (!plankRecipes || !plankRecipes.length) continue

    try {
      await bot.craft(plankRecipes[0], maxCraftTimes, null)
      await wait(200)
    } catch (_) {
      // continue trying other wood types
    }


    if (totalPlanks(bot) >= needAtLeast) return true
  }

  return totalPlanks(bot) >= needAtLeast
}

function countItemByName(bot, name) {
  return countByPredicate(bot, (it) => it?.name === name)
}

async function ensureMaterialsForWoodenPickaxe(bot) {
  let planks = totalPlanks(bot)
  let sticks = countItemByName(bot, 'stick')

  if (sticks < 2) {
    const missingSticks = 2 - sticks
    const stickCraftTimes = Math.ceil(missingSticks / 4)
    const planksNeededForSticks = stickCraftTimes * 2

    if (planks < planksNeededForSticks) {
      await craftPlanksFromLogs(bot, planksNeededForSticks)
      planks = totalPlanks(bot)
    }

    if (planks < planksNeededForSticks) {
      return {
        ok: false,
        reason: `insufficient planks for sticks: need ${planksNeededForSticks}, have ${planks}`,
      }
    }

    const stickDef = bot.registry.itemsByName.stick
    const stickRecipes = stickDef ? bot.recipesFor(stickDef.id, null, 1, null) : []
    if (!stickRecipes || !stickRecipes.length) {
      return { ok: false, reason: 'no recipe for stick' }
    }

    try {
      await bot.craft(stickRecipes[0], stickCraftTimes, null)
      await wait(200)
    } catch (err) {
      return { ok: false, reason: `failed to craft sticks: ${err?.message || err}` }
    }


    planks = totalPlanks(bot)
    sticks = countItemByName(bot, 'stick')
  }

  if (planks < 3) {
    await craftPlanksFromLogs(bot, 3)
    planks = totalPlanks(bot)
  }

  if (planks < 3 || sticks < 2) {
    return {
      ok: false,
      reason: `insufficient materials for wooden_pickaxe: planks=${planks}, sticks=${sticks}`,
    }
  }

  return { ok: true, reason: 'materials ready for wooden_pickaxe' }
}

function buildPlacementCandidates(bot) {

  const origin = bot.entity.position.floored()
  const offsets = [
    [0, -1, 0],
    [1, -1, 0],
    [-1, -1, 0],
    [0, -1, 1],
    [0, -1, -1],
    [1, -1, 1],
    [1, -1, -1],
    [-1, -1, 1],
    [-1, -1, -1],
    [2, -1, 0],
    [-2, -1, 0],
    [0, -1, 2],
    [0, -1, -2],
  ]

  const candidates = []
  for (const [dx, dy, dz] of offsets) {
    const base = bot.blockAt(origin.offset(dx, dy, dz))
    if (!base || base.boundingBox !== 'block') continue
    const top = bot.blockAt(base.position.offset(0, 1, 0))
    if (!top || top.boundingBox !== 'empty') continue
    candidates.push(base)
  }

  return candidates
}

async function ensureCraftingTable(bot) {
  const tableId = bot.registry.blocksByName.crafting_table.id
  let table = bot.findBlock({ matching: tableId, maxDistance: 32 })
  if (table) return { table, reason: 'found nearby crafting_table' }

  const tableItem = bot.inventory.items().find((i) => i.name === 'crafting_table')
  if (!tableItem) return { table: null, reason: 'no crafting_table item in inventory' }

  try {
    await bot.equip(tableItem, 'hand')
  } catch (err) {
    return { table: null, reason: `failed to equip crafting_table: ${err?.message || err}` }
  }

  const candidates = buildPlacementCandidates(bot)
  if (!candidates.length) {
    return { table: null, reason: 'no valid nearby surface to place crafting_table' }
  }

  let lastErr = null
  for (const base of candidates) {
    try {
      await bot.pathfinder.goto(new goals.GoalNear(base.position.x, base.position.y, base.position.z, 2))
      await bot.placeBlock(base, new Vec3(0, 1, 0))
      await wait(200)
      table = bot.findBlock({ matching: tableId, maxDistance: 6 })

      if (table) return { table, reason: 'placed crafting_table' }
    } catch (err) {
      lastErr = err
    }
  }

  return {
    table: null,
    reason: `failed to place crafting_table near player: ${lastErr?.message || 'unknown error'}`,
  }
}


async function craftSkill(bot, args = {}) {
  const item = args.item
  const count = Number(args.count || 1)
  if (!item) return { success: false, reason: 'craft requires item' }

  const def = bot.registry.itemsByName[item]
  if (!def) return { success: false, reason: `unknown craft item: ${item}` }

  if (item === 'crafting_table') {
    await craftPlanksFromLogs(bot, 4)
  }

  if (item === 'wooden_pickaxe') {
    const prep = await ensureMaterialsForWoodenPickaxe(bot)
    if (!prep.ok) {
      return { success: false, reason: prep.reason }
    }
  }


  let recipes = bot.recipesFor(def.id, null, count, null)
  if (recipes && recipes.length) {

    try {
      await bot.craft(recipes[0], count, null)
      return { success: true, reason: `crafted ${count} ${item} (no table)` }
    } catch (err) {
      return { success: false, reason: `craft failed: ${err?.message || err}` }
    }
  }

  const { table, reason: tableReason } = await ensureCraftingTable(bot)
  if (!table) {
    if (item === 'crafting_table') {
      return { success: false, reason: 'cannot craft crafting_table: need at least 4 planks (logs can be converted automatically)' }
    }
    return { success: false, reason: `need crafting_table for ${item} but none available (${tableReason})` }
  }

  await bot.pathfinder.goto(new goals.GoalNear(table.position.x, table.position.y, table.position.z, 2))
  await wait(250)

  recipes = bot.recipesFor(def.id, null, count, table)
  for (let i = 0; i < 3 && (!recipes || !recipes.length); i++) {
    await wait(200)
    recipes = bot.recipesFor(def.id, null, count, table)
  }
  if (!recipes || !recipes.length) {
    return { success: false, reason: `no recipe for ${item} even with table` }
  }


  try {
    await bot.craft(recipes[0], count, table)
    return { success: true, reason: `crafted ${count} ${item} (with table)` }
  } catch (err) {
    return { success: false, reason: `craft failed: ${err?.message || err}` }
  }
}

module.exports = {
  craftSkill,
}

