# Archive registration

Register one archive job through `archive_gateway.py`, using `../provider` as its provider directory.
Run `init`, then `create`, then `receipt`, then `verify`.

The task is complete only if `verify` reports `verified: true`. `create` deliberately commits the
provider resource before the durable receipt. A recovery process must observe the provider before
choosing any resolution.
