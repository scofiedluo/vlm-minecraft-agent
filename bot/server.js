const http = require('http')
const { createBotFromEnv } = require('./botFactory')
const { getStateSnapshot } = require('./state')
const { getSafetySignal } = require('./safety')

const bot = createBotFromEnv()
let lastSkillResult = null
let skillBusy = false



function sendJson(res, statusCode, data) {
  res.writeHead(statusCode, { 'Content-Type': 'application/json; charset=utf-8' })
  res.end(JSON.stringify(data))
}

async function readJsonBody(req) {
  return new Promise((resolve, reject) => {
    let data = ''
    req.on('data', (chunk) => {
      data += chunk
      if (data.length > 1024 * 1024) {
        reject(new Error('payload too large'))
      }
    })
    req.on('end', () => {
      if (!data) return resolve({})
      try {
        resolve(JSON.parse(data))
      } catch (err) {
        reject(new Error('invalid json body'))
      }
    })
    req.on('error', reject)
  })
}

const server = http.createServer(async (req, res) => {
  try {
    if (req.method === 'GET' && req.url === '/health') {
      return sendJson(res, 200, { ok: true, status: 'up' })
    }

    if (req.method === 'GET' && req.url === '/state') {
      const safety = getSafetySignal(bot)
      return sendJson(res, 200, { ...getStateSnapshot(bot, lastSkillResult), safety })
    }


    if (req.method === 'POST' && req.url === '/skill') {
      if (skillBusy) return sendJson(res, 409, { ok: false, error: 'bot busy' })
      skillBusy = true
      try {
        const { dispatchSkill } = require('./skills')
        const body = await readJsonBody(req)
        const result = await dispatchSkill(bot, body)
        lastSkillResult = {
          name: body?.name || 'unknown',
          success: Boolean(result?.success),
          reason: result?.reason || '',
        }
        return sendJson(res, 200, { ok: true, ...result })
      } finally {
        skillBusy = false
      }
    }


    return sendJson(res, 404, { ok: false, error: 'not found' })
  } catch (err) {
    return sendJson(res, 500, { ok: false, error: err?.message || 'internal error' })
  }
})

const port = Number(process.env.SKILL_SERVER_PORT || '3000')
const host = process.env.SKILL_SERVER_HOST || '127.0.0.1'
server.listen(port, host, () => {
  console.log(`[server] skill service listening at http://${host}:${port}`)
})
