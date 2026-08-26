#!/usr/bin/env node
/*
 * set-guest-password.js — turn the guest sign-in on (or off), on its own.
 *
 *   node set-guest-password.js          set or change the guest password
 *   node set-guest-password.js --off    remove guest sign-in from this build
 *
 * setup-shared-login.js does this too, but it does the TEAM password in the
 * same run and so it asks for your GitHub token first. This one never needs it.
 *
 * That is not a shortcut, it is the shape of the thing: a guest blob carries
 * {demo:1} and nothing else. No token, no owner, no repository. It opens the
 * built-in sample board — invented people, invented projects, held in memory,
 * read-only — and your repository is never called. So the only secret involved
 * is the guest password itself, and this script can seal one without knowing
 * anything about your GitHub account.
 *
 * It writes exactly one line of index.html: `const GHVIEW=...;`. Your team
 * password (GHENC) is not read, not re-sealed and not touched.
 */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const readline = require('readline');

const FILE = path.join(__dirname, 'index.html');
const ITERATIONS = 600000;
const OFF = process.argv.includes('--off');

/* A passphrase somebody can repeat over a call. 181 words at 7.5 bits each, so five of them
   is 37 bits. Thin for the team password, which is why setup-shared-login.js suggests seven of
   these — but exactly right here: a guest blob carries {demo:1} and no credential, so there is
   nothing behind it worth a day of anybody's electricity. */
const WORDS = ('able acorn amber anchor apple arrow autumn badge bamboo basket beacon birch ' +
  'bishop bloom bottle branch bridge bronze butter cactus candle canvas canyon carbon castle ' +
  'cedar cherry cinder circle citrus cloud clover cobalt copper coral cotton cradle crater ' +
  'crimson crystal cypress daisy dagger dawn delta denim desert diamond dolphin domino ember ' +
  'emerald falcon fable feather fennel fiddle flame flint forest fossil garnet ginger glacier ' +
  'granite gravel harbor hazel helix hollow indigo ivory jasmine jasper jungle juniper kettle ' +
  'lagoon lantern lattice lemon lichen lilac linen lotus lumber magnet mango maple marble ' +
  'marigold meadow mellow meteor mint mirror monsoon mosaic myrtle nectar nickel noble ' +
  'nutmeg oasis olive onyx opal orbit orchid osprey otter paisley pebble pepper pewter ' +
  'pigment pillar pine pistachio pollen poplar prairie prism pumpkin quarry quartz quiver ' +
  'radish rapid raven ribbon ripple river rosemary rust saffron sage salmon sandal sapphire ' +
  'satin scarlet sequoia shadow shale silver slate solar sorrel spruce stellar sterling ' +
  'stone summit sunset syrup tamarind tangent teal tender thistle thunder timber topaz ' +
  'torch trellis tulip tundra turquoise umber valley velvet vermilion violet walnut willow ' +
  'wicker wisp yarrow zephyr zenith').split(/\s+/);
/* distinct words: the phrase gets read out loud, and a repeat is the thing people mistype */
const makePass = () => { const p = new Set();
  while (p.size < 5) p.add(WORDS[crypto.randomInt(0, WORDS.length)]);
  return [...p].join('-'); };

/* Interactive from a terminal, which is the normal way. When stdin is a pipe node's readline
   answers the first question and then hangs, so read the lines directly — that also makes the
   tool testable. */
const TTY = Boolean(process.stdin.isTTY);
let rl = null, piped = null, pipeAt = 0;
if (TTY) rl = readline.createInterface({ input: process.stdin, output: process.stdout, terminal: true });
else { try { piped = fs.readFileSync(0, 'utf8').split(/\r?\n/); } catch (e) { piped = []; } }
const closeInput = () => { if (rl) rl.close(); };
const ask = q => {
  if (!TTY) { const a = (piped[pipeAt++] || '').trim(); process.stdout.write(q + '\n'); return Promise.resolve(a); }
  return new Promise(res => rl.question(q, a => res(a.trim())));
};

