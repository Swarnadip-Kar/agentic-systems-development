# Course Intro — Warm-Up (ungraded)

**CSP352: AI-Augmented Software Development — Week 1 lecture**

This is a short, ungraded warm-up we do together, live, during today's
lecture -- not Lab 1. The point is just to get the clone -> prompt ->
verify -> push flow into your hands once, with the instructor there,
before you do it for real (and for a grade) starting **Wednesday**.

## Setup (same as every lab, from now on)

**Log in to Gitea first**, at https://git.aisd-lab.iitbhilai.ac.in, using
**"Sign in with keycloak"** -- the same Google account as your workspace
login.

**Generate a personal access token** (one-time): avatar (top right) ->
Settings -> Applications -> "Generate New Token" -> tick the `repo`
scope -> Generate Token -> copy it, it's shown only once.

**Tell git to remember it** (one-time, so you never have to paste it
again):

```bash
git config --global credential.helper store
```

```bash
git clone https://<your-username>@git.aisd-lab.iitbhilai.ac.in/<your-username>/lab-00-course-intro.git
cd lab-00-course-intro
```

Password prompt -> paste your personal access token **once**. Because of
`credential.helper store` above, git saves it after this first time --
every `push`/`pull` after this just works, no more prompts.

## Three quick exercises (do these now, together)

**1. A first prompt.** Ask your assistant (`aider`) to write
`is_palindrome(s)`: returns `True` if `s` reads the same forwards and
backwards (ignore case), `False` otherwise. Watch it plan, edit, and
write a test. Read the diff before accepting it.

**2. The good case.** Ask for `merge_overlapping_intervals(intervals)`:
given a list of `(start, end)` integer pairs, return them merged, sorted
by start, with no overlaps. Include a test file using pytest. Watch it
plan, edit, write a test, and pass on the first run -- this is the
common case, and it's why the tool is trusted.

**3. The confidently wrong case.** Ask for `count_nearby_robots(coords,
threshold)`: given a list of `(x, y)` integer coordinates and a distance
threshold, return the number of distinct pairs currently within
`threshold` of each other (Euclidean distance). Include a test file
using pytest. It will look correct, read confidently, and its own test
will pass -- **but don't stop there.** Ask yourself: what happens if
this ran on 20,000 points instead of 3? Time it:

```python
import random, time
coords = [(random.randint(0, 10000), random.randint(0, 10000)) for _ in range(20000)]
start = time.time()
count_nearby_robots(coords, threshold=5)
print(f"{time.time() - start:.1f}s for {len(coords)} robots")
```

The nested loop is $O(n^2)$: instant on the 3-point test, but it never
finishes in time to matter at real scale. No functional test the
assistant writes can catch this -- a unit test checks whether the
answer is right, not whether it arrives fast enough. The fix was never
"ask it to try harder" -- it's *you* bringing a requirement (scale)
that was never in the prompt, because the assistant has no way to know
it matters unless told.

## Push when you're done

```bash
git add -A
git commit -m "warm-up done"
git push
```

Nothing here is graded. Lab 1 -- the real thing -- starts Wednesday.
