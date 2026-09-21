**A(a) Similarity Definition**



Similarity is defined as the Jaccard similarity between sets of normalized

word 3-grams generated from the title and body of each notice.



Two representations were compared:

1\. Normalized word 3-grams

2\. Normalized character 5-grams



Word 3-grams were selected because they gave better separation between

labelled same and different pairs.



Word 3-gram:

Same mean similarity = 0.641

Different mean similarity = 0.2623

Separation = 0.3787



Character 5-gram:

Same mean similarity = 0.7002

Different mean similarity = 0.433

Separation = 0.2672



Signal/noise decisions:

\- estimated\_value: signal; it is a structured parsed value and is usually reliable.

\- closing\_date: signal, but not a hard identity key because corrigenda can change it.

\- reference numbers: noise for cross-portal matching because each portal creates unrelated reference numbers.

\- portal boilerplate: noise because nodal aggregators repeat large common blocks.



Chosen representation: normalized word 3-grams over title + body using Jaccard similarity.



Adoption cost: the system must normalize/tokenize the notice text and store/process

the word 3-gram representation, which adds preprocessing and storage/indexing work.



**A(b) Reduced Representation and Similarity Estimation**



Exact Jaccard similarity over the complete word 3-gram representation

requires storing/processing the full set of shingles. I therefore used

MinHash signatures as a reduced representation.



The accuracy requirement was set to an absolute similarity-estimation

error of at most 0.06 for at least 95% of the labelled pairs.



Results on all 900 manually labelled pairs:



MinHash size    Mean error    95th percentile    Maximum error

64              0.03716       0.09711             0.20312

128             0.02730       0.06697             0.13900

256             0.01805       0.04448             0.07650

512             0.01366       0.03466             0.06184



There were 0 failures for every signature size.



I selected a 256-value MinHash signature because its 95th-percentile

error of 0.04448 satisfies the 0.06 accuracy requirement while using

half the storage of a 512-value signature. Increasing to 512 gives

better accuracy but increases the signature size by 2x for a relatively

smaller reduction in error.



Therefore the implemented reduced representation is a 256-value

MinHash signature.



**A(c) Candidate Retrieval and Risk**



Comparing every notice with every other notice requires 71,994,000

pair comparisons for 12,000 notices, which is not suitable for the

nightly time limit.



I built an inverted index over normalized word 3-grams. Very common

3-grams were excluded using a document-frequency cutoff of 10, and

each notice contributes up to its 64 rarest 3-grams to candidate

retrieval.



On the 900 labelled pairs, 273 of 279 labelled same pairs survived

the candidate stage, giving candidate-stage recall of 97.85%.



The probability that a pair survives increases strongly with its true

similarity. Pairs above 0.6 similarity had 100% survival in the labelled

sample, while low-similarity pairs were mostly filtered out.



The full corpus produced 196,617 unique candidate pairs compared with

71,994,000 all-pairs comparisons, reducing candidate work by about

99.73%. The mean candidate list was 21.53 notices, with P95 = 39,

P99 = 47 and maximum = 65.



I use a numerical false-merge to missed-merge cost ratio of 100:1.

Therefore candidate generation is configured to retain likely true

duplicates rather than aggressively merging records. The candidate

stage only retrieves possible matches; the final similarity threshold

makes the duplicate decision.



**B(d) Retrieval structure and database access**



The retrieval structure from A(c) was stored as persistent relational data in PostgreSQL. The schema contains a notices table with notice\_id as the primary key and a shingle\_index table containing (shingle, notice\_id) posting entries. The database contains 12,000 notices and 724,646 indexed rare-shingle postings.



I chose a B-tree index on (shingle, notice\_id) because candidate lookup begins with an exact normalized shingle and then retrieves the associated notice IDs. PostgreSQL can therefore locate the relevant posting rows through the index rather than scanning the complete inverted index.



The measured lookup for the shingle 520 and 70 used an Index Only Scan with 10 rows returned, zero heap fetches, and 0.070 ms execution time. As a forced alternative, I disabled index and bitmap scans. PostgreSQL then used a Parallel Sequential Scan, examining the table and removing 241,545 rows by the filter per worker; execution time was 9.741 ms.



This measurement supports the indexed access path because the lookup can be resolved from the index while the sequential alternative must scan the relation.



**B(e) Full-corpus retrieval distribution, hotspot and mitigation**



The retrieval was run over the full corpus of 12,000 notices. Before

mitigation, the system generated 258,783 candidate references, with a mean

of 21.57 candidates per notice, median 20, P95 39, P99 47 and maximum 67.

There were 196,978 unique candidate pairs. The measured wall-clock time was

15.901 seconds, which is below the 20-minute nightly budget on the current

corpus.



The work was unevenly distributed. The highest-cost notices generated up

to 67 candidates. The top hotspot was N010649 from P073 with 64 candidates,

followed by notices from P020, P006, P229, P063, P004 and other portals.

P004 occurred repeatedly among the high-cost notices.



The portal profile explains why this can happen. Portals use different

formats, and some append repeated disclaimer/footer text. Some portals also

republish notices and corrigenda as new notices. The retrieval design keeps

up to 64 rare word 3-grams per notice and accepts shingles with document

frequency <= 10. Therefore, a notice containing many shingles that are rare

in the overall corpus can contribute many posting lookups. The candidate

set is the union of notices reached through those postings, producing an

uneven workload. Portal volume also matters because high-volume portals

provide more opportunities for overlapping shingles.



As a mitigation, the maximum indexed rare shingles was reduced from 64 to

32 per notice. This reduced total candidate references from 258,783 to

63,522, mean candidates from 21.57 to 5.29, P95 from 39 to 11, P99 from 47

to 13, and the maximum from 67 to 18. Unique candidate pairs fell from

196,978 to 46,478.



The mitigated wall-clock retrieval time was 14.611 seconds. Thus both

configurations are comfortably below the 20-minute budget for the measured

12,000-notice corpus, although the reduced candidate quantity is the more

important scaling benefit because the expensive downstream similarity

stage operates on the candidate set.



The mitigation has a measurable retrieval-quality cost. On the 900 labelled

pairs, 273/279 labelled same pairs survived before mitigation (97.85%),

whereas 256/279 survived after mitigation (91.76%). Thus the mitigation

removed 17 of the 279 labelled duplicate pairs and reduced same-pair

survival by 6.09 percentage points.



This trade-off is material because the product's stated cost asymmetry is

100:1 for a false merge versus a missed merge. Therefore the reduction in

retrieval quantity cannot be treated as automatically beneficial: it must

be considered together with the measured loss of duplicate recall.

