const { goals } = require('mineflayer-pathfinder')
const { getSafetySignal } = require('../safety')

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function isAlive(bot, entity) {
  return entity && entity.isValid !== false && Boolean(bot.entities[entity.id])
}

function normalizeMobName(rawMob) {
  if (!rawMob) return ''
  const lower = String(rawMob).toLowerCase().trim()
  const alias = {
    shepp: 'sheep',
    pigg: 'pig',
  }
  return alias[lower] || lower
}

function findNearestMob(bot, mobName, maxDistance) {
  const pos = bot.entity.position
  return Object.values(bot.entities)
    .filter((e) => isAlive(bot, e) && e.position && e.name === mobName)
    .map((e) => ({ entity: e, distance: pos.distanceTo(e.position) }))
    .filter((x) => x.distance <= maxDistance)
    .sort((a, b) => a.distance - b.distance)[0]?.entity || null
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

async function roamToFindMob(bot, mobName, startPos, maxDistance, timeoutAt) {
  const searchRadius = Math.max(8, Math.min(maxDistance, 56))
  const offsets = buildRoamOffsets(searchRadius, 2, 10)

  for (const [dx, dz] of offsets) {
    if (Date.now() >= timeoutAt) break

    const target = findNearestMob(bot, mobName, maxDistance)
    if (target) return target

    const gx = Math.floor(startPos.x + dx)
    const gz = Math.floor(startPos.z + dz)
    const gy = Math.floor(bot.entity.position.y)

    try {
      await bot.pathfinder.goto(new goals.GoalNear(gx, gy, gz, 3))
    } catch (_) {
      // 忽略寻路失败，继续下一个搜索点
    }

    const foundAfterMove = findNearestMob(bot, mobName, maxDistance)
    if (foundAfterMove) return foundAfterMove

    await wait(120)
  }

  return null
}


async function huntSkill(bot, args = {}) {
  const mob = normalizeMobName(args.mob || args.mobType)
  if (!mob) return { success: false, reason: 'hunt requires mob (e.g. pig/sheep)' }

  const count = Number(args.count || 1)
  const maxDistance = Number(args.maxDistance || 64)
  const timeoutMs = Number(args.timeoutMs || 60000)
  const reach = 3
  const attackCooldownMs = 600
  const startAt = Date.now()
  const timeoutAt = startAt + timeoutMs
  const origin = bot.entity.position.clone()
  let killed = 0

  while (Date.now() < timeoutAt) {
    if (getSafetySignal(bot).danger) {
      return {
        success: killed >= count,
        reason: killed > 0 ? `hunted ${killed} ${mob} then aborted (danger)` : 'aborted: danger',
      }
    }

    let target = findNearestMob(bot, mob, maxDistance)
    if (!target) {
      target = await roamToFindMob(bot, mob, origin, maxDistance, timeoutAt)
    }

    if (!target) {
      if (killed >= count) return { success: true, reason: `hunted ${killed} ${mob}` }
      continue
    }

    try {
      bot.pathfinder.setGoal(new goals.GoalFollow(target, 2), true)
    } catch (_) {
      // ignore
    }

    while (isAlive(bot, target) && Date.now() < timeoutAt) {
      if (getSafetySignal(bot).danger) break
      const distance = bot.entity.position.distanceTo(target.position)
      if (distance <= reach) {
        try {
          await bot.attack(target)
        } catch (_) {
          // ignore attack jitter
        }
        await wait(attackCooldownMs)
      } else {
        await wait(150)
      }
    }

    try {
      bot.pathfinder.setGoal(null)
    } catch (_) {
      // ignore
    }

    if (!isAlive(bot, target)) {
      killed += 1
      if (killed >= count) return { success: true, reason: `hunted ${killed} ${mob}` }
    }
  }

  if (killed > 0) {
    return { success: false, reason: `timeout hunting ${mob}, killed ${killed}/${count}` }
  }
  return { success: false, reason: `timeout hunting ${mob}, no ${mob} found in search radius ${maxDistance}` }
}


module.exports = {
  huntSkill,
}
