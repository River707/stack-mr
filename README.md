# Stacked MRs for GitLab

This is a command-line tool that helps you create multiple GitLab
merge requests (MRs) all at once, with a stacked order of dependencies.

Imagine that we have a change `A` and a change `B` depending on `A`, and we
would like to get them both reviewed. Without stacked MRs one would have to
create two MRs: `A` and `A+B`. The second PR would be difficult to review as it
includes all the changes simultaneously. With stacked MRs the first PR will
have only the change `A`, and the second PR will only have the change `B`. With
stacked MRs one can group related changes together making them easier to
review.

Example:
![StackedPRExample1](https://modular-assets.s3.amazonaws.com/images/stackpr/example_0.png)

## Dependencies

This is a non-comprehensive list of dependencies required by `stack-mr.py`:

- Install `glab`, e.g. via [homebrew](https://gitlab.com/gitlab-org/cli/#installation): `brew install glab`.
- Run `glab auth login` with SSH

## Installation

Manually, you can clone the repository and run the following command:

```bash
pipx install .
```

## Workflow

`stack-mr` is a tool allowing you to work with stacked MRs: export,
view, and land them.

The `stack-mr` tool has four commands:

- `export` (or `submit`) - create a new stack of MRs from the given set of
  commits. One can think of this as “push my local changes to the corresponding
  remote branches and update the corresponding MRs (or create new MRs if they
  don’t exist yet)”.
- `view` - inspect the given set of commits and find the linked MRs. This
  command does not push any changes anywhere and does not change any commits.
  It can be used to examine what other commands did or will do.
- `abandon` - remove all stack metadata from the given set of commits. Apart
  from removing the metadata from the affected commits, this command deletes
  the corresponding local and remote branches and closes the MRs.
- `land` - merge MRs from the stack corresponding to the given set of commits.
  This command attempts to merge MRs from the stack one by one, and if
  succeeded deletes the corresponding branches from local and remote repos.

A usual workflow is the following:

```bash
while not ready to merge:
    make local changes
    commit to local git repo or amend existing commits
    create or update the stack with `stack-mr.py export`
merge changes with `stack-mr.py land`
```

You can also use `view` at any point to examine the current state, and
`abandon` to drop the stack.

Under the hood the tool creates and maintains branches named
`$USERNAME/stack/$BRANCH_NUM` and embeds stack metadata into commit messages,
but you are not supposed to work with those branches or edit that metadata
manually. I.e. instead of pushing to these branches you should use `export`,
instead of deleting them you should use `abandon`, and instead of merging them
you should use `land`.

The tool looks at commits in the range `BASE..HEAD` and creates a stack of MRs
to apply these commits to `TARGET`. By default, `BASE` is `main` (local
branch), `HEAD` is the git revision `HEAD`, and `TARGET` is `main` on remote
(i.e. `origin/main`). These parameters can be changed with options `-B`, `-H`,
and `-T` respectively and accept the standard git notation: e.g. one can use
`-B HEAD~2`, to create a stack from the last two commits.

After creating a stack, an in-place rebase (`git rebase -i HEAD~N`) can be used
to edit commits in the stack (such as to address review feedback), add new
commits to the stack, etc.

### Example

The first step before creating a stack of MRs is to double-check the changes
we’re going to post.

By default the tool will look at commits in `main..HEAD` range and will create
a PR for every commit in that range.

For instance, if we have

```bash
# git checkout my-feature
# git log -n 4  --format=oneline
**cc932b71c** (**my-feature**)        Optimized navigation algorithms for deep space travel
**3475c898f**                         Fixed zero-gravity coffee spill bug in beverage dispenser
**99c4cd9a7**                         Added warp drive functionality to spaceship engine.
**d2b7bcf87** (**origin/main, main**) Added module for deploying remote space probes

```

Then the tool will consider the top three commits as changes, for which we’re
trying to create a stack.

> **Pro-tip**: a convenient way to see what commits will be considered by
> default is the following command:
>

```bash
alias githist='git log --abbrev-commit --oneline $(git merge-base origin/main HEAD)^..HEAD'
```

We can double-check that by running the script with `view` command - it is
always a safe command to run:

```bash
# stack-mr view
...
VIEW
**Stack:**
   * **cc932b71** (No MR): Optimized navigation algorithms for deep space travel
   * **3475c898** (No MR): Fixed zero-gravity coffee spill bug in beverage dispenser
   * **99c4cd9a** (No MR): Added warp drive functionality to spaceship engine.
SUCCESS!
```

If everything looks correct, we can now export the stack, i.e. create all the
corresponding MRs and cross-link them. To do that, we run the tool with
`export` command:

```bash
# stack-mr export
...
SUCCESS!
```

The command accepts a couple of options that might be useful, namely:

- `--draft` - mark all created MRs as draft. This helps to avoid over-burdening
  CI.
- `--draft-bitmask` - mark select MRs in a stack as draft using a bitmask where
    `1` indicates draft, and `0` indicates non-draft.
    For example `--draft-bitmask 0010` to make the third PR a draft in a stack
    of four.
    The length of the bitmask must match the number of stacked MRs.
    Overridden by `--draft` when passed.
- `--reviewer="handle1,handle2"` - assign specified reviewers.

If the command succeeded, we should see “SUCCESS!” in the end, and we can now
run `view` again to look at the new stack:

```python
# stack-mr view
...
VIEW
**Stack:**
   * **cc932b71** (!439, 'rriddle/stack/103' -> 'rriddle/stack/102'): Optimized navigation algorithms for deep space travel
   * **3475c898** (!438, 'rriddle/stack/102' -> 'rriddle/stack/101'): Fixed zero-gravity coffee spill bug in beverage dispenser
   * **99c4cd9a** (!437, 'rriddle/stack/101' -> 'main'): Added warp drive functionality to spaceship engine.
SUCCESS!
```

We can also go to gitlab and check our MRs there:

![StackedPRExample2](https://modular-assets.s3.amazonaws.com/images/stackpr/example_1.png)

If we need to make changes to any of the MRs (e.g. to address the review
feedback), we simply amend the desired changes to the appropriate git commits
and run `export` again. If needed, we can rearrange commits or add new ones.

When we are ready to merge our changes, we use `land` command.

```python
# stack-mr land
LAND
Stack:
   * cc932b71 (!439, 'rriddle/stack/103' -> 'rriddle/stack/102'): Optimized navigation algorithms for deep space travel
   * 3475c898 (!438, 'rriddle/stack/102' -> 'rriddle/stack/101'): Fixed zero-gravity coffee spill bug in beverage dispenser
   * 99c4cd9a (!437, 'rriddle/stack/101' -> 'main'): Added warp drive functionality to spaceship engine.
Landing 99c4cd9a (!437, 'rriddle/stack/101' -> 'main'): Added warp drive functionality to spaceship engine.
...
Rebasing 3475c898 (!438, 'rriddle/stack/102' -> 'rriddle/stack/101'): Fixed zero-gravity coffee spill bug in beverage dispenser
...
Rebasing cc932b71 (!439, 'rriddle/stack/103' -> 'rriddle/stack/102'): Optimized navigation algorithms for deep space travel
...
SUCCESS!
```

This command lands the first PR of the stack and rebases the rest. If we run
`view` command after `land` we will find the remaining, not yet-landed MRs
there:

```python
# stack-mr view
VIEW
**Stack:**
   * **8177f347** (!439, 'rriddle/stack/103' -> 'rriddle/stack/102'): Optimized navigation algorithms for deep space travel
   * **35c429c8** (!438, 'rriddle/stack/102' -> 'main'): Fixed zero-gravity coffee spill bug in beverage dispenser
```

This way we can land all the MRs from the stack one by one.

## Specifying custom commit ranges

The example above used the default commit range - `main..HEAD`, but you can
specify a custom range too. Below are several commonly useful invocations of
the script:

```bash
# Export a stack of last 5 commits
stack-mr export -B HEAD~5

# Use 'origin/main' instead of 'main' as the base for the stack
stack-mr export -B origin/main

# Do not include last two commits to the stack
stack-mr export -H HEAD~2
```

These options work for all script commands (and it’s recommended to first use
them with `view` to double check the result). It is possible to mix and match
them too - e.g. one can first export the stack for the last 5 commits and then
land first three of them:

```bash
# Inspect what commits will be included HEAD~5..HEAD
stack-mr view -B HEAD~5
# Create a stack from last five commits
stack-mr export -B HEAD~5

# Inspect what commits will be included into the range HEAD~5..HEAD~2
stack-mr view -B HEAD~5 -H HEAD~2
# Land first three MRs from the stack
stack-mr land -B HEAD~5 -H HEAD~2
```
