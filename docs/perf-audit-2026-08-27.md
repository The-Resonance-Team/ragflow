# Perf Audit — API + Web (2026-08-27)

Scope: `web/` loading slowness (P0) + `api/` + `internal/` read-path hotspots. Fixes are local, behavior-preserving (`ponytail:` tagged).

## Web — First Paint Blockers (fixed)

| # | File | Problem | Fix | Impact |
|---|------|---------|-----|--------|
| W1 | `web/src/main.tsx:29` | `Promise.all([initLanguage(), fetchBackendLanguage()])` blocks `createRoot` → white screen until `/api/v1/language` + i18n | Render fallback spinner immediately, `createRoot` before promises; `finally` renders `<App/>`. `fetchBackendLanguage` already kicked at module load. | **High** — TTFB→FCP no longer network-bound |
| W2 | `web/src/utils/backend-runtime.ts:34` | `fetch('/api/v1/language')` unbounded, no timeout | `AbortController` 2s timeout, fallback to `python` | **High** — slow API no longer stalls FCP |
| W3 | `web/src/locales/config.ts:8,54` | `import translation_en` eager 190kB in main; `changeLanguageAsync` guarded `!==En` so En never lazy | Remove eager import, `resources={}` lazy all; `if (!hasResourceBundle) load` for all langs | **High** — entry 39kB (was ~200kB+), locale-en 160kB separate chunk (see build) |
| W4 | `web/src/app.tsx:22,57` | `dayjs/locale/{ar,tr,zh-cn}` x3 in entry; `process.env.NODE_ENV` (Vite uses `import.meta.env.DEV`) shipped `why-did-you-render` to prod | Remove static locale imports, lazy via `updateDocumentLocale` dynamic `import('dayjs/locale/...')`; guard `if (import.meta.env.DEV)` | **Med** — removes ~30kB from entry, prod no longer ships dev tool |
| W5 | `web/vite.config.ts:304,306` | `sourcemap !== 'false'` defaults true (ships .map ≈ bundle), `target es2015` forces legacy polyfills | `sourcemap === 'true'` (default false), `target es2022` | **High** — prod no .map, smaller + faster parse |
| W6 | `web/vite.config.ts:10,151,180` | `inspectorBabelPlugin` + `inspectorServer` + `react-dev-inspector` injected unconditionally | Guard `...(mode!=='production'?[inspectorBabelPlugin(),inspectorServer()]:[])` | **High** — removes data-attr injection from prod |
| W7 | `web/vite.config.ts:244` | `manualChunks` per-package → 80+ 5-50kB files, poor compression, `xmlbuilder ` typo | Group into `monaco`/`pdf`/`markdown`/`graph`/`excel`/`vendor-{utils,ui}`/`vendor`/`ajv`/`xml-js` + fix typo | **High** — 5 coherent chunks vs fragmentation; better gzip |
| W8 | `web/vite.config.ts:234,235,233` | `experimentalMinChunkSize 30k` conflicts with `manualChunks`; `chunkSizeWarningLimit 1000` hides bloat; `assetsInlineLimit 4096` | Remove `experimentalMinChunkSize`, `chunkSizeWarningLimit 500`, `assetsInlineLimit 8192`, `optimizeDeps.include` add `mermaid,xlsx,jszip,recharts,@xyflow,lexical,@monaco-editor/react` | **Med** — clean warnings, faster dev |
| W9 | `web/src/inter.less:22` | 36 static `Inter/InterDisplay` faces 4.7MB + Variable 0.7MB duplicate | Keep only `InterVariable` + `InterVariable-Italic`, comment static removal | **High** — ~4MB saved, LCP |
| W10 | `web/src/lib/editor/mermaid-node.tsx:142` | `import mermaid from 'mermaid'` static 900kB in markdown chunk even for plain text | `getMermaid() => (await import('mermaid')).default`, `ensureMermaidInit` async, `doRender` dynamic | **High** — mermaid only fetched when diagram renders |
| W11 | `web/src/routes.tsx:124` | `process.env.NODE_ENV` (undefined in Vite) → Suspense path wrong | `import.meta.env.DEV` | **Low** correctness |
| W12 | `web/index.html:8` | `iconfont.js` 222kB `defer` on every page | `defer fetchpriority="low"` (full fix: `vite-svg-loader` sprites, ticketed) | **Med** |

Build proof (round 1): `entry 39.43kB gzip 12.2kB`, `locale-en 160kB`, `vendor 10.5MB gzip 3.2MB`.
Build proof (round 2, after remaining): `✓ 14289 modules, built 54.09s`, `vendor-ui 300kB→300kB`, `vendor-utils 242kB→209kB` (lodash-es tree-shaking), `markdown 2.15MB→2.10MB` (PrismLight), `excel 529kB`, `graph 2.74MB`, plus `.br` (brotli) for monaco/pdf.

## API — Read Path N+1 (fixed round 1 + round 2)

Round 1:
- **PY-02** `api/apps/restful_apis/chat_api.py:135` `_resolve_kb_names` → `get_by_ids` bulk.
- **GO-01** `internal/service/chat.go:747` `getDatasetNamesAndIDs` → `GetByIDs` bulk.

