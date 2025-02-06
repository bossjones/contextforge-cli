# Git Commit Message Convention

| This is based on [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/#summary)

## Commit Message Format

A commit message consists of a **header**, **body** and **footer**. The header has a **type**, **scope** and
**subject**. The commit message should be structured as follows:

```markdown
<type>(<scope>): <subject>

<body>

<footer>
```

The **scope**, **body** and **footer** are optional.

## Type

Possible types are :

| Type     | Description                                        |
| -------- | -------------------------------------------------- |
| build    | a change that affect the build or dependencies     |
| chore    | a change that does not affect source or test files |
| ci       | a change in CI config files or scripts             |
| docs     | a change to documentation                          |
| feat     | a new feature                                      |
| fix      | a bug fix                                          |
| perf     | a change in the code to improve performance        |
| refactor | a change in the code (neither a feature or fix)    |
| revert   | a revert of a previous commit                      |
| style    | a change in the code format                        |
| test     | a new test or test correction                      |

## Scope

The scope specify where the change was made. For example, a **component** `button` or **file name** `readme`.

## Subject

The subject contains a brief imperative description of the change.

- use the imperative present tense, for example `change`, not `changed` nor `changes`.
- do not capitalize the first letter, for example `change`, not `Change`.
- do not use the dot `.` at the end.

## Body

The body contains an imperative explanation of the change. It should specify the **why** and **how** the change was
made.

## Footer

The footer contains any information about **breaking changes** or a reference to an existing Github **issue** or **pull
request**. A breaking change should start with `BREAKING CHANGE:` followed by its description.

## Examples

See [Conventional Commits examples](https://www.conventionalcommits.org/en/v1.0.0/#examples).