const seal = (secret, obj) => {
  const salt = crypto.randomBytes(16);
  const iv = crypto.randomBytes(12);
  const key = crypto.pbkdf2Sync(secret, salt, ITERATIONS, 32, 'sha256');
  const c = crypto.createCipheriv('aes-256-gcm', key, iv);
  /* the auth tag is appended to the ciphertext, which is what WebCrypto expects on the way back */
  const ct = Buffer.concat([c.update(JSON.stringify(obj), 'utf8'), c.final(), c.getAuthTag()]);
  return JSON.stringify({ salt: salt.toString('base64'), iv: iv.toString('base64'),
    ct: ct.toString('base64'), it: ITERATIONS });
};

/* Would this password also open the team blob? We cannot compare the two plaintexts — GHENC is
   sealed and this script never learns it — but we can try the key on it. GCM is authenticated,
   so a wrong password throws and a right one does not. */
function opensTeam(html, pass) {
  const m = html.match(/^const GHENC=(\{.*\});$/m);
  if (!m) return false;
  let b; try { b = JSON.parse(m[1]); } catch (e) { return false; }
  try {
    const key = crypto.pbkdf2Sync(pass, Buffer.from(b.salt, 'base64'), b.it || ITERATIONS, 32, 'sha256');
    const raw = Buffer.from(b.ct, 'base64');
    const d = crypto.createDecipheriv('aes-256-gcm', key, Buffer.from(b.iv, 'base64'));
    d.setAuthTag(raw.slice(raw.length - 16));
    Buffer.concat([d.update(raw.slice(0, raw.length - 16)), d.final()]);
    return true;
  } catch (e) { return false; }
}

(async () => {
  if (!fs.existsSync(FILE)) { console.error('No index.html next to this script.'); process.exit(1); }
  const html = fs.readFileSync(FILE, 'utf8');
  if (!/^const GHVIEW=.*;$/m.test(html)) {
    console.error('Could not find the "const GHVIEW=...;" line in index.html.'); process.exit(1);
  }
  const hasTeam = /^const GHENC=\{/m.test(html);

  if (OFF) {
    fs.writeFileSync(FILE, html.replace(/^const GHVIEW=.*;$/m, 'const GHVIEW=null;'), 'utf8');
    console.log('\nGuest sign-in removed. Only the team password opens this build.');
    closeInput(); return;
  }

  console.log('\nGuest sign-in');
  console.log('A second password you can hand to anybody for a trial. It opens the built-in');
  console.log('sample board: invented people, invented projects, read-only, held in memory.');
  console.log('Your board is never fetched and your token is never decrypted, so this password');
  console.log('is safe to give out. Your team password is not touched by this script.\n');

  const suggested = makePass();
  console.log('Suggested guest password:  ' + suggested);
  const typed = await ask('Press Enter to use it, or type your own: ');
  const pass = typed || suggested;
  if (pass.length < 12) {
    console.error('\nToo short. The sealed blob is published in index.html, so the password is');
    console.error('the whole of the security — twelve characters is the floor.');
    closeInput(); process.exit(1);
  }
  if (hasTeam && opensTeam(html, pass)) {
    console.error('\nThat is the team password. A guest password has to be a different one, or');
    console.error('everybody you hand it to can edit the board.');
    closeInput(); process.exit(1);
  }

  const out = html.replace(/^const GHVIEW=.*;$/m,
    ('const GHVIEW=' + seal(pass, { demo: 1 }) + ';').replace(/\$/g, '$$$$'));
  /* the guest blob holds {demo:1} and nothing else, so there is nothing to leak — but check the
     team blob came through untouched, because that is the one that matters */
  const before = (html.match(/^const GHENC=.*;$/m) || [''])[0];
  const after = (out.match(/^const GHENC=.*;$/m) || [''])[0];
  if (before !== after) {
    console.error('\nABORT: the team blob changed. Nothing written.');
    closeInput(); process.exit(1);
  }
  fs.writeFileSync(FILE, out, 'utf8');

  console.log('\n  GUEST PASSWORD:  ' + pass);
  console.log('\nWritten into index.html. Commit and push, then anyone with the link and that');
  console.log('password can look round the sample board and change nothing.');
  console.log('To take it away again:  node set-guest-password.js --off');
  closeInput();
})();
