# Mermaid diagram types

Canonical source: https://mermaid.js.org and the
[mermaid syntax docs](https://github.com/mermaid-js/mermaid/tree/develop/packages/mermaid/src/docs/syntax).
Mermaid adds new diagram types over time — if a needed relationship isn't
covered below, check that source before assuming it's unsupported.

| Need to show | Diagram type | Start keyword |
|---|---|---|
| Process / decision flow | Flowchart | `flowchart` (or legacy `graph`) |
| Time-ordered messages between actors | Sequence | `sequenceDiagram` |
| OOP structure, inheritance | Class | `classDiagram` |
| State machine, transitions | State | `stateDiagram-v2` |
| Database schema, table relationships | Entity Relationship | `erDiagram` |
| Project schedule / timeline with bars | Gantt | `gantt` |
| Proportional breakdown | Pie | `pie` |
| Radial brainstorm / outline | Mindmap | `mindmap` |
| UX journey with satisfaction scores | User Journey | `journey` |
| Chronological events (no durations) | Timeline | `timeline` |
| Branches, merges, tags | Git Graph | `gitGraph` |
| Software architecture context/containers | C4 | `C4Context`, `C4Container`, `C4Component`, `C4Dynamic`, `C4Deployment` |
| Requirements traceability | Requirement | `requirementDiagram` |
| Agile task board | Kanban | `kanban` |
| Prioritization matrix | Quadrant | `quadrantChart` |
| Multi-dimensional comparison | Radar | `radar` |
| Resource/energy flow volumes | Sankey | `sankey-beta` |
| Nested hierarchical proportions | Treemap | `treemap` |
| System building blocks / network | Block | `block-beta` |
| Data transmission layout | Packet | `packet-beta` |
| Cloud/IT architecture landscape | Architecture | `architecture-beta` |
| Set overlaps | Venn | `venn` |
| Cause-effect analysis | Ishikawa / Fishbone | `ishikawa` |
| Generic hierarchy/tree | Tree View | `treeView` |
| Strategy mapping | Wardley Map | `wardley` |
| Event-driven system modeling | Event Modeling | `eventmodeling` |
| Numeric series comparison | XY Chart | `xychart-beta` |
| UML sequence (alt renderer) | ZenUML | `zenuml` |
| Actors and use cases | Use Case | `usecase` |
| Agent/tool call graphs | Agent Flow | `agentflow` |
| Sense-making framework | Cynefin | `cynefin` |
| Parallel process lanes | Swimlanes | `swimlanes` |
| Grammar production rules | Railroad | `railroad` |

Pick the *narrowest* type that matches the relationship — e.g. prefer
`stateDiagram-v2` over `flowchart` for state transitions, and `erDiagram`
over a generic flowchart for schemas. A wrong-but-renderable type still
passes `mmdc` validation, so this choice isn't caught by tooling.

## Style rules for neat diagrams

Apply regardless of diagram type:

1. **One direction per diagram.** `TD`/`TB` for hierarchies and process
   steps, `LR` for pipelines/timelines; stay consistent within a doc.
2. **Meaningful node IDs, human labels.** `A[Client]` not `A[A]`; short
   stable IDs (`api`, `db`, `auth`): `client --> api --> auth`.
3. **Label edges that aren't obvious.** `api -->|401| client` beats an
   unlabeled arrow when the condition matters.
4. **Keep it small.** More than ~15 nodes or ~20 edges signals splitting
   into two diagrams rather than growing one dense graph.
5. **No inline styling hacks.** Avoid `style`/`classDef` overrides unless
   a legend is explicitly needed; the default theme renders consistently.
6. **Comment intent, not syntax.** `%% comment` sparingly, explaining
   *why* a branch exists.
7. **Accessible titles for standalone renders.** Set `accTitle`/`accDescr`
   so the generated SVG carries a title/alt text:
   ```
   flowchart TD
       accTitle: Auth request flow
       accDescr: Client requests a token from the auth service before calling the API.
       Client --> Auth --> API
   ```
