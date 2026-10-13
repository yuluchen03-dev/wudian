# RM-009 — Streaming semantics assessment (STREAMING-SEMANTICS-001)

**Task**: t8 · **Owner**: rag-expert · **attempt_id**: `689c72f8-d1a4-4bfb-8b02-1061eedccaff`
**Mode**: READ-ONLY assessment. **No implementation. No source file edited. No commit, no push.**
**Recommendation**: **DEFERRED_WITH_DESIGN** (§7)

---

## 0. Summary

Production `POST /api/ai/chat-sage` with `stream=true` is **not streaming**. FIX-005A (`34afd1d`,
"verify citations before streaming output") deliberately converted the transport into
**buffer → validate → chunk**: the provider stream is fully drained into memory, the citation guard
runs on the complete response, and only then is the already-final text re-emitted in 4-character
chunks over SSE.

This is **safe-first and correct for the product's core promise**, but it has three measurable costs
established below: a **~8–9 s time-to-first-content-byte**, **100 % of provider cost paid even when
the client disconnects**, and **zero cancellation leverage on upstream work**.

I recommend **DEFERRED_WITH_DESIGN**: keep option A in production, and if TTFC becomes a product
priority, adopt the option B design in §7.3 — which requires an **inline** pending marker, not merely
a trailing citation list. **Option C must be rejected** (§6): it reintroduces exactly the condition
FIX-005A exists to remove.

---

## 1. What is actually on the wire today

`backend/app/api/ai.py:92-156` — the SSE generator:

| Order | Event | Emitted when | Source line |
|---|---|---|---|
| 1 | `{"type":"chapters","chapters":[...]}` | after `rag.retrieve_for_sage_chat()` returns | `ai.py:99-120` |
| 2 | **silence** | during LLM generation **and** guard validation | — |
| 3 | `{"content":"…"}` × N, 4 chars each | after validation completes | `ai.py:128-130` |
| 4 | `{"type":"citations","citations":[...]}` | after all text chunks | `ai.py:131-134` |
| 5 | `[DONE]` | end | `ai.py:135` |

The buffering happens in `backend/app/services/ai_service.py:224-261`:

```python
224:        raw_chunks = []
225:        try:
226:            async for chunk in llm_client.stream(messages, temperature=0.8):
227:                raw_chunks.append(chunk)          # <-- provider fully drained into memory
...
234:        raw_response = "".join(raw_chunks)
...
241:        data = llm_client._parse_json(raw_response)
...
246:        citations, all_verified = self._validate_citations(raw_citations, refs)
...
253:        return ChatSageResponse(...)               # <-- only NOW does anything return
```

and `_response_text_chunks` (`ai_service.py:263-280`) re-slices the *validated* payload at
`chunk_size = 4`. So stage 3 is a **rebroadcast of an in-memory string**, not provider output.

The comment at `ai.py:127` states the intent plainly:
> *"Final response is only returned after the shared CitationGuard."*

**The provider's token stream is never forwarded. `llm_client.stream`'s per-token granularity is
consumed internally and discarded.**

---

## 2. Time-to-first-chunk (TTFC) cost of buffering

**This is the central finding: under option A, TTFC == total generation time.** Nothing textual can be
emitted before the provider finishes *and* the guard passes, because both the text chunks and their
verification derive from one completed `ChatSageResponse`.

### Real measured totals (from `docs/kb-v1/FIX-005-Q5-REAL-PROVIDER-E2E.md` §6)

| Case | total latency | citations | any_verified |
|---|---|---|---|
| Q5-RP-09 stream, valid citation scenario | **8.06 s** | 0 | false |
| Q5-RP-10 stream, induced-citation | **9.39 s** | 0 | false |

The same document records, verbatim (§6 Streaming Latency Diagnostic):
> `time_to_first_chunk`（验证后渲染分段）：**≈0.0000 s**
> 说明：因 FIX-005A 采用「完整响应 → 校验 → 分块输出」，**上游逐 token 流式语义不再保持**；
> 首包延迟由完整生成时间决定。

