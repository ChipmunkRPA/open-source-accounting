# GovInfo eCFR research snapshot: 2026-10-04

This Standard collection contains **31,604 searchable regulatory section texts**
from five downloaded XML containers: eCFR Titles 12, 17, 26, 31 and 48. It adds
government-source reading material, not 31,604 original articles or independent
publications. The existing original-article library is counted separately.

| Title | Raw section elements | Exported section texts |
|---|---:|---:|
| 12: Banks and Banking | 7,199 | 6,932 |
| 17: Commodity and Securities Exchanges | 3,528 | 3,318 |
| 26: Internal Revenue | 6,160 | 6,013 |
| 31: Money and Finance: Treasury | 5,398 | 5,234 |
| 48: Federal Acquisition Regulations System | 11,544 | 10,107 |

The 31,604 exported source records contain 31,603 distinct normalized text hashes.
One identical Title 48 provision appears at two distinct official nodes; both
locators are preserved and the duplicate text is disclosed rather than counted
as another distinct text.

The retained source XML totals 175,207,199 bytes. Its 33,829 section elements include
2,215 metadata-only entries and ten entries held for copyright-notice review;
neither category's records or body text is included in the public shards.
All raw XML and the generated SQLite database remain outside this publication.
The manifest and five logical compressed JSONL streams bind each projection to
the exact source URL, container hash, section locator, volume and retrieval time.

## Dates and source status

Amendment dates vary between volumes inside a title container. Read each record's
`declared_amendment_date_raw`; the listing's last-modified timestamp and download
timestamp are different fields. This collection does not claim every rule is
current through October 4 or that a historical volume label is an effective date.
For a decision, check the official source, amendments and applicability.

These are whitespace-normalized XML text projections. The source contains graphics
in 203 section elements and tables or math in 1,095; affected records carry explicit
flags. External images and incorporated standards were not downloaded. Layout,
formulas and missing graphics need inspection in the originating publication.
The project does not certify an official edition, legal conclusion or professional
accounting review. No Source operation rights or Agent admission is granted.

## Rights and attribution

Sources: [GovInfo bulk developer documentation](https://www.govinfo.gov/developers),
[GovInfo public-domain and copyright policy](https://www.govinfo.gov/about/policies).
U.S. government regulatory text is distinguished from external incorporated works,
third-party notices and images. An incorporation reference does not acquire or
license the underlying standard. Copyright-notice and ownership-wording matches are conservatively held
for review; this screening is not a claim that a keyword test decides copyright.
No NARA/Federal Register seal, branding or external graphics is redistributed.
The original project article license does not relabel government-source text.

Title 26 is stored in two ordered transfer parts; the other four compressed streams
are single files. Each part is at most 10 MiB. Download every file listed in the
manifest. The loader checks each part and the exact reassembled gzip hash before
reading any section. The logical dataset bytes and source counts are unchanged.

## Search the downloaded snapshot

Python's standard library and SQLite FTS5 suffice. From the repository root:

```sh
python tools/govinfo/load_snapshot.py --snapshot corpus/govinfo/ecfr/2026-10-04 --database /tmp/accounting-ecfr-20261004.sqlite
python tools/govinfo/search_corpus.py 'internal control' --title 17 --database /tmp/accounting-ecfr-20261004.sqlite
python tools/govinfo/search_corpus.py 'cost accounting' --title 48 --database /tmp/accounting-ecfr-20261004.sqlite
```

The loader checks every compressed shard, source binding, text hash and count.
It refuses to overwrite an existing database. Search results retain source dates,
locators and rendering limitations. This is a downloadable research dataset and
local search tool; it does not activate the hosted website or a paid Agent.

## Collect a later snapshot

Use a new external workspace so earlier source bytes and dates remain available:

```sh
python tools/govinfo/collect_ecfr.py --workspace /tmp/accounting-ecfr-next --discover
python tools/govinfo/index_ecfr.py --workspace /tmp/accounting-ecfr-next
python tools/govinfo/export_ecfr.py --workspace /tmp/accounting-ecfr-next --destination /tmp/accounting-ecfr-next-public
```

The collector follows only the official HTTPS GovInfo host, checks listed XML
sizes, preserves byte hashes and resumes verified files. Changed listings require
a new snapshot workspace. The indexer rejects DTD/entity-bearing XML, detects
duplicate composite identities, separates reserved/empty text, and withholds notice
matches. Independently review new dates, rights flags, counts and source changes
before publishing any later snapshot. Future archives are not automatically added
to Git; storage planning is a separate step.
