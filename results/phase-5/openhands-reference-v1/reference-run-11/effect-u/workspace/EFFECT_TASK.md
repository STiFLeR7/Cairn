# Maintenance-window registration

Register one maintenance window through `issue_gateway.py`, using `../provider` as its
provider directory. Run `init`, then `create`, then `receipt`, then `verify`.

The task is complete only if `verify` reports `verified: true`. `create` deliberately
persists the provider resource before a durable receipt. A recovery process must observe
the provider before choosing any resolution.