That `≈0.0000 s` is the *render* delay — it measures only the trivial re-slicing loop, which
**conceals** the real user-visible wait. The honest figure is the full generation time.

### My independent measurement — framing and chunk cost

Probe: `deliverables/kb-v1/dsh-rm009-measure.py` §1.

| reply size | rendered | chunks (size 4) | SSE payload | framing overhead |
|---|---|---|---|---|
| 200 chars | 242 | 61 | ≈2 249 B | **3.11×** |
| 800 chars | 842 | 211 | ≈7 799 B | 3.09× |
| 2 000 chars | 2 042 | 511 | ≈18 899 B | 3.09× |
| 8 000 chars | 8 042 | 2 011 | ≈74 399 B | 3.08× |

`chunk_size = 4` inflates the wire volume **~3×** versus the rendered text (each 4-char chunk carries
~11 bytes of JSON envelope + `data: ` + `\n\n`). At 2 000 chars this is 511 separate SSE frames.
This is a **secondary** inefficiency, not the main cost.

### TTFC comparison (model)

| | option A (current) | option B / C |
|---|---|---|
| TTFC | **8.06 s / 9.39 s** (= full generation) | first provider token |
| TTFC penalty of buffering | **≈8.0–9.3 s, i.e. 161×–187× slower to first byte** | — |
| Total latency | 8.06 / 9.39 s | essentially identical (+~20 ms framing) |

**Honest scope note:** the 8.06 s / 9.39 s totals are **real measured** values. The per-token cadence
(≈50 ms) is a **model**, because Q5 (real credentials) is only partially exercised and provider
cadence was not recorded token-by-token. **The TTFC conclusion does not depend on that model** —
option A *cannot* emit before completion for any cadence, so TTFC == total generation by
construction.

**Verdict:** buffering costs essentially **all** of the perceived latency. Total latency is
unchanged; the user simply receives the entire answer at the end instead of watching it form.

---

## 3. Cancellation behaviour (client disconnects mid-generation)

Probe: `deliverables/kb-v1/dsh-rm009-cancel.py` — models a real disconnect via task cancellation
(Starlette/uvicorn behaviour), synthetic 100-token generation.

| | option A (current) | option B (true stream) |
|---|---|---|
| events emitted before disconnect | 3 | 3 |
| **provider tokens produced** | **100 / 100 (100 %)** | **3 / 100 (3 %)** |
| upstream work saved by cancelling | none | ~97 % |

**Under option A the entire provider generation is already paid for before the first content chunk
reaches the client.** A disconnect during the silent window cannot save a single token: the work is
already in `raw_chunks` (`ai_service.py:224-227`). Cancelling forfeits only the cheap 4-char render
loop.

**Consequences not previously quantified:**
- **Cost amplification / abuse surface.** Any client that abandons a request after ~1 s still causes
  the full generation to be billed. There is no server-side early-exit.
- **Token quota is debited regardless.** `llm_client._record_tokens` runs in the `finally` of
  `stream()` (`llm_client.py:250-254`), so `today_tokens` advances even for abandoned requests.
- **Cross-request amplification.** Because `_check_quota` reads a process-global daily counter
  (`llm_client.py:132-141`), abandoned requests can exhaust the daily budget
  (`DAILY_TOKEN_LIMIT`) for all users.

An earlier probe in this task used `async for … : await gen.aclose()`, which does **not** model a
disconnect and under-reported the effect; that measurement is superseded by the task-cancellation
probe above.

---

## 4. Memory behaviour for long responses

Probe: `deliverables/kb-v1/dsh-rm009-measure.py` §3, via `tracemalloc`.

| output size | peak traced memory | bytes held per output char |
|---|---|---|
| 2 000 chars | ≈33.1 KiB | ≈17.0 |
| 20 000 chars | ≈320.4 KiB | ≈16.4 |
| 100 000 chars | ≈1 606.7 KiB | ≈16.5 |

