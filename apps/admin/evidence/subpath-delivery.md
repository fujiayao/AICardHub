# Admin existing-site subpath delivery

- Base: `fa89ef3efef230b18b1e2850f2283a82d9c0f39f`.
- Branch: `fix/admin-aicardhub-subpath`.
- Build: `VITE_BASE=/aicardhub/admin/ pnpm build`.
- API requests, including multipart imports, resolve to `/aicardhub/api/...`.
- JSON response media fields use `/aicardhub/files/...`; JSON request bodies restore these fields to `/files/...`. The schema allowlist is `logo_url`, `image_url`, `photo_url`, `photo_bg_url`, `wechat_qr_url`, `qr_url`, `poster_url`.
- Titles, knowledge content, ordinary URL fields, absolute external URLs, router logic paths and multipart contents are not rewritten. NoteEditor is unchanged. Generated API files, dependencies, H5 and backend are unchanged.
- Checks: 27 Node tests passed; `pnpm typecheck` passed; `pnpm lint` passed; production subpath build passed. Vite reports the existing large markdown/Element Plus chunks as warnings.
- Build index references `/aicardhub/admin/favicon.svg` and `/aicardhub/admin/assets/...`.
- Contract SHA256 (unchanged): `3ebe39cd03645b7c69558307f9e60097c4c2f9ccc98a327105cb630cdc64d4e2`.
- No database migration or API contract changes. No visual changes or screenshots. Browser production-dist verification is owned by mainline; no live deployment or SSH operation was performed.

## Native template review at delivery

During review the independently owned native template was replaced by `aicardhub.locations.conf.in`, a server-context include scoped to `/aicardhub/`, with no new production listener/certificate/server block; optional staging is separate. The new include still needs two concrete corrections: `disable_symlinks on` on admin/H5 assets rejects the deliberate `current` release symlink; use an appropriate trusted-release path or narrow `from=` policy. SPA `error_page 404 /.../index.html` retains HTTP 404 on deep links; use a successful internal fallback while retaining hard 404 for missing assets. Its media regex also still excludes hyphens/underscores in card codes. Existing unrelated site paths must remain served by the original configuration. No nginx runtime validation was performed.
