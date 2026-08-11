# Wiki2018 Provenance Review for v0.2 Preview

Review date: 2026-08-11

Scope: LAFC-Evict v0.2 real-data preview, Wiki2018 family only.

## Classification

`APPROVED_WITH_ATTRIBUTION_AND_CAVEAT`

The official Wikimedia documentation supports public redistribution of derived preview rows generated from Wikimedia pageview data. The preview should still include source attribution and non-endorsement wording because this is good scholarly provenance and avoids implying Wikimedia Foundation affiliation.

## Evidence

- Wikimedia Downloads lists `Pageview, Mediacount, Unique, and other stats` as Analytics data files and links to dump licensing information.
- Wikimedia dump licensing states that all Analytics datasets are available under the Creative Commons CC0 public domain dedication unless otherwise specified.
- The `/other/pageviews/` readme states that pageview statistics are available for download and that all Analytics datasets are available under CC0.
- Wikimedia Analytics API access policy states that API-provided data is available under CC0 and that API datasets can also be downloaded in bulk through `dumps.wikimedia.org`.
- Wikimedia pageview definition documentation describes pageviews as aggregated request counts and identifies public dump files/API/web tools as public data sources derived from private pageview tables.

Official source URLs:

- https://dumps.wikimedia.org/
- https://dumps.wikimedia.org/legal.html
- https://dumps.wikimedia.org/other/pageviews/readme.html
- https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/documentation/access-policy.html
- https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/concepts/page-views.html
- https://meta.wikimedia.org/wiki/Research:Page_view

## Dataset-Specific Scope

The LAFC-Evict v0.2 preview:

- includes only rows derived from the `wiki2018` family;
- does not redistribute raw Wikimedia pageview dump rows;
- does not expose raw page titles;
- pseudonymizes object identifiers;
- stores derived cache-eviction features and supervision labels;
- excludes Brightkite, CitiBike, CloudPhysics, MetaCDN, MetaKV, and Twemcache pending separate redistribution review.

This distinction reduces redistribution risk because the released artifacts are derived, pseudonymized training/evaluation rows rather than a repackaged copy of the upstream pageview dumps. The upstream data source is also documented by Wikimedia as CC0.

## Final Attribution Wording

LAFC-Evict v0.2 preview includes derived cache-eviction supervision examples generated from Wikimedia public pageview data. Wikimedia pageview data is made available by the Wikimedia Foundation at `https://dumps.wikimedia.org/other/pageviews/` under the Creative Commons CC0 1.0 public domain dedication. This LAFC-Evict preview does not redistribute raw pageview dump rows or raw page titles; object identifiers are deterministic public pseudonyms. Wikimedia and the Wikimedia Foundation do not endorse this derived dataset.

## License Metadata Recommendation

Use Hugging Face metadata:

```yaml
license: cc0-1.0
```

Rationale: Wikimedia Analytics pageview data is documented as CC0, and the derived preview can be released under CC0 as a dataset. Do not describe the dataset payload as MIT. Code in the canonical publication repository remains separately licensed.

## Caveat

This review is based on public Wikimedia documentation and is not legal advice. If future releases include any non-Wiki2018 family, repeat provenance review for each source family before publication.
