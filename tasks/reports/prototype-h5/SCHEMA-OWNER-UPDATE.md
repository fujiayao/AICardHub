# LIVE schema owner update — read before B2/B3 implementation

Main has implemented, export pending:
- CardData company_id/company_name/company_short_name.
- StatsData today/yesterday each {visits,visitors,chats,leads}; Asia/Shanghai calendar boundaries; daily date labels same timezone.
- VisitorData source and intent_level optional, from latest record accessible to current employee only.

B2 today's labels MUST use stats.today, previous-day delta = today metric minus yesterday metric. Recent visitors show real source and optional intent level. B3 company locked row uses generated company fields. Preserve every prototype section. Main tests server. No server edits, no hand generated API edits. Keep A1 candidate priority; integrate after exported contract available.

Additional main update:
- B5 retain original AI-status three metrics. GET /me/assistant/metrics operation me_assistant_metrics -> {answers,unanswered,disliked,notes,corrections,period_days:7}, authorized own card, non-test assistant messages last7d. Generated endpoint helper assistantMetrics forthcoming.
- Personal knowledge intro no dedicated NoteInput field. Preserve edit-intro through existing real note body with clear matching user label and safe semantics, or request minimum metadata if impossible. No fake metric or section deletion.

23:51 schema export READY NOW:
Coordinator ran existing node scripts/generate-api.mjs D:/AIWork/智能名片/AICardHub/contracts/openapi.json. Generated44 existing H5 operations plus complete schemas; SHA f901114020e4a755dfd84f8661e45fb941a8dce1847e52095855c2da852fe801. New CardData/StatsData/VisitorData/AssistantMetricsData types available. YOU need add assistantMetrics:['get','/api/v1/me/assistant/metrics','staff'] alias to apps/h5/scripts/endpoints.mjs (source allowed) then parent reruns generator. Do not hand-edit generated. Main latest says menu/login fixes owned by another worker, DO NOT touch menu/login/firstpassword flows. Tell staff agent this now; focus B2-B13 content, keep existing shell navigation.

23:53 USER update B6: NoteInput.description max80 optional; NoteData.description/updated/tokens real frontmatter and version preservation. Omitted description keeps previous. Use independent intro0/80 field, list summary + update time + word/token display with correct meaning. NO embedding description in body workaround. Main handles server tests/export. B5metrics done. Other missing fields concise list only.