**Option A holds, simultaneously, for the whole response:** the `raw_chunks` list, the joined
`raw_response` string, the parsed `data` dict, the rendered string, and the full chunk list
(`ai_service.py:224-280`). Usage is **linear and bounded by `LLM_MAX_TOKENS`**, at a stable ~16.5 B
per output character.

**Assessment: this is NOT a practical risk.** At a generous 100 000-char response the peak is ~1.6 MiB
per in-flight request. Typical sage answers are a few hundred characters
(scenario §2: 8.06 s ≈ 150–200 tokens). The buffer strategy is therefore **memory-acceptable**; the
problem is latency and cancellation, not footprint. Option B would reduce peak (no full-response
retention), but that is not a reason to change on its own.

---

## 5. Provider failure handling

`ai_service.py:224-238` and `ai.py:136-146`:

| Failure | Where | Behaviour | Assessment |
|---|---|---|---|
| Provider raises mid-stream | `ai_service.py:228-232` | catches, logs **without payload**, returns `build_stream_fallback_response` (validated cache answer) | Good — no credential leak, still guarded |
| Provider returns "unavailable" text | `ai_service.py:235-238` | detected, swapped for cached structured payload | Good |
| Provider unavailable from the start | `ai_service.py:203-206` | `llm_client.is_available` false → cache fallback | Good |
| Failure before validation completes | `ai.py:136-146` | emits `{"type":"error","code":"stream_incomplete"}` **and no citations event** | Good — fails closed |
| Partial JSON from a truncated stream | `ai_service.py:241-243` | `_parse_json` fails → `data = {}` → no citations → `all_verified=False` | Good |

**Key property: option A fails closed.** Because nothing is emitted before validation, a mid-stream
provider failure produces *no text and no citations* — never a half-verified quote. This is asserted
by `test_api_sse_provider_error_returns_generic_error_without_citation_event`
(`backend/tests/test_fix005a_streaming.py:200-226`), which also verifies the error **sentinel string
is absent from the response body and logs**.

Error redaction is a documented, separately-audited property (`FIX-005-Q5-REAL-PROVIDER-E2E.md` §7,
`REAL_PROVIDER_ERROR_REDACTION = PARTIAL` — covers deterministic `model_not_found`, not all 401/403
paths).

**Under option B this property degrades:** text already sent cannot be un-sent. A mid-stream failure
would leave a **truncated, unverified** answer on screen. Option B therefore requires an explicit
client-side "abandoned / unverified" terminal state that does not exist today.

---

## 6. Pending-citation UX — what the user sees while nothing is emitted

**Server side:** there is **no keepalive, heartbeat, or progress event** in `event_stream()`. The only
pre-generation byte is the `chapters` event, itself gated on retrieval (`ai.py:99-120`). The
subsequent silence is **not bounded by any server-side timeout in the route** — only by
`LLM_TIMEOUT` on the provider call (`llm_client.py:95`).

**Client side** (`frontend/components/sage/SageChat.tsx:87-187`):
- `setIsSearching(true)` on submit (`:105`), cleared **only when the first text chunk arrives**
  (`:139-142`).
- `firstChunkReceived` gates that transition, so the retrieval spinner **stays up for the entire
  generation** (~8–9 s).
- `isStreaming` stays true until the promise resolves in `finally` (`:183-186`).
- The client parser (`frontend/lib/api.ts:1077-1120`) recognizes `chapters`, `citations`, and
  `content`; an unknown `type` is **silently ignored** (`:1102-1113`).

**Today's UX, precisely:** the user sees an indeterminate "searching chapters" state for ~8–9 s, then
the complete answer appears almost instantly (511 frames × ~0.04 ms). The interface **claims to be
streaming** (`chatWithSageStream` takes an `onChunk` callback and accumulates text) while delivering
a single burst. The "streaming" affordance is presentational only — a genuine but *unreported* UX
inconsistency, and the honest subject of STREAMING-SEMANTICS-001.

