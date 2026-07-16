# Stage 7A-R real-panel data-lock review

**Accepted data-content lock:** `3d171f7ce109d2e340f2f4f37f5376a81a4f8ec06761595a5c120ffd457fece6`

All 12 independent checks passed. The corpus contains 8 training, 4 development, and 12 locked parent families. Relative-index pseudo-panels remain forbidden.

## Checks

- PASS — hash_recomputed
- PASS — partition_counts_exact
- PASS — shortages_zero
- PASS — source_families_unique
- PASS — candidate_ids_unique
- PASS — alignment_legal
- PASS — training_lengths
- PASS — locked_lengths
- PASS — minimum_series
- PASS — hash_fields_valid
- PASS — no_excessive_missingness
- PASS — relative_index_forbidden

## Accepted families

| Partition | Candidate | Length | Series | Alignment |
|---|---|---:|---:|---|
| training | train_monash_fred_md | 728 | 107 | calendar_start_and_length_aligned |
| training | train_monash_nn5_daily | 791 | 111 | calendar_start_and_length_aligned |
| training | train_monash_tourism_monthly | 333 | 168 | calendar_start_and_length_aligned |
| training | train_darts_energy | 35064 | 20 | native_wide_chronology |
| training | train_darts_weather | 52695 | 21 | native_wide_chronology |
| training | train_rdatasets_irates | 531 | 10 | native_wide_chronology |
| training | train_rdatasets_forward_fx | 276 | 9 | native_wide_chronology |
| training | train_rdatasets_banking_crises | 211 | 69 | native_wide_chronology |
| development | dev_rdatasets_seatbelts | 192 | 8 | native_wide_chronology |
| development | dev_rdatasets_usmacrog | 204 | 12 | native_wide_chronology |
| development | dev_darts_australian_tourism | 36 | 96 | native_wide_chronology |
| development | dev_darts_ilinet | 1301 | 8 | native_wide_chronology |
| locked | locked_darts_traffic | 17544 | 862 | native_wide_chronology |
| locked | locked_darts_exchange | 7588 | 8 | native_wide_chronology |
| locked | locked_rdatasets_ozone | 24 | 1728 | native_wide_chronology |
| locked | locked_rdatasets_australian_elections | 27 | 17 | native_wide_chronology |
| locked | locked_rdatasets_income_inequality | 66 | 22 | native_wide_chronology |
| locked | locked_rdatasets_manufacturing_cost | 25 | 9 | native_wide_chronology |
| locked | locked_rdatasets_cigar | 30 | 46 | native_entity_time_panel |
| locked | locked_rdatasets_gasoline | 19 | 18 | native_entity_time_panel |
| locked | locked_rdatasets_produc | 17 | 48 | native_entity_time_panel |
| locked | locked_rdatasets_sumhes | 26 | 125 | native_entity_time_panel |
| locked | locked_rdatasets_incidents | 50 | 204 | native_entity_time_panel |
| locked | locked_rdatasets_grunfeld | 20 | 10 | native_entity_time_panel |

This acceptance authorizes only the exact-capacity Stage 7A-R run against the frozen data identities and content hashes.
