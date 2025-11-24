# History cleanup — .venv-node removed

On 2025-11-23 we removed the `.venv-node` directory from the repository history to reduce repo size and remove committed virtualenv artifacts.

What changed
- The `.venv-node` directory was removed from all commits, branches and tags.
- The repository history has been rewritten and force-pushed to the remote.

Backups
- A full repository bundle was created and left in the parent directory (example filename starts with `kimberly-backup-before-filter-repo-`). Keep this safe if you need to restore the earlier history.

Important for contributors
- Because history was rewritten, your local clones and branches that existed prior to this change will be incompatible with the remote.

Recommended steps for collaborators
1. Save any local changes you haven't published (e.g., create patches or branches).
2. The easiest way to avoid issues is to re-clone the repository:

   git clone https://github.com/cmh-demos/kimberly.git

   or, if you must keep an existing clone, reset safely:

   git fetch origin
   git checkout <branch-you-want>
   git reset --hard origin/<branch-you-want>

3. For local branches with commits you want to keep, create a new branch and rebase or cherry-pick them onto the updated tips.

If you'd like me to also remove the repository backups or take additional cleanup steps (or to purge other folders), ask and I can help coordinate.

---

# History cleanup — node_modules removed

We also removed all tracked `node_modules/` entries from repository history on 2025-11-23.

What changed
- Any committed files under `node_modules/` were removed from all commits and refs.
- The repository history was rewritten and force-pushed to the remote to reflect these changes.

Backups
- A second full repo bundle (backup) was created and saved one directory up; filename starts with `kimberly-backup-before-filter-repo-node_modules-`.

Important for contributors
- Because history was rewritten again, everyone will need to resync their local clones (re-clone or reset) just like the earlier item above.

Recommended steps for collaborators
1. Re-clone the repository or reset your local branches:

   git clone https://github.com/cmh-demos/kimberly.git

   or

   git fetch origin
   git checkout <branch-you-want>
   git reset --hard origin/<branch-you-want>

2. If you have local work to keep, create patches or a temporary branch and rebase/cherry-pick onto the new tips.

