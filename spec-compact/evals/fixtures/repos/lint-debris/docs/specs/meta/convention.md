# Spec conventions

Artifact classes and their filename prefixes:

| Class | Filename | Content lifetime |
|---|---|---|
| `requirements` | `requirements.md`, `requirements_<topic>.md` | Permanent — acceptance criteria, numbered requirement IDs. |
| `design` | `design_<topic>.md` | Long-lived — decisions, components, data model. |
| `plan` | `plan_<topic>.md` | Transient — implementation worklist for one feature. |
| `index` | `index.md` | Generated map of the spec tree. |

One topic folder per module. Requirement IDs are referenced as `requirements.md#6.2`.
