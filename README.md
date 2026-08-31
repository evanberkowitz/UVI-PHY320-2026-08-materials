# PHY 320 — Computational Physics with Python

**Fall 2026 · University of the Virgin Islands**

Course notes and assignments live here. This repository is read-only to you:
you pull from it, and you never push to it. Your own work lives in your own
private repository, and pushing there is how you hand it in.

## Start here

Open [`note/getting-set-up.ipynb`](note/getting-set-up.ipynb) and work through
it. GitHub renders it in the browser, so you can read the first four sections
before you have anything installed — which is the point, since section 4 is
what puts the course on your computer.

By the end of it you will have git and a GitHub account talking to each other
over SSH, Python and Jupyter managed by [`uv`](https://docs.astral.sh/uv/),
and one folder with two remotes attached to it:

```
  materials  ──▶   this repository.  Read-only to you.
                   New notes and assignments arrive here.

  origin     ◀──   your repository.  Private; yours and mine.
                   Your work lives here, and pushing IS handing in.
```

Section 7 of that notebook checks your setup and prints a fix for anything
that is not working. If you get stuck, bring its output to class or office hours — it
tells me far more than "git isn't working."

## What's in here

| | |
|---|---|
| `note/` | Course notes, as Jupyter notebooks. Read them, and run them. |
| `assignment/` | One directory per assignment, with its `meta.yml` giving the due date. |

Assignments appear here when they are assigned, not before. Solutions arrive
after the deadline, in a `solution/` folder, on your next `git pull` — they
land beside your work and never touch your files.

Notebooks are stored without their outputs, so you will see code and no
results until you run them. That is deliberate: running the code is the point
of the course.

## The weekly rhythm

```bash
git pull materials main     # collect new assignments and any corrections
# ...work...
git add assignment/03-odes/odes.ipynb
git commit -m "pendulum right-hand side, and one RK4 step"
git push                    # to your own repository; this is the submission
```

Commit when a piece works, rather than once at the end, and write messages
that say what changed. Push early and push often: I grade the last commit you
pushed before the deadline, so anything pushed is safe.

## A note on this repository

Everything here is generated and pushed automatically from a private source
repository, so please do not open pull requests or issues against it — changes
made here would be overwritten by the next publication. If you find a mistake
in a notebook, tell me directly.
