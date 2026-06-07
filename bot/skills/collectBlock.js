const { goals } = require('mineflayer-pathfinder')
const { getSafetySignal } = require('../safety')


function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function countInventory(bot, itemName) {
  return bot.inventory
    .items()
    .filter((it) => it.name === itemName)
    .reduce((acc, it) => acc + it.count, 0)
}

// 方块 -> 掉落物（未列出的默认掉落同名物品）
const BLOCK_DROP = {
  stone: 'cobblestone',
  deepslate: 'cobbled_deepslate',
  grass_block: 'dirt',
  coal_ore: 'coal',
  deepslate_coal_ore: 'coal',
  iron_ore: 'raw_iron',
  deepslate_iron_ore: 'raw_iron',
}

function expectedDrop(block, args = {}) {
  return args.drop || BLOCK_DROP[block] || block
}

const PICKAXE_RE = /(_ore$|^stone$|^cobblestone$|^deepslate|_deepslate$|^andesite$|^diorite$|^granite$|^tuff$|^calcite$|^netherrack$|^blackstone$)/
const AXE_RE = /(_log$|_wood$|_planks$|^crafting_table$|^chest$|^bookshelf$)/
const SHOVEL_RE = /(^dirt$|^grass_block$|^sand$|^gravel$|^clay$|^soul_sand$|^soul_soil$|^snow)/

function categoryForBlock(blockName) {
  if (PICKAXE_RE.test(blockName)) return 'pickaxe'
  if (AXE_RE.test(blockName)) return 'axe'
  if (SHOVEL_RE.test(blockName)) return 'shovel'
  return null
}

function findToolByCategory(bot, category) {
  return bot.inventory.items().find((it) => it.name.endsWith(`_${category}`)) || null
}

async function equipToolForBlock(bot, blockName) {
  const category = categoryForBlock(blockName)
  if (!category) return

  const tool = findToolByCategory(bot, category)
  if (tool && bot.heldItem?.name !== tool.name) {
    try {
      await bot.equip(tool, 'hand')
    } catch (_) {
      // 装备失败不阻断采集
    }
  }
}

function isWoodLikeBlock(blockName) {
  return /(_log$|_wood$|_stem$)/.test(blockName)
}

function isExposedBlock(bot, pos) {
  const dirs = [
    [1, 0, 0],
    [-1, 0, 0],
    [0, 1, 0],
    [0, -1, 0],
    [0, 0, 1],
    [0, 0, -1],
  ]
  for (const [dx, dy, dz] of dirs) {
    const adj = bot.blockAt(pos.offset(dx, dy, dz))
    if (!adj || adj.boundingBox === 'empty') return true
  }
  return false
}

function findTargetBlock(bot, blockName, maxDistance, options = {}) {
  const registry = bot.registry?.blocksByName || {}
  const blockDef = registry[blockName]
  if (!blockDef) return null

  if (options.preferExposed && typeof bot.findBlocks === 'function') {
    const positions = bot.findBlocks({
      matching: blockDef.id,
      maxDistance,
      count: 64,
    })
    for (const pos of positions) {
      const blk = bot.blockAt(pos)
      if (blk && isExposedBlock(bot, blk.position)) return blk
    }
  }

  return bot.findBlock({
    matching: blockDef.id,
    maxDistance,
  })
}

function buildRoamOffsets(searchRadius, rings = 2, pointsPerRing = 8) {
  const offsets = []
  const angleJitter = Math.random() * Math.PI * 2

  for (let ring = 1; ring <= rings; ring++) {
    const radius = Math.max(6, Math.floor((searchRadius * ring) / rings))
    for (let i = 0; i < pointsPerRing; i++) {
      const theta = angleJitter + (Math.PI * 2 * i) / pointsPerRing
      offsets.push([Math.floor(Math.cos(theta) * radius), Math.floor(Math.sin(theta) * radius)])
    }
  }

  offsets.sort(() => Math.random() - 0.5)
  return offsets
}

async function roamToFindBlock(bot, blockName, originPos, maxDistance, timeoutAt, options = {}) {
  const searchRadius = Math.max(8, Math.min(maxDistance, 56))
  const offsets = buildRoamOffsets(searchRadius, 2, 10)

  for (const [dx, dz] of offsets) {
    if (Date.now() >= timeoutAt) break

    const found = findTargetBlock(bot, blockName, maxDistance, options)
    if (found) return found

    const gx = Math.floor(originPos.x + dx)
    const gz = Math.floor(originPos.z + dz)
    const gy = Math.floor(bot.entity.position.y)

    try {
      await bot.pathfinder.goto(new goals.GoalNear(gx, gy, gz, 3))
    } catch (_) {
      // 忽略单个点位寻路失败，继续巡航
    }

    const foundAfterMove = findTargetBlock(bot, blockName, maxDistance, options)
    if (foundAfterMove) return foundAfterMove

    await wait(120)
  }

  return null
}


async function gotoAndDig(bot, target) {

  await bot.pathfinder.goto(new goals.GoalNear(target.position.x, target.position.y, target.position.z, 2))
  const block = bot.blockAt(target.position)
  if (!block) throw new Error('target block vanished before dig')
  await equipToolForBlock(bot, block.name)
  await bot.dig(block)
  return block.name
}



async function collectBlockSkill(bot, args = {}) {
  const block = args.block || 'oak_log'
  const count = Number(args.count || 1)
  const maxDistance = Number(args.maxDistance || 32)
  const dropName = expectedDrop(block, args)

  if (count <= 0) {
    return { success: true, reason: 'count <= 0, nothing to do' }
  }

  const before = countInventory(bot, dropName)
  const targetTotal = before + count
  const startAt = Date.now()
  const timeoutMs = Number(args.timeoutMs || 30000)
  const timeoutAt = startAt + timeoutMs
  const origin = bot.entity.position.clone()
  const enableRoaming = args.enableRoaming === true || isWoodLikeBlock(block)

  while (Date.now() < timeoutAt) {

    if (getSafetySignal(bot).danger) {
      return { success: false, reason: 'aborted: danger detected' }
    }

    const now = countInventory(bot, dropName)

    if (now >= targetTotal) {
      return { success: true, reason: `collected ${now - before} ${dropName}` }
    }


    const searchOptions = { preferExposed: block === 'stone' }
    let target = findTargetBlock(bot, block, maxDistance, searchOptions)

    if (!target && enableRoaming) {
      target = await roamToFindBlock(bot, block, origin, maxDistance, timeoutAt, searchOptions)
    }


    if (!target) {
      return { success: false, reason: `nearby no ${block} in ${maxDistance} blocks` }
    }


    try {
      const minedBlockName = await gotoAndDig(bot, target)
      const nowAfterDig = countInventory(bot, dropName)
      if (nowAfterDig >= targetTotal) {
        return { success: true, reason: `collected ${nowAfterDig - before} ${dropName}` }
      }
      const settleWait = categoryForBlock(minedBlockName) === 'pickaxe' ? 120 : 220
      await wait(settleWait)
    } catch (err) {
      return { success: false, reason: `collect failed: ${err?.message || err}` }
    }

  }

  const after = countInventory(bot, dropName)
  if (after > before) {
    return { success: true, reason: `timeout but still got ${after - before} ${dropName}` }
  }
  return { success: false, reason: `timeout collecting ${dropName}` }
}


module.exports = {
  collectBlockSkill,
}
