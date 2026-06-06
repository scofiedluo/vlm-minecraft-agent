async function craftSkill(bot, args = {}) {
  const item = args.item
  const count = Number(args.count || 1)
  if (!item) return { success: false, reason: 'craft requires item' }

  const itemByName = bot.registry.itemsByName[item]
  if (!itemByName) return { success: false, reason: `unknown craft item: ${item}` }

  const recipes = bot.recipesFor(itemByName.id, null, 1, null)
  if (!recipes || recipes.length === 0) {
    return { success: false, reason: `no recipe for ${item}` }
  }

  try {
    await bot.craft(recipes[0], count, null)
    return { success: true, reason: `crafted ${count} ${item}` }
  } catch (err) {
    return { success: false, reason: `craft failed: ${err?.message || err}` }
  }
}

module.exports = {
  craftSkill,
}
