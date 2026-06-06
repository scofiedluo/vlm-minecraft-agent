const mineflayer = require('mineflayer')
const { pathfinder } = require('mineflayer-pathfinder')


function parseBool(raw, fallback = false) {
  if (raw == null) return fallback
  const v = String(raw).trim().toLowerCase()
  if (['1', 'true', 'yes', 'on'].includes(v)) return true
  if (['0', 'false', 'no', 'off'].includes(v)) return false
  return fallback
}

function createBotFromEnv() {
  const host = process.env.MC_HOST || 'localhost'
  const port = Number(process.env.MC_PORT || '25565')
  const username = process.env.MC_USERNAME || 'vlm_agent'
  const version = process.env.MC_VERSION || '1.20.1'

  const viewerEnabled = parseBool(process.env.BOT_VIEWER_ENABLED, true)
  const viewerPort = Number(process.env.BOT_VIEWER_PORT || '3007')
  const viewerFirstPerson = parseBool(process.env.BOT_VIEWER_FIRST_PERSON, true)

  const bot = mineflayer.createBot({
    host,
    port,
    username,
    version,
  })

  bot.loadPlugin(pathfinder)

  bot.once('spawn', () => {
    console.log(`[bot] spawned: ${username}@${host}:${port} v${version}`)

    if (viewerEnabled) {
      try {
        const { mineflayer: prismarineViewer } = require('prismarine-viewer')
        prismarineViewer(bot, {
          port: viewerPort,
          firstPerson: viewerFirstPerson,
        })
        console.log(`[viewer] ready: http://127.0.0.1:${viewerPort} (firstPerson=${viewerFirstPerson})`)
      } catch (err) {
        console.error('[viewer] failed:', err?.message || err)
        console.warn('[viewer] fallback: set BOT_VIEWER_ENABLED=false to run bot without viewer')
      }
    }

  })

  bot.on('error', (err) => {
    console.error('[bot] error:', err?.message || err)
  })

  bot.on('kicked', (reason) => {
    console.warn('[bot] kicked:', reason)
  })

  bot.on('end', (reason) => {
    console.warn('[bot] disconnected:', reason || 'connection closed')
  })

  return bot
}

module.exports = {
  createBotFromEnv,
}

