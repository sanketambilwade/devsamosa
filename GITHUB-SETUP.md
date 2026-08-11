# DevSamosa on GitHub — the app and the board, both free

This puts the app on the web and keeps the board in a private repository, so your laptop, your
phone and your team all read and write the same data. No database, no monthly cost, and every
save is kept in the repo's history so you can always go back.

Total time: about 15 minutes.

---

## What you end up with

Two repositories. The split is what keeps it free *and* private:

| repo | visibility | holds |
|---|---|---|
| `devsamosa` | **public** | `index.html` only — the app itself, served by GitHub Pages |
| `devsamosa-data` | **private** | the board: your people, projects and daily updates |

The app is public because GitHub Pages only serves free sites from public repos. That's fine —
it's just the program, the same file you already have. **Your data is never in it.** The board
lives in the private repo, and only someone holding a token you created can read it.

---

## 1. Put the app online (5 min)

1. On github.com click **New repository**. Name it `devsamosa`, leave it **Public**, create it.
2. Click **uploading an existing file** and drag in **`index.html`**. Pages looks for that exact
   name, which is why the app file is called that. Commit.
3. Go to **Settings → Pages**. Under *Build and deployment*, set Source to **Deploy from a branch**,
   branch **main**, folder **/ (root)**. Save.

Only upload `index.html` and the two setup guides. **Don't upload `CLAUDE.md`** — it names your
clients and your team, and this repo is public. The `.gitignore` already excludes it if you push
with git instead.

After a minute your app is live at `https://<your-username>.github.io/devsamosa/`.

## 2. Make the data repository (2 min)

**New repository** again. Name it `devsamosa-data`, set it to **Private**, and tick
**Add a README file** so it isn't empty. Create it.

Don't put anything else in it — the app writes its own files.

## 3. Make an access token (4 min)

This is what lets the app write to that private repo from your browser.

1. Go to **github.com/settings/personal-access-tokens** (Settings → Developer settings →
   Personal access tokens → **Fine-grained tokens**).
2. **Generate new token.** Name it `devsamosa`.
3. **Repository access** → *Only select repositories* → pick **`devsamosa-data`**. Nothing else.
4. **Permissions** → *Repository permissions* → find **Contents** → set it to **Read and write**.
   Leave everything else alone.
5. Set an expiry you're happy with, generate, and **copy the token now** — GitHub shows it once.

That token can touch that one repository and nothing else in your account. If it ever leaks,
delete it on this page and make another.

## 4. Connect (2 min)

Open your Pages URL. On the connect screen:

- **Data repository** — `yourusername/devsamosa-data`
- **Access token** — paste it

Hit **Connect**, then create your login (username, password, secret number).

The board starts **empty** — your team and client names are deliberately not baked into the app,
because the app file is public. Load them once with **••• → Restore from a file** and pick
`starter-board.json` (it's in this folder, next to this guide). That puts your 18 developers and
13 projects in, and from then on everything lives in the private repo. You only ever do this once.

Keep `starter-board.json` off the public repo — the `.gitignore` already excludes it.

**On each other device:** open the same URL, paste the same two values once, sign in with the
password you just made. Same board everywhere.

**On your phone:** open the URL in Safari or Chrome → **Share → Add to Home Screen**. It opens
full-screen with the samosa icon.

---

## 5. One shared password, so nobody else has to do any of this (5 min)

Steps 3 and 4 are per-device, which gets old fast if you're handing the link around. Run this once
and everyone else just needs the link and a password:

```
node setup-shared-login.js
```

It asks for the repository and your token, checks the token works, and encrypts both into
`index.html`. Then commit and push that file.

From then on, on any device:

1. **First time only** — type the team password, then pick a **4-digit PIN** for that device.
2. **Every time after** — just the PIN, on a numeric keypad.

There is no username. One password, one board, everyone sees the same thing.

The script suggests a five-word password like `cedar-lantern-quartz-meadow-ripple`. Use it. It's
strong enough for the encrypted blob to be published, and short enough to read out on a call.

### Why the PIN isn't the password

They protect different things, which is why the short one is safe and the long one is needed.

The team password guards a file that is **published on the internet**. Anyone can download it and
guess at it offline, as fast as their hardware allows — nothing can rate-limit them, because there
is no server. Four digits would fall in about a second; five random words would take longer than
the universe has existed.

Your PIN guards a copy that lives **only in that browser**, and is wiped after five wrong tries.
To attack it someone needs your unlocked phone first, at which point the PIN is the least of your
problems. That's the same split your banking app uses.

If you forget the PIN, tap **Forgot your PIN?** and sign in with the team password again.

### What you're trading

The encrypted blob sits in `index.html`, which is public. Nobody can get anything out of it without
the password — it's AES-256 with 600,000 rounds of key stretching — but **the password becomes the
only thing protecting the board.** That means:

- Use the generated password, not `devsamosa2026`. A guessable one is the whole attack.
- Share it the way you'd share a door code, and don't post it anywhere public.
- Anyone who has it can read and edit everything. There's no per-person access, which is what you
  wanted — just be deliberate about who gets it.

To change the password or rotate the token, run the script again and push. Everyone signs in with
the new password next time; nothing is lost.

### Or: separate access per person

If you'd rather each person be individually revocable, skip the shared password. Invite them to
`devsamosa-data` (Settings → Collaborators) and have them make their **own** token by repeating
step 3. Their edits then show up under their own name in the repo's history, and you can remove
just them later without disturbing anyone else.

---

## How syncing behaves

- Your changes save as you type, as before.
- Other devices pick them up **within 15 seconds**, or instantly when you switch back to the tab.
- Polling pauses while you're typing or dragging, so the screen never jumps under your hands.
- Each developer's updates live in their own file. Two people editing **different** developers
  never collide — both saves land. Only two people editing the **same** developer at the same
  moment will make one of them reload, and nothing is silently lost when that happens.

## Your backups are automatic now

Every save is a commit. Open `devsamosa-data` on github.com and click **History** to see every
version of the board that has ever existed, with the date and who made it. Click any entry to see
exactly what changed, and **⋯ → View file** to read the board as it stood that day.

This is a real backup: it's off your device, it's versioned, and nothing overwrites it. The in-app
**••• → Backups & undo** snapshots still work too — those are faster for an accidental delete, but
they only live in the browser you took them in.

## Moving your existing data in

On the device that has your real data: **••• → Download backup**. Then open the GitHub version and
use **••• → Restore from a file**. The board uploads and everyone sees it.

## Falling back

- **Use this device only** on the connect screen returns to local storage.
- **••• → Disconnect team repo** forgets the repo and token on that device. Your data stays in the
  repo, untouched.
- The **Use a Supabase database instead** link on the connect screen is still there if you ever
  want it.

---

## Cost and limits

Free, permanently. Public repos, private repos, Pages and the API are all free at this size, and
**nothing pauses if you stop using it for a while.**

Two limits exist, and you are nowhere near either:

- **5,000 API requests per hour.** A busy standup uses around 300. Idle polling uses 240 an hour.
- **Roughly 500 writes per hour.** A standup makes a few dozen.

The one thing to keep an eye on is **token expiry**. When the token you made in step 3 runs out,
the app says it was rejected — make a new one the same way and paste it in. Put a reminder in your
calendar a week before, and you'll never notice it.

## The honest limit

Everyone shares one login to the app itself, and the board is one document split across files.
That suits a standup where one person types while listening. If you ever want all 18 developers
signing in as themselves and editing their own rows, that's a different shape of thing — every
person would need a GitHub account and their own token, and at that point a real database with
proper accounts is the better answer.
