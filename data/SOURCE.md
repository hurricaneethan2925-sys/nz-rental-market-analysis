# Data provenance

- Provider: The Ministry of Business, Innovation and Employment (MBIE), via Tenancy Services.
- Source page: https://www.tenancy.govt.nz/about-tenancy-services/data-and-statistics/rental-bond-data/
- Download: https://www.tenancy.govt.nz/assets/Uploads/Tenancy/Rental-bond-data/detailed-monthly-tla-tenancy-september.csv?m=24491d4fca0935f5cd5d4da6145efa6f3a12ab03
- Page release date: 10 September 2026.
- Retrieved for this project: 1 October 2026 (Pacific/Auckland).
- Coverage: February 1993–July 2026, monthly territorial-authority file.
- Original file is preserved byte-for-byte.
- Data licence: CC BY 3.0 NZ, https://creativecommons.org/licenses/by/3.0/nz/
- SHA-256: `a50937ef88e1834c9a804215115586dd6be63468173f9e23495d868c6ca3ee3f`

The source describes confidentiality rounding and suppression. It warns that migration between bond systems may cause discontinuities and revisions. Consult the current source page before interpreting a refreshed release.

## Fields used

| Original field | Analysis field | Meaning |
| --- | --- | --- |
| TimeFrame | month | Tenancy start month |
| location_id | location_id | Territorial-authority identifier |
| location | location | Published area name |
| LodgedBonds | lodged_bonds | Reported lodged-bond count |
| ActiveBonds | active_bonds | Active-bond stock |
| ClosedBonds | closed_bonds | Reported closed-bond count |
| MedianRent | median_rent | Published median weekly rent, NZD |
| GeometricMeanRent | geometric_mean_rent | Published geometric mean weekly rent, NZD |

Other columns remain available in the original CSV but are not used in this analysis. National and unallocated rows are excluded from the cleaned TA table. Medians are used directly from the named source column, not reconstructed from the geometric mean.
