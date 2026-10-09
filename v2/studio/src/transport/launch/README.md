# Campaign launch transport

Owner UI-01.06/L3. Generated published launch DTOs validate every request/response.
LaunchSubmission wraps the immutable original Runtime admission wire bytes in a
campaign.launch envelope with identical actor/scope/request identity and installed
profile pin. No client-side canonical hash is claimed. Receipt validation checks
profile/identity, monotonic revision, immutable admission binding, accepted run,
terminal state and worker bounds. Returned records are recursively frozen.

LaunchClient uses only same-origin Deployment routes, HttpOnly session cookies and
bounded JSON/timeouts. It sends no owner credential, shell command or Runtime POST.
Safe failures distinguish denied/missing/busy/conflict without exposing owner text.
No automatic POST retry. Module tests: tests/transport/launch. Live qualification
is separate from these synthetic transport tests.
