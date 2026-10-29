# Lab 1 — AI-Assisted Coding

**CSP352: AI-Augmented Software Development — Week 1**

Today you use an AI coding assistant (Aider) for real software engineering
tasks: writing code from a prompt, refining a prompt when the first result
is wrong, and debugging with the assistant's help. The goal isn't "get the
assistant to write everything" -- it's learning to direct it well, read what
it produces critically, and know when to push back.

This lab runs across **two separate 2-hour sessions, Wednesday and
Friday (10:30--12:30)** -- not one 4-hour block. Each session has its
own deliverable, due by the end of that session, not carried over to
"finish later." (If you're reading this during the Week 1 lecture on
Tuesday: this isn't today -- today's warm-up is in `lab-00-course-intro`.)

## Setup — do this first, every time

Your assistant API key is already configured. Your Gitea account and a
copy of this repo were pre-created for you -- **but you still need to
clone it** before running anything, or your work won't be tracked (no
git repo = no commits = nothing to grade).

**Log in to Gitea first**, at https://git.aisd-lab.iitbhilai.ac.in, using
**"Sign in with keycloak"** -- the same Google account as your workspace
login. There is no separate Gitea password to remember or ask anyone for.

**Then generate a personal access token** (needed once, for `git clone`/
`push` -- a browser login alone doesn't cover git operations): click your
avatar (top right) -> Settings -> Applications -> "Generate New Token" ->
give it any name, then under **Repository** select **Read and Write**
(Gitea uses separate scope checkboxes per category, unlike GitHub's
single `repo` toggle -- picking only "Read" here is the single most
common way to get a `403 Forbidden` on `git push` while `git clone`/
`pull` and even the token itself work fine) -> Generate Token -> **copy
it immediately, it's shown to you only once.**

**Tell git to remember it** (one-time -- skip this and you'll be asked
to paste the token on every single `push`/`pull`, which gets old fast):

```bash
git config --global credential.helper store
```

In a terminal:

```bash
git clone https://<your-username>@git.aisd-lab.iitbhilai.ac.in/<your-username>/lab-01-ai-assisted-coding.git
cd lab-01-ai-assisted-coding
```

(Replace `<your-username>` with your actual Gitea username, lowercase --
**this is not necessarily your official institute roll number**; it's the
username your account was created with. If unsure, check the URL of your
own repo after logging in, or ask before the session starts.)

When it asks for a password, **paste your personal access token** -- not
your Google password, and not a Gitea password (you never set one). With
`credential.helper store` set above, this is the only time you'll need
to paste it -- git saves it and reuses it automatically after this.

**Always run `aider` from inside this cloned directory**, not your bare
home folder -- that's what makes your work an actual git repo the
instructors can see the history of.

## Session 1 (Wednesday, 10:30--12:30) — first prompts

| Time | Exercise |
|---|---|
| 15 min | Orientation -- first prompt, read the diff before accepting |
| 90 min | `exercises/01_first_prompt/` and `exercises/02_prompt_refinement/` |
| 15 min | Commit and push what you have |

**Submit by pushing before Session 1 ends.** This is graded on its own --
not a draft to be finished in Session 2.

```bash
git add -A
git commit -m "session 1: first prompt + refinement"
git push
```

## Session 2 (Friday, 10:30--12:30) — debugging with an assistant

| Time | Exercise |
|---|---|
| 90 min | `exercises/03_debugging/` |
| 30 min | Write `NOTES.md`, commit, push |

**Submit by pushing before Session 2 ends.**

```bash
git add -A
git commit -m "session 2: debugging + notes"
git push
```

## How this is graded

Not by whether your final code is "correct" in isolation -- by the
**process**: your commit history, and your gateway trace (every assistant
call you made is logged server-side). A large jump in code with almost no
assistant activity in the window looks like you didn't actually do the
exercise here, and gets flagged for a quick chat, not an automatic penalty.
Random weekly viva sampling (~10 students) walks through *why* you made a
specific prompt or fix -- the graded skill is designing the interaction, not
just producing output. Each session's push is graded as its own checkpoint.