Note the delay is dominated by the **LLM generation**, not by the citation guard: `guard_citations`
is a pure in-memory substring/whitelist check over ≤5 refs and is negligible next to multi-second
generation. **Moving validation does not buy back the latency.** This matters for §7: option B's
speedup comes from *not buffering*, not from *not verifying*.

---

## 7. The three options compared

### 7.1 Option A — buffer → verify → chunk (**current**)

| Dimension | Result |
|---|---|
| TTFC | ≈ full generation (8–9 s measured) |
| Total latency | 8.06 / 9.39 s |
| Cancellation | **no upstream saving; 100 % cost paid** |
| Memory | ~16.5 B/char, linear, ≤~1.6 MiB @100k chars — acceptable |
| Provider failure | **fails closed** — no partial text, no citations |
| Pending UX | indeterminate spinner ≈ full generation, no heartbeat |
| **Safety** | **SAFE — zero exposure window** |

### 7.2 Option B — true streaming with citation pending state

Forward provider tokens immediately; emit citations as `verification_status="pending"` and reconcile
with a later event.

Notably **the schema already supports this**: `Citation.verification_status` includes a `"pending"`
literal (`backend/app/schemas/ai.py:118-125`). The hook exists; nothing populates it today.

| Dimension | Result |
|---|---|
| TTFC | first token (~50 ms modelled) — **≈160–190× improvement** |
| Total latency | unchanged |
| Cancellation | **stops near disconnect point** (3 % vs 100 % work) |
| Memory | lower peak (no full-response retention) |
| Provider failure | **fails OPEN-ish** — truncated text already on screen; needs a new terminal state |
| Pending UX | honest *if* an inline pending signal is shown |
| **Safety** | **CONDITIONALLY SAFE — bounded exposure window, not zero** |

### 7.3 Option C — text streaming, citation delayed

Stream text; withhold all citations until the end. **No pending state is ever shown.**

| Dimension | Result |
|---|---|
| TTFC | first token |
| Cancellation | stops near disconnect |
| Pending UX | **dishonest** — unmarked text, then a citation list appears (or never) |
| **Safety** | **UNSAFE — reintroduces the FIX-005A defect** |

Option C is **strictly dominated by Option B**: identical exposure window, strictly less honesty.

---

## 8. Safety implication of each option (the decisive criterion)

Probe: `deliverables/kb-v1/dsh-rm009-safety.py`, using the **real** `citation_guard`. The synthetic
reply embeds a fabricated classical line:

> `子曰：宽恕之道，可平天下万民之怨。` (fabricated)

Ground truth from `guard_citations`:

| citation | verifiable | trust_state |
|---|---|---|
| 引1 — fabricated line | **False** | `insufficient_evidence` |
| 引2 — real 《论语·卫灵公》 line | True | `verified` |

**Does an unverified/fabricated quote reach the user before verification?**

| Option | Fabricated text reaches the client pre-verification? | Exposure window | Verdict |
|---|---|---|---|
| **A** | **No** (text is derived from the validated payload) | **0** | **SAFE** |
| **B** | **Yes** — as narrative text, before any trust marking | `[first token … citations event]` | **CONDITIONALLY SAFE** — only with an inline pending marker |
| **C** | **Yes** — unmarked, with no pending signal at all | `[first token … end]` | **UNSAFE — reintroduces the FIX-005A defect** |

**This is the crux for option B.** Forwarding raw tokens means the fabricated line `子曰：宽恕之道…`
appears in the user's view while it still *looks like* an authoritative classical quotation.
A trailing `pending` marker on a separate citation list is **insufficient**, because:

1. The text arrives **before** the citations event (`ai.py:128-134` emits text first).
2. `SageChat.tsx` renders content immediately (`:143-147`) and only attaches citations later (`:160-164`).
3. The client parser silently ignores unknown event types (`api.ts:1102-1113`), so an unrecognized
   pending signal would vanish without error.
4. A user reading classic-looking text does not cross-reference a citation list appended seconds later.

