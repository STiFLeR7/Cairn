# OpenHands P5.1 capability acquisition

Pinned host: `openhands-sdk==1.42.1` plus `openhands-tools==1.42.1`, in an
isolated Python environment. This is capability evidence only: it is neither a
Cairn adapter nor a sealed portability workload.

`openhands_capability_probe.py` exercised only released host APIs. The control
proved all P5.1 prerequisites:

1. `LocalConversation.condense()` appended `Condensation` and changed the
   active host view from 17 events to 6.
2. A fresh process re-opened the same persisted condensation state.
3. The host-owned Windows terminal tool emitted `ActionEvent` before
   `ObservationEvent` and wrote `P5_OPENHANDS_TOOL_EVENT` into its workspace.
4. A process owning a durable two-event conversation was force-terminated; a
   different Python process re-opened that conversation from persistence.

`run/` contains the host's persisted state, event files, and workspace marker.
The first crash-control attempt failed before readiness because the probe's
`agent()` return was misplaced; its logs are retained as probe-defect evidence,
and its process was never killed. The second attempt is the admitted control.

This admits only the OpenHands P5.1 host-capability boundary. It does not admit
two-host portability, recovery conformance, a real-model result, or a Cairn
contract change.
