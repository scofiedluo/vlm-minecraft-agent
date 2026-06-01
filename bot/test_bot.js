/*
 * @Author: scofiedluo scofiedluo@gmail.com
 * @Date: 2026-06-01 10:53:23
 * @LastEditors: scofiedluo scofiedluo@gmail.com
 * @LastEditTime: 2026-06-01 11:06:57
 * @FilePath: \vlm-minecraft-agent\bot\test_bot.js
 * @Description: 
 * 
 * Copyright (c) 2026 by ${scofiedluo}, All Rights Reserved. 
 */
const mineflayer = require('mineflayer')

const bot = mineflayer.createBot({
  host: 'localhost',
  port: 25565,
  username: 'vlm_agent',
  version: '1.20.1'
})

bot.once('spawn', () => {
  console.log('Bot spawned in Minecraft')
  bot.chat('Hello, I am VLM Agent')
})

bot.on('error', err => console.error(err))
bot.on('end', () => console.log('Bot disconnected'))