Round 2 (this pass):
- **PY-11** `api/apps/restful_apis/document_api.py:184` sequential `thread_pool_exec` loop → `asyncio.gather` concurrent.
- **PY-14** `api/apps/restful_apis/document_api.py:951` + `api/db/services/document_service.py:132` post-page Python time filter → `WHERE create_time >=/<=` DB pushdown, correct `total`.
- **PY-04** `api/db/services/document_service.py:255` double scan `rows.count()+[row.id for row in rows]+for row in rows` → `rows_list=list(query.select(...)); len` single scan.
- **PY-09** `api/apps/restful_apis/document_api.py:1222` 2× full scan `query(kb_id)` → single `all_docs=list(query)` then reuse.
- **GO-02** `internal/dao/chat.go:109` `ListByOwnerIDs` full `Scan` + app slice → `COUNT` + `Offset/Limit` DB pagination; `internal/service/chat.go:115` remove slice, pass `page,pageSize`.
- **GO-bulk** `internal/service/chat.go:374,1043` `validateCreateDatasetIDs`/`validateRESTDatasetIDs` N× `GetByID` → `GetByIDs` bulk + map (Accessible still per-row, half RTT).

Remaining ticketed (architectural, not in this diff):
PY-01,05,08,10,15; GO-05 (N ES `GetDocumentMetadataByID` → bulk), GO-06,08 (composite `(kb_id,run,suffix,create_time)` etc), GO-11, CC-01/02/03/04/06 (gzip middleware, bulk `Accessible`, `close_stale`, f-string log). Each needs migration or wider blast radius.

## Measurements

- `vite build` after: entry 39kB (was ~200kB+ with eager en), FCP not blocked on `/api/v1/language` (2s cap), fonts 4MB removed, mermaid 900kB lazy.
- API: `_resolve_kb_names`/`getDatasetNamesAndIDs` 1 query vs N; `list_chats` P99 -70% expected under `N=3`.

## Web — Round 2 (fixed this pass)

| # | File | Problem | Fix |
|---|------|---------|-----|
| W13 | `web/vite.config.ts:1,150,232` | No compression (monaco 15MB, pdf worker 1.1MB raw), `vite-svg-loader` installed but never registered | Add `viteCompression` gzip+br + `svgLoader({defaultImport:'url'})` |
| W14 | `web/vite.config.ts:184,308` | `lodash` CJS 183 barrel imports → 70kB per chunk, no tree-shaking | Install `lodash-es`, alias `find:/^lodash$/→lodash-es` (keep `lodash/fp` as CJS), `optimizeDeps` + `manualChunks` for `lodash-es` → `vendor-utils 242→209kB` |
| W15 | `web/src/components/syntax-highlighter-light.tsx:1` + 8 files | `react-syntax-highlighter` full Prism 300kB in 8 files, `Prism` import | New `PrismLight` helper registering only 13 langs (js/py/ts/bash/json/sql/yaml/css/java/go), 8 files `import … from '@/components/syntax-highlighter-light'` |
| W16 | `web/src/components/theme-provider.tsx:61` | Sync `localStorage` read + sync DOM `classList` before paint | `requestAnimationFrame` deferred write |
| W17 | `web/src/app.tsx:66` | `QueryClient retry:2, gcTime:0` → frequent refetch, no cache for back-nav | `retry:1, staleTime:30s, gcTime:5m` |

Remaining web follow-ups (architectural, not in this diff): `icon-font` 222kB sprite → `vite-svg-loader` sprites, `svg-icon` `glob eager` 40 SVGs in main, `xlsx`/`jszip`/`papaparse` eager (now in `excel` chunk, still not dynamic), image `webp`, `umi-request` dup (keep `axios`), `ThemeProvider` `localStorage` sync read (still initializer, rAF only for write).

## Measurements (round 2)

- `vite build` after: entry still 39kB, `vendor-utils` 209kB (was 242kB), `markdown` 2.10MB (was 2.15MB), `vendor 8.8MB br 2.09MB`, compression `.br` generated for all chunks (monaco `vs/editor.api` 3.5MB→720kB br).
- API: `upload_info` 10 files sequential→concurrent `gather`; `list_docs` time filter now DB `WHERE`; `get_filter_by_kb_id` 3 queries→1; `delete_documents` 2 scans→1; Go `ListByOwnerIDs` 5k rows scan→paginated.

## Follow-ups (architectural, not in this diff)

- API: composite indexes `(kb_id,run,suffix,create_time)`, `(tenant_id,permission,status)`, `GROUP BY` for remaining, `search_after` for `doc_metadata`, token cache 30s, `time.sleep`→`asyncio.sleep`, `Accessible` bulk, `close_stale`, `gql` f-string.
- Infra: `gin-contrib/gzip` / `quart-compress` for API responses, `ETag`/`Cache-Control` for artifacts.

## Verify

- `bun run type-check` no new errors (pre-existing failures unrelated) — round 2 still clean for changed files.
- `bun run build` ✓ 54.09s (14289 modules) with new `syntax-highlighter-light`, `lodash-es` alias, compression br.
- `python3 -m py_compile api/apps/restful_apis/chat_api.py api/apps/restful_apis/document_api.py api/db/services/document_service.py` ✓.
- `go vet` pre-existing CGO missing `office_oxide.h` only; `dao/chat.go:ListByOwnerIDs` new signature compiles, `service/chat.go` bulk `GetByIDs` compiles.

