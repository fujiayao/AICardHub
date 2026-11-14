# LIANGWEI A2 small repair — ready for parent validation

Edits use native Edit only. No shell, check.sh or screenshots have been run (未执行).

## Changes
1. `apps/h5/src/pages/chat/[code].vue`
   - Imports: moved `AnonymousPortrait` above `ChatComposer`, so the `@/components/common/*` group is alphabetical (perfectionist/import sort).
   - `.welcome-avatar` now has `position:relative; display:block; width/height:76px; border-radius:var(--r-pill); overflow:hidden; background:linear-gradient(165deg,var(--c-hero-top),var(--c-ink)); box-shadow:var(--sh-welcome)`, plus `.welcome-avatar img{width:100%;height:100%;object-fit:cover;object-position:center top}`.
   - Root cause: the old rule set only size and shadow. The `.avatar-ai::after` online dot (`position:absolute; width/height:28%`) had no positioned ancestor at the avatar level, so it resolved against an outer box and showed up as a large cyan pill. Now it is a 28% dot in the bottom-right of the 76px circle.
2. `apps/h5/src/components/visitor/CardAiEntry.vue`: when there is no opening line, the fallback uses `card.name` (`您好，我是{name}的 AI 分身，有什么可以帮您？`). If the name is empty, it uses the neutral `您好，有什么可以帮您？`. The broken text `我是我的 AI 分身` is gone.
3. `apps/h5/src/components/common/AnonymousPortrait.vue`: aria-label changed to `匿名人物插画占位，非真实照片`. The SVG shapes are unchanged.

## Parent validation commands (未执行)
```bash
cd apps/h5 && pnpm lint && pnpm typecheck
node tasks/reports/prototype-h5/capture-candidate.cjs   # compare A2 against reference/A2.png
```

## Risk
- Not compared visually yet. The 76px size and `--sh-welcome` ring are kept, and the gradient matches the `.chat-head .avatar` / CardAiEntry `.avatar` gradient.
