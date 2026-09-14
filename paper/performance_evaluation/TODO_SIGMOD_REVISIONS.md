# Deferred content/citation issues (NOT fixed during this template migration)

This file exists per the migration task's explicit instruction: this migration
is mechanical/format-only (SIGMOD `acmart` -> Elsevier `elsarticle` for
Performance Evaluation). Any citation-correctness or other content issue
noticed along the way is recorded here for a future, separate, human-reviewed
revision pass -- it is intentionally **not** corrected in either
`paper/sigmod2027/` (frozen) or `paper/performance_evaluation/` (this new
template) as part of this task.

## 1. Possible author-name error in `vietri2018lecar` (LeCaR, HotStorage 2018)

`refs.bib` (copied verbatim into the new template) contains:

```
@inproceedings{vietri2018lecar,
  author = {Vietri, Giuseppe and Rodriguez, Liana V. and Martinez, William A. and ...},
  title = {Driving Cache Replacement with ML-based LeCaR},
  ...
}
```

The middle co-author is recorded as **"Martinez, William A."**. Independent
recollection of this FIU cache-replacement research line (Rangaswami / Zhao /
Narasimhan group) suggests the actual co-author on this line of work is
**"Martinez, Wendy A."**, not "William A." This was not independently
re-verified against the publisher's own metadata (USENIX HotStorage 2018
page) as part of this mechanical migration -- that verification, and any bib
fix, is exactly the kind of citation-content cleanup this task's SOP
explicitly excludes ("no citation-content cleanup beyond what's needed to
compile").

**Action for a future revision pass:** verify the correct given name against
the USENIX HotStorage'18 program / DBLP entry for this paper, and correct
`refs.bib` in both the SIGMOD source (if that bundle is ever reopened) and
this Performance Evaluation template if confirmed wrong.

## 2. Unused bibliography entry

`narita2019efficient` (Narita, Yasui, Yata, "Efficient Counterfactual
Learning from Bandit Feedback", AAAI 2019) is present in `refs.bib` but does
not appear to be `\cite`'d from any section file in either the SIGMOD source
or this template. Harmless (compiles fine either way), but worth a cleanup
pass: either cite it where relevant (Section~10, counterfactual/bandit
related work) or remove it.

## 3. General note

No other citation-metadata problems were identified during this migration,
but this migration's review was scoped to "does it compile / does it
mechanically match the SIGMOD source," not a full bibliographic audit against
publisher records. A dedicated citation-audit pass (checking every `\cite`
key's author list, venue, year, and DOI against DBLP/publisher records) has
not been performed for either manuscript and is out of scope here.
