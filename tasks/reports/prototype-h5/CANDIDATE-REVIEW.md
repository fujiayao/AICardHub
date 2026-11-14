# Candidate4740503 review — next round required fixes

Actual browser screenshot candidate-A1.png was inspected by coordinator, not accepted as pixel fidelity:
1. A1 bottom CTA disappeared from first viewport: .vc-bar is in normal flow; prototype has sticky/flex fixed viewport footer. Fix actual viewport/page scroll containment or fixed dock scoped to max480px. Preserve no-phone/no-WeChat data rules.
2. Gray ai-q rows have native button beveled gray borders; prototype has border:none. .glass also has native button border. Explicit scoped button resets required, do not remove focus-visible outline. Quick buttons same native reset issue.
3. Color literals remain in CardHero rgba, CardAiEntry rgba, A1 rgba, AnonymousPortrait SVG attrs. Move exact original colors to tokens.css variables; exact SVG geometry unchanged.
4. CardHero onShare currently inherited hardcoded ?s=link loses campaign e; requirement preserve source s/e. Pass actual scene query/prop or use safe route scene helpers. Report claim 'all source preserved' premature.
5. Long source company/title naturally wrap; no data fabrication. Real5dbb1d43 has no phone/WeChat; lack of those buttons intentional.
6. CardDetails still previous layout, needs original exact contact rows/company/product card236px/104px image/no fabricated images and sections. Not done in first candidate.

A1 screenshot measures hero440, no surname tile, no overflow/page errors. Typecheck/lint passed after A1 template complete. First candidate4740503 committed by coordinator; frontend source authored entirely Opus. Do not restage stale snapshot or undo commit.

Read SCHEMA-OWNER-UPDATE.md before staff. Main fields ready soon. Need native staff agent now, exact same model onceai, disjoint components/staff +pages/staff only; main owns common/styles. Agent must Read B PNG screenshots and actual render functions before port. B1 outside staff pages login? coordinate mapping; avoid overlapping A files.

Screenshot follow-up at23:53: candidate-A2.png now visibly broken: welcome avatar is square and its .avatar-ai::after renders giant teal pill at lower right because .welcome-avatar lacks position:relative, border-radius, overflow:hidden and shared avatar sizing/background rules. It must be circular original portrait. Read candidate-A2.png for actual regression. Header avatar okay. Fix welcome avatar scoped positioning BEFORE claiming A2 complete. A1 fixed dock now present, next capture verify.

URGENT USER fresh schema: SCHEMA-OWNER-UPDATE.md appended23:53 and generated types ready. Must tell native staff: StatsData.today/yesterday already generated; do not still show unavailable yesterday. Notes description80/updated/tokens now approved (main exporting). Add assistantMetrics alias source now and coordinator gen. Login/menu owned other worker, do not touch these. Avoid stale helper lack as reason for persistent dashes when source alias trivial authorized.

23:54 validation: vue-tsc passed. Lint1 error chat/[code].vue line13 import AnonymousPortrait must precede ResourceState per import sort. Parent does not fix source, Opus fix native Edit.