Therefore option B is only acceptable if the pending/uncertain state is attached **to the text
itself** (an inline placeholder or explicit "待核验" marker rendered in the sentence), so that the
guard's verdict gates the *appearance of authority*, not merely the presence of a metadata field.

**FIX-005A is not broken by this assessment — I recommend keeping it.** Option C is the option that
would break it, and it is rejected outright.

---

## 9. Recommendation: **DEFERRED_WITH_DESIGN**

**Keep option A as production behaviour. Do not implement a change in RM-009.**

Rationale — a real change is large, and the safety invariant currently in force is load-bearing:

1. **Safety is the product's core promise.** *每个观点，都能追到原典；找不到，就不硬编.* Option A is the
   only one of the three with a **zero** pre-verification exposure window. Trading it for latency is a
   product decision the team has not been asked to make, and FIX-005A is a TERMINAL PASS.
2. **The change is not local.** Option B touches: the SSE event contract (`api/ai.py`), the citation
   lifecycle (`schemas/ai.py:118-125` `pending`), the client parser (`frontend/lib/api.ts:1077-1120`),
   the chat component's streaming/pending rendering (`SageChat.tsx:87-187`), and the failure terminal
   state. It also needs new tests for the *new* exposure window, plus re-validation of the existing
   15 FIX-005A assertions (baseline verified green: **15 passed**).
3. **Total latency is unchanged.** Option B improves *perceived* responsiveness only. The 8–9 s
   generation cost is not addressed by any of the three options.
4. **Q5 is only partially unblocked.** Provider cadence was never measured token-by-token, so the
   real TTFC gain is **modelled, not measured**. Committing to a redesign on a modelled benefit
   would violate the project's own evidence discipline.
5. **The dominant cost is provider latency, not the guard.** Saving the render loop gains ~0 ms;
   only removing the buffer helps — which is precisely the part that is unsafe by default.

### 9.1 Concrete design if the team later chooses to proceed (option B, gated)

Preconditions — **all** must hold before implementation starts:

- **P1 (blocking, product).** Explicit written acceptance that the pre-verification exposure window
  becomes non-zero, replacing the current zero-window guarantee.
- **P2 (blocking, design).** An **inline** pending contract: any classical-looking quotation in
  streamed text renders inside an explicit 待核验 / 未验证 affordance from its first character, and is
  resolved in place by the citations event. A trailing list alone is **not** acceptable (§8).
- **P3 (blocking, UX).** A defined terminal state for mid-stream provider failure that marks the
  already-displayed text as incomplete and unverified.
- **P4.** Re-measure TTFC with real credentials token-by-token to replace the model in §2.

Required work items (estimate: **large**, multi-file, needs its own gate):

| # | Item | File(s) |
|---|---|---|
| B1 | Emit `{"type":"text","content":…}` per provider token, replacing post-hoc re-chunking | `services/ai_service.py:224-280`, `api/ai.py:122-130` |
| B2 | Buffer **only** the citation-bearing JSON region (or parse incrementally) to run the guard as soon as citations are complete | `services/ai_service.py:241-246` |
| B3 | Populate `verification_status="pending"`, then reconcile via a `citations_resolved` event | `schemas/ai.py:118-125`, `api/ai.py:131-134` |
| B4 | Inline pending rendering + in-place reconciliation | `frontend/lib/api.ts:1077-1120`, `SageChat.tsx:136-165` |
| B5 | Terminal "incomplete/unverified" state on disconnect or provider error | `api/ai.py:136-146`, `SageChat.tsx:167-186` |
| B6 | SSE heartbeat/keepalive during any residual silent window | `api/ai.py` |
| B7 | New tests: inline-pending invariant, mid-stream failure, non-parity with A's zero window | `backend/tests/test_fix005a_streaming.py` (extend), new file |
| B8 | Re-run the RM-005/FIX-005A safety suite; prove no fabricated quote is presented as authoritative | existing suites |

**Do not start B1–B8 without P1–P3.** Absent them, implementing option B would knowingly regress a
frozen safety property.

