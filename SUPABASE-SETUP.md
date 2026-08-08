# DevSamosa — one shared board across all your devices

Right now each browser keeps its own copy of the data. This connects the app to a free
Supabase database so your laptop, your phone and your team all read and write the **same board**.

Total time: about 15 minutes. No servers to run, no monthly cost at your size.

---

## 1. Create the database (5 min)

1. Go to **supabase.com**, sign up, click **New project**.
2. Name it `devsamosa`. Pick a region near you — **Mumbai (ap-south-1)** if you're in India.
3. Set a database password (you won't need it in the app; save it anyway).
4. Wait for the project to finish provisioning.

## 2. Create the table (2 min)

Open **SQL Editor** in the left sidebar, paste all of this, and press **Run**.

```sql
-- one row holds the whole board; version stops two devices overwriting each other
create table public.board (
  id          text primary key,
  data        jsonb not null default '{}'::jsonb,
  version     bigint not null default 1,
  updated_at  timestamptz not null default now()
);

insert into public.board (id, data, version) values ('main', '{}'::jsonb, 1);

-- lock it down: only signed-in people can read or write
alter table public.board enable row level security;

create policy "signed in can read"   on public.board
  for select to authenticated using (true);

create policy "signed in can update" on public.board
  for update to authenticated using (true) with check (true);

create policy "signed in can insert" on public.board
  for insert to authenticated with check (true);
```

**Why this is safe.** The anon key sits in the HTML where anyone can read it — that's how Supabase
is designed. Security comes from those policies: the key alone gets you nothing, because every
policy requires `authenticated`. Only someone with a real account can see your data.

## 3. Turn off open sign-ups (1 min)

By default anyone who finds your URL could create an account.

Go to **Authentication → Providers → Email** and turn **Enable sign ups** off.
Then add your team yourself under **Authentication → Users → Add user** (set a password,
tick *Auto Confirm User*). They can change it later via *Forgot password*.

If you'd rather people self-register, leave sign-ups on but keep **Confirm email** enabled.

## 4. Get your two values (1 min)

**Settings → API**:

- **Project URL** — looks like `https://abcdefgh.supabase.co`
- **anon public** key — a long string starting `eyJ...`

Do **not** copy the `service_role` key. That one bypasses every policy.

## 5. Host the app (3 min)

Drag `devsamosa.html` onto **app.netlify.com/drop**. You get a permanent URL.
Rename the file to `index.html` first if you want a tidier address.

GitHub Pages, Cloudflare Pages or your own IIS box all work the same way.

## 6. Connect (2 min)

Open your new URL. The app asks for the Project URL and anon key — paste them, hit **Connect**,
then create your account or sign in.

On each other device: open the same URL, paste the same two values once, sign in. That's it —
same board everywhere.

**On your phone:** open the URL in Safari or Chrome → **Share → Add to Home Screen**. It opens
full-screen with the samosa icon.

---

## How syncing behaves

- Your changes save as you type, as before.
- Other devices pick them up **within 15 seconds**, or instantly when you switch back to the tab.
- Polling pauses while you're typing or dragging, so the screen never jumps under your hands.
- If two people save at once, the second save is **refused rather than allowed to overwrite**.
  That device reloads the other person's version and tells you. Nothing is silently lost.

That last point is the honest limit of this design: the board is a single document, so simultaneous
editing means one person reloads. For a standup where one person drives, this is the right
trade — it's simple and it cannot corrupt data. If you ever need genuine multi-editor
collaboration, that's a different schema (one row per update) and a bigger change.

## Falling back

- **Use this device only** on the connect screen returns to local storage.
- **••• → Sign out of team board** signs out but keeps the connection.
- **••• → Use a shared team database** connects a local install later.
- Before switching, take **••• → Download backup** — local and cloud data are separate stores.

## Moving your existing data up

On the device that has your real data: **••• → Download backup**. Then sign in to the cloud
version and use **••• → Restore from a file**. The board uploads and everyone sees it.

## Cost

Supabase's free tier covers 500 MB of database and 50,000 monthly active users. This app stores a
few hundred kilobytes and has 18 people. You will not approach the limits.

One caveat: free projects **pause after 7 days with no activity**. Daily standup use keeps it
awake. If it ever pauses, un-pause it from the dashboard — no data is lost.
