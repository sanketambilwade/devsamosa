/* setup-shared-login.js — turn shared passwords into the whole sign-in.
 *
 *   node setup-shared-login.js
 *
 * Makes up to two credentials and writes both into index.html:
 *
 *   TEAM password   ->  GHENC   ->  a token that can write.  Full access.
 *   GUEST password  ->  GHVIEW  ->  {demo:1}, and no token at all.
 *
 * A guest gets the built-in sample board: invented people, invented projects,
 * held in memory and read-only. Your repository is never called and your token
 * is never decrypted, so the guest password is safe to hand to anybody and there
 * is nothing to set up on GitHub for it.
 *
 * Everything happens on this machine: the tokens are never sent anywhere except
 * to github.com to be verified, and the passwords are never stored at all.
 *
 * After running it, commit and push index.html. The encrypted blobs are safe to
 * publish — without the passwords they are meaningless — but that also means the
 * passwords are the only thing protecting the board. Use the ones it generates.
 */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const readline = require('readline');

const FILE = path.join(__dirname, 'index.html');
const ITERATIONS = 600000;

/* a passphrase people can actually repeat over a call, still ~77 bits */
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

const pick = () => WORDS[crypto.randomInt(0, WORDS.length)];
const makePass = () => Array.from({ length: 5 }, pick).join('-');

/* Interactive when run from a terminal, which is the normal way. When stdin is
   a pipe, node's readline only answers the first question and then hangs, so
   read the lines directly instead — that also makes the tool testable. */
const TTY = Boolean(process.stdin.isTTY);
let rl = null, masking = false, prompt = '', piped = null, pipeAt = 0;

if (TTY) {
  rl = readline.createInterface({ input: process.stdin, output: process.stdout, terminal: true });
  rl._writeToOutput = s => {
    if (!masking) return process.stdout.write(s);
    if (s.includes('\n')) process.stdout.write('\n');
    else if (s.startsWith(prompt)) process.stdout.write(prompt);
  };
} else {
  try { piped = fs.readFileSync(0, 'utf8').split(/\r?\n/); } catch (e) { piped = []; }
}
const closeInput = () => { if (rl) rl.close(); };

function ask(q, hidden) {
  if (!TTY) {
    const a = (piped[pipeAt++] || '').trim();
    process.stdout.write(q + (hidden ? '(hidden)' : a) + '\n');
    return Promise.resolve(a);
  }
  return new Promise(res => {
    masking = Boolean(hidden); prompt = q;
    rl.question(q, a => { masking = false; res(a.trim()); });
  });
}

