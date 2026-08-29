---
okf_version: "0.2"
type: meeting
title: "Design session — offline vault, CRDT versus operational transform"
tier: raw
initiative: NOVA
created: "2026-08-12"
updated: "2026-08-12"
created_by: AR
updated_by: AR
status: ACTIVE
tags: [nova, offline, vault, crdt, ot, design-session]
---

# Design session — offline vault, CRDT versus operational transform

Transcript-style capture, lightly cleaned. Participants: AR, RV, SP, CL. Ninety minutes. The question on the table was how a TaskFlow board reconciles two divergent histories when a laptop comes back from a train tunnel.

---

**AR:** Framing first. The vault is the local write-ahead store. The board keeps accepting edits with no network, and at some point the two histories have to be reconciled. There are two families of answer and we should pick a family today, not a library.

**RV:** Operational transform and the convergent replicated data type family. OT is the older one — you keep a linear op log on the server and transform incoming ops against the ops that landed while the client was away.

**SP:** The thing I remember about OT is that everybody who has implemented it says the transform functions are where the bugs live.

**RV:** That is the received wisdom and I think it is right. OT puts the correctness burden in a set of pairwise transform functions, and the number of pairs grows with the number of op types. We have card move, card edit, column reorder, label change, assignee change, due date, and archive. That is a lot of pairs, and every new op type multiplies the surface.

**AR:** Whereas the replicated-data-type family puts the burden in the data structure. The merge is commutative by construction, so two clients that saw the same set of ops in any order land in the same state. You do not write a transform function per pair; you pick types whose merge is already defined.

**CL:** What does that cost me on the box? Because the replicated types I have read about carry per-character metadata and that sounded expensive.

**RV:** It is real. A naive text type keeps a tombstone per deleted character forever. The mature libraries garbage-collect, but you are still carrying more bytes than the plain string. For a card title it is nothing. For a description field with a long edit history it is measurable.

**CL:** And the envelope I published is 320 MB of headroom on the app process. If the vault lives in the browser that is not my problem, but if the server holds a replicated document per board it very much is.

**AR:** Server holds ops, not documents. Materialise on read, cache the materialised board. That keeps the server side bounded.

**SP:** Can I bring up the part I care about? Whichever family we pick, there is a residue. Two people rewrite the same card title while both are dark. No structure decides that for you — it just picks one deterministically. Deterministic is not the same as correct, and if we silently drop somebody's sentence they will notice.

**AR:** Agreed, and I want to be precise about scope here. The structure settles ordering. It does not settle intent. The residue where intent matters needs a human, and that is a UX surface, not an algorithm.

**SP:** Then I want the residue to be small and legible. If the merge produces a hundred items to review, nobody reviews them.

**RV:** It will be small. Card moves, reorders, label and assignee changes all merge cleanly — those are set and register operations. The residue is essentially same-field text rewrites, and in practice that is rare because two people rarely retitle the same card in the same window.

**AR:** So the shape is: replicated types settle everything structural, and same-field text divergence surfaces to a review queue where a person picks. Does anybody want to defend OT?

**RV:** Not really. The one honest argument for OT is that the server stays authoritative and the wire format is smaller. But we would be writing transform functions for seven op types and we would be maintaining them forever.

**CL:** I would rather carry bytes than carry pairwise correctness proofs.

**AR:** Then the family is settled and the library is the next question. RV to evaluate candidates and report. The criteria I care about, in order: bundle size, garbage collection of tombstones, whether the clock is exposed so our sync layer can piggyback on it, and whether the maintainer answers issues.

**SP:** And a fifth: can I read the divergence out of it? If I cannot enumerate the residue I cannot build the review queue.

**AR:** Good. Add it to the list.

**CL:** One more from me. Whatever it is, I want a bounded local store. An unbounded write-ahead log in a browser origin is a support ticket waiting to happen.

**AR:** Bounded, with a deterministic eviction policy. That is a workstream on its own.

---

## Actions

- RV: evaluate replicated-data-type libraries against the five criteria; write up as a raw note.
- SP: sketch the review queue for the text-divergence residue.
- CL: confirm the browser-side store bound against the published envelope.
- AR: draft the decision entry once the library evaluation lands.
