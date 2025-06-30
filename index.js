// Equivalent implementation of your FastAPI game registry app in JavaScript (Node.js)
// This version uses Express + Axios + native in-memory cache

const express = require('express');
const axios = require('axios');
const crypto = require('crypto');
const app = express();

app.use(express.json());

const API_CONFIG = {
  host: '0.0.0.0',
  port: 4444,
  refresh_interval: 5
};

const CACHE = {
  games: [],
  last_updated: 0,
  last_snapshot: null
};

const REGISTERED_GAMES = [];

function hashGames(games) {
  const sorted = JSON.stringify(games.sort((a, b) => a.id.localeCompare(b.id)));
  return crypto.createHash('sha256').update(sorted).digest('hex');
}

async function fetchGame(url, name, provider = 'JILI') {
  const fullUrl = `${url}/api/games`;
  const headers = {
    'Accept': 'application/json',
    'Referer': url,
    'User-Agent': 'Mozilla/5.0'
  };
  const params = {
    name,
    manuf: provider,
    requestFrom: 'H6'
  };

  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      const response = await axios.get(fullUrl, { headers, params, timeout: 2000 });
      if (response.status === 200) {
        const data = response.data.data || [];
        console.log(`\n✅ Fetched '${name}' [${provider}] - ${data.length} game(s)`);
        return data;
      }
    } catch (e) {
      console.log(`\n⚠️ Network error on attempt ${attempt + 1} for '${name}': ${e.message}`);
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }

  console.log(`\n❌ Failed to fetch '${name}' after 2 attempts`);
  return [];
}

async function updateGames() {
  const tasks = REGISTERED_GAMES.map(g => fetchGame(g.url, g.name, g.provider));
  const results = await Promise.all(tasks);

  const combined = [];
  for (const games of results) {
    for (const game of games) {
      if (!combined.some(g => g.id === game.id)) {
        combined.push(game);
      }
    }
  }

  if (combined.length === 0) return false;

  const newHash = hashGames(combined);
  if (CACHE.last_snapshot === newHash) {
    console.log("\n🔁 No changes detected.");
    return false;
  }

  CACHE.games = combined;
  CACHE.last_updated = Date.now() / 1000;
  CACHE.last_snapshot = newHash;
  console.log(`🔄 CACHE updated with ${combined.length} game(s)`);
  return true;
}

async function refreshLoop(baseInterval = 5) {
  let failCount = 0;
  const maxBackoff = 25;

  while (true) {
    let wait = baseInterval;
    if (REGISTERED_GAMES.length > 0) {
      const changed = await updateGames();
      if (!changed) failCount++;
      else failCount = 0;
    } else {
      failCount++;
    }

    wait += Math.min(failCount * 5, maxBackoff);
    console.log(`\n⏳ Sleeping for ${wait} seconds...\n`);
    await new Promise(resolve => setTimeout(resolve, wait * 1000));
  }
}

app.post('/register', (req, res) => {
  const { url, name, provider = 'JILI' } = req.body;
  if (!name || REGISTERED_GAMES.some(g => g.name === name)) {
    return res.json({ status: 'exists', message: `'${name}' already registered` });
  }
  REGISTERED_GAMES.push({ url, name, provider });
  console.log(`\n🎰 Registered: ${name}\n`);
  res.json({ status: 'ok', message: `Registered '${name}' with provider '${provider}'` });
});

app.post('/deregister', (req, res) => {
  const { name } = req.body;
  const index = REGISTERED_GAMES.findIndex(g => g.name === name);
  if (index >= 0) {
    REGISTERED_GAMES.splice(index, 1);
    console.log(`\n🎰 De-Registered: ${name}\n`);
    return res.json({ status: 'ok', message: `Deregistered '${name}'` });
  }
  res.json({ status: 'not_found', message: `'${name}' not found` });
});

app.get('/game', (req, res) => {
  const name = (req.query.name || '').replace(/\s+/g, '').toLowerCase();
  const found = CACHE.games.find(g => g.name.replace(/\s+/g, '').toLowerCase() === name);
  if (found) return res.json(found);
  res.status(404).json({ error: `Game '${req.query.name}' not found.` });
});

app.get('/games', (req, res) => {
  res.json({
    status: 0,
    data: CACHE.games,
    last_updated: CACHE.last_updated,
    registered_games: REGISTERED_GAMES
  });
});

app.listen(API_CONFIG.port, API_CONFIG.host, () => {
  console.log(`🚀 Server listening on http://${API_CONFIG.host}:${API_CONFIG.port}`);
  refreshLoop(API_CONFIG.refresh_interval);
});