### 9.2 Cheaper, safety-neutral follow-ups (allowlist)

These may be scheduled independently without touching the FIX-005A guarantee:

- **Reduce `chunk_size` overhead** (`ai_service.py:279`): 4 chars → 24–48 chars cuts wire volume ~3×
  → ~1.1× and SSE frames 511 → ~45. Purely presentational; **no change to what or when anything is
  verified.**
- **Add an SSE heartbeat** during the buffering window so proxies do not idle-timeout and the client
  can display honest progress. Emits no content.
- **Correct the latency diagnostic** in `FIX-005-Q5-REAL-PROVIDER-E2E.md` §6: the `≈0.0000 s`
  `time_to_first_chunk` measures only the render loop and should be paired with the full-generation
  figure (8.06 / 9.39 s) to avoid a misleading record. *(Documentation change — **not** performed in
  this read-only task; flagged for the owner.)*
- **Stop labelling the transport "streaming" in UI copy** until it genuinely streams.

---

## 10. Evidence, reproduction, and limitations

### Reproduction

```powershell
backend/.venv/Scripts/python.exe deliverables/kb-v1/dsh-rm009-measure.py   # TTFC model, chunking, memory
backend/.venv/Scripts/python.exe deliverables/kb-v1/dsh-rm009-cancel.py    # cancellation semantics
backend/.venv/Scripts/python.exe deliverables/kb-v1/dsh-rm009-safety.py    # safety invariant
# FIX-005A baseline (must stay green and unmodified)
cd backend; $env:JWT_SECRET_KEY='conftest-test-only-secret'
./.venv/Scripts/python.exe -m pytest tests/test_fix005a_streaming.py tests/test_fix005_q5_mock_e2e.py -q
```

| Artifact | Content |
|---|---|
| `deliverables/kb-v1/dsh-rm009-measure.py` / `-out.txt` | Chunking math, TTFC model, memory, wire timeline |
| `deliverables/kb-v1/dsh-rm009-cancel.py` / `-out.txt` | Task-cancellation comparison A vs B |
| `deliverables/kb-v1/dsh-rm009-safety.py` / `-out.txt` | Exposure-window analysis with the real citation guard |

### Verification performed

- FIX-005A + FIX-005 Q5 suites: **15 passed** (`backend/.venv/Scripts/python.exe -m pytest … -q`).
- Source inspected: `api/ai.py`, `services/ai_service.py`, `services/llm_client.py`,
  `schemas/ai.py`, `services/citation_guard.py`, `frontend/lib/api.ts`, `components/sage/SageChat.tsx`.
- No source file, test, Gold, `TARGETS`, or frozen metric was modified. Chroma was never opened
  (probes point `CHROMA_PERSIST_DIR` at a temp copy; the streaming path does not touch Chroma anyway).

### Limitations (honest)

- **Q5 is only partially unblocked.** The 8.06 s / 9.39 s totals are real measured values from
  `FIX-005-Q5-REAL-PROVIDER-E2E.md`, but **provider token cadence was never measured**. The
  per-token figures in §2 are a **model**. The TTFC conclusion (A cannot emit before completion)
  is structural and independent of that model; the *magnitude* of the B-side gain is not measured.
- Cancellation and memory results come from faithful **simulations** of the generator/transport
  contract, not from a live client disconnect against a real provider. They establish the
  control-flow property (A pays full cost; B stops early), not production timing.
- No end-to-end browser test was performed; the pending-UX analysis (§6) is derived from the client
  source, not from observing a live session.
- Error-redaction coverage remains **PARTIAL** per the upstream doc (§7 there); not re-audited here.
- A prior cancellation probe in this task (`dsh-rm009-measure.py` §4) used `aclose()`, which does not
  model a disconnect; its null result is superseded by `dsh-rm009-cancel.py` and is retained in the
  raw output for transparency.
- **This is an assessment only. No implementation was performed, and none is proposed for approval
  without P1–P3.**
