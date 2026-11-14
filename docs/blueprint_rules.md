# Blueprint to rules (src/env)
A cell may be placed iff it is: a **target**, **not built**, **supported** and **order_ok**.
- **Supported:** a *seed* (the cell of each connected piece nearest a depot) or 4-adjacent to a built block.
- **order_ok:** after placing it, every other unbuilt target is still reachable from a depot by walking over cells that are
  not rocks and not built. This is the "never close a gap that would later be unreachable" rule.
- **Compiler check:** `RuleSet.check_buildable` / `verify_buildable` builds the blueprint in random legal orders and reports a dead end.
  Example of a rejected blueprint: a one-row corridor `D.##.` (see `tests/test_rules.py`).
Formats: JSON, or ASCII text (`#` target, `.` free, `D` depot, `X` rock).