async function main() {
  if (!fs.existsSync(FILE)) { console.error('index.html not found next to this script'); process.exit(1); }

  console.log('\nDevSamosa — set up one shared password\n' + '='.repeat(38));
  console.log('This encrypts your repo and token into index.html so anyone with');
  console.log('the link and the password can use the board. Nothing leaves this');
  console.log('machine except a single check against github.com.\n');

  const repo = await ask('Data repository (owner/name): ');
  const m = /^([\w.-]+)\/([\w.-]+)$/.exec(repo);
  if (!m) { console.error('\nWrite it as owner/name, e.g. sanketambilwade/devsamosa-data'); process.exit(1); }

  const token = await ask('GitHub token, read AND write (input hidden): ', true);
  if (token.length < 20) { console.error('\nThat token looks too short.'); process.exit(1); }

  process.stdout.write('\nChecking the token... ');
  const r = await fetch(`https://api.github.com/repos/${m[1]}/${m[2]}`, {
    headers: { Authorization: 'Bearer ' + token, Accept: 'application/vnd.github+json' },
  });
  if (!r.ok) {
    console.error(`failed (HTTP ${r.status}).`);
    console.error(r.status === 404 ? 'No such repository, or the token cannot see it.'
      : r.status === 401 ? 'The token was rejected — it may have expired.' : '');
    closeInput(); process.exit(1);
  }
  const info = await r.json();
  if (!info.permissions || !info.permissions.push) {
    console.error('failed.\nThat token can read but not write. It needs Contents: Read and write.');
    closeInput(); process.exit(1);
  }
  console.log(`ok — ${info.full_name}, ${info.private ? 'private' : 'PUBLIC (!)'}`);
  if (!info.private) console.log('  WARNING: that repository is public. Anyone can already read the board.');

  /* The guest half. One kind: the sample board. No token, nothing to set up. */
  console.log('\nGuest sign-in (optional). A second password you can hand to someone for a');
  console.log('trial. It opens a built-in sample board — invented people, invented projects,');
  console.log('read-only, held in memory. Your board is never fetched and your token is never');
  console.log('decrypted, so it is safe to give to anybody.');
  const vAns = (await ask('\nAdd a guest password? [Y/n]: ', false)).trim().toLowerCase();
  if (vAns && !/^(y|yes|n|no)$/.test(vAns)) {
    console.error('\nAnswer y or n.'); closeInput(); process.exit(1);
  }
  const demo = vAns !== 'n' && vAns !== 'no';

  const suggested = makePass();
  console.log(`\nSuggested team password:  ${suggested}`);
  console.log('  (five random words. Strong enough that the published blob cannot be');
  console.log('   cracked, and short enough to read out on a call.)');
  const typed = await ask('\nPress Enter to use it, or type your own: ', false);
  const pass = typed || suggested;
  if (pass.length < 12) {
    console.error('\nToo short. The encrypted blob is public, so a weak password is the whole');
    console.error('attack. Use at least 12 characters, or take the suggested one.');
    closeInput(); process.exit(1);
  }

  let vPass = '';
  if (demo) {
    const vSug = makePass();
    console.log(`\nSuggested guest password:  ${vSug}`);
    const vTyped = await ask('Press Enter to use it, or type your own: ', false);
    vPass = vTyped || vSug;
    if (vPass.length < 12) {
      console.error('\nToo short — same reason as the team one.');
      closeInput(); process.exit(1);
    }
    if (vPass === pass) {
      console.error('\nThe two passwords must differ, or nobody can sign in as a guest: the');
      console.error('team blob is tried first and would always win.');
      closeInput(); process.exit(1);
    }
  }

  /* WebCrypto expects the GCM tag appended to the ciphertext, which is why the tag is
     concatenated on rather than shipped beside it. There is a test for exactly that interop. */
  const sealRaw = (secret, obj) => {
    const salt = crypto.randomBytes(16);
    const iv = crypto.randomBytes(12);
    const key = crypto.pbkdf2Sync(secret, salt, ITERATIONS, 32, 'sha256');
    const cipher = crypto.createCipheriv('aes-256-gcm', key, iv);
    const ct = Buffer.concat([cipher.update(JSON.stringify(obj), 'utf8'), cipher.final(), cipher.getAuthTag()]);
    return JSON.stringify({
      salt: salt.toString('base64'), iv: iv.toString('base64'),
      ct: ct.toString('base64'), it: ITERATIONS,
    });
  };
  const seal = (secret, tok) => {
    const salt = crypto.randomBytes(16);
    const iv = crypto.randomBytes(12);
    const key = crypto.pbkdf2Sync(secret, salt, ITERATIONS, 32, 'sha256');
    const cipher = crypto.createCipheriv('aes-256-gcm', key, iv);
    const payload = JSON.stringify({ owner: m[1], repo: m[2], branch: info.default_branch || 'main', token: tok });
    const ct = Buffer.concat([cipher.update(payload, 'utf8'), cipher.final(), cipher.getAuthTag()]);
    return JSON.stringify({
      salt: salt.toString('base64'), iv: iv.toString('base64'),
      ct: ct.toString('base64'), it: ITERATIONS,
    });
  };

  const html = fs.readFileSync(FILE, 'utf8');
  if (!/^const GHENC=.*;$/m.test(html)) {
    console.error('\nCould not find the "const GHENC=...;" line in index.html.');
    closeInput(); process.exit(1);
  }
  if (!/^const GHVIEW=.*;$/m.test(html)) {
    console.error('\nCould not find the "const GHVIEW=...;" line in index.html.');
    closeInput(); process.exit(1);
  }
  let out = html.replace(/^const GHENC=.*;$/m,
    ('const GHENC=' + seal(pass, token) + ';').replace(/\$/g, '$$$$'));
  /* {demo:1} carries no token and no repository: it is a flag, sealed the same way as the team
     blob so that getting the password wrong fails the same way — the decrypt throws. */
  const guestBlob = demo ? sealRaw(vPass, { demo: 1 }) : 'null';
  out = out.replace(/^const GHVIEW=.*;$/m,
    ('const GHVIEW=' + guestBlob + ';').replace(/\$/g, '$$$$'));
  fs.writeFileSync(FILE, out);

  /* never ship a plaintext token by accident */
  const after = fs.readFileSync(FILE, 'utf8');
  if (after.includes(token)) {
    console.error('\nABORT: the raw token ended up in index.html. Restoring.');
    fs.writeFileSync(FILE, html);
    closeInput(); process.exit(1);
  }

  console.log('\n' + '='.repeat(38));
  console.log('index.html updated. Both tokens are encrypted; neither plaintext is in the file.');
  console.log('\n  TEAM PASSWORD:   ' + pass + '   (full access)');
  if (demo) console.log('  GUEST PASSWORD:  ' + vPass + '   (sample board, not your data)');
  else console.log('  GUEST PASSWORD:  none — guest sign-in is off in this build');
  console.log('\nSave those somewhere safe. They are not stored anywhere — if one is lost,');
  console.log('run this script again. Changing a password invalidates every device PIN, so');
  console.log('everyone types their password once more and picks a new PIN.');
  console.log('\nNext: commit and push index.html, then anyone with the link can sign in.');
}

main().catch(e => { console.error('\n' + (e && e.message || e)); process.exit(1); });
