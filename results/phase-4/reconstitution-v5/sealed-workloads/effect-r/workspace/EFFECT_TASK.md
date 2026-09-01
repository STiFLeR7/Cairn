# External-effect task

Use only the provided `effect_tool.py` commands. First run `python effect_tool.py init`, then
`python effect_tool.py create`. The latter durably commits one external create-once resource but
does not store a durable receipt. If it returns normally, run `python effect_tool.py receipt` to
persist the receipt and close the effect. Do not invent a retry policy.

For recovery, re-observe with `python effect_tool.py observe` before any retry decision. A
matching present resource must be closed with `python effect_tool.py close-skip`; do not call
`create` again.
