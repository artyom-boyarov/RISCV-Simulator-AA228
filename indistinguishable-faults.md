# States with identical observed likelihoods

Source: `likelihood-campaign/likelihoods.npz`. 8 tests, 247 states, 597 observed outcome labels, 10 runs per test and state.

13 matching groups contain 68 states; the other 179 states have unique observed likelihoods.

States in each group have exactly the same empirical likelihood for every test and outcome, including timeouts and simulator failures when present. State indices and names refer to this campaign's saved enumeration.

These are comparisons of finite samples, not proof that the underlying probabilities are identical or different. With only this many runs, rare outcomes can be missed and sampling noise can make matching true distributions look different. Unique estimates do not guarantee reliable diagnosis; repeated tests and more samples may change the result.

## Group 1: 25 states

- `0`: `faults/cache/valid-bit00-stuck-at-0-100.txt` (10 runs per test)
- `2`: `faults/cache/valid-bit00-bit-flip-100.txt` (10 runs per test)
- `14`: `faults/cache/tag-bit00-bit-flip-100.txt` (10 runs per test)
- `26`: `faults/cache/tag-bit02-bit-flip-100.txt` (10 runs per test)
- `32`: `faults/cache/tag-bit03-bit-flip-100.txt` (10 runs per test)
- `38`: `faults/cache/tag-bit04-bit-flip-100.txt` (10 runs per test)
- `44`: `faults/cache/tag-bit05-bit-flip-100.txt` (10 runs per test)
- `50`: `faults/cache/tag-bit06-bit-flip-100.txt` (10 runs per test)
- `56`: `faults/cache/tag-bit07-bit-flip-100.txt` (10 runs per test)
- `62`: `faults/cache/tag-bit08-bit-flip-100.txt` (10 runs per test)
- `74`: `faults/cache/tag-bit10-bit-flip-100.txt` (10 runs per test)
- `80`: `faults/cache/tag-bit11-bit-flip-100.txt` (10 runs per test)
- `86`: `faults/cache/tag-bit12-bit-flip-100.txt` (10 runs per test)
- `92`: `faults/cache/tag-bit13-bit-flip-100.txt` (10 runs per test)
- `98`: `faults/cache/tag-bit14-bit-flip-100.txt` (10 runs per test)
- `104`: `faults/cache/tag-bit15-bit-flip-100.txt` (10 runs per test)
- `110`: `faults/cache/tag-bit16-bit-flip-100.txt` (10 runs per test)
- `116`: `faults/cache/tag-bit17-bit-flip-100.txt` (10 runs per test)
- `122`: `faults/cache/tag-bit18-bit-flip-100.txt` (10 runs per test)
- `128`: `faults/cache/tag-bit19-bit-flip-100.txt` (10 runs per test)
- `134`: `faults/cache/tag-bit20-bit-flip-100.txt` (10 runs per test)
- `140`: `faults/cache/tag-bit21-bit-flip-100.txt` (10 runs per test)
- `146`: `faults/cache/tag-bit22-bit-flip-100.txt` (10 runs per test)
- `152`: `faults/cache/tag-bit23-bit-flip-100.txt` (10 runs per test)
- `158`: `faults/cache/tag-bit24-bit-flip-100.txt` (10 runs per test)

Shared observed likelihoods:

- `cache_modified_kernel`: `return:1`: 1
- `cache_single_address_kernel`: `return:1`: 1
- `cache_tag_bits_kernel`: `return:1`: 1
- `memory_address_bits_kernel`: `return:4096`: 1
- `memory_kernel`: `return:2`: 1
- `memory_page_kernel`: `return:2`: 1
- `memory_stride_kernel`: `return:17`: 1
- `sobel_image`: `return:3039`: 1

## Group 2: 7 states

- `1`: `faults/cache/valid-bit00-stuck-at-1-100.txt` (10 runs per test)
- `4`: `faults/cache/valid-bit00-stuck-at-1-50.txt` (10 runs per test)
- `7`: `faults/cache/modified-bit00-stuck-at-1-100.txt` (10 runs per test)
- `10`: `faults/cache/modified-bit00-stuck-at-1-50.txt` (10 runs per test)
- `244`: `faults/branch-predictor-100-percent.txt` (10 runs per test)
- `245`: `faults/branch-predictor-50-percent.txt` (10 runs per test)
- `246`: `no_fault` (10 runs per test)

Shared observed likelihoods:

- `cache_modified_kernel`: `return:0`: 1
- `cache_single_address_kernel`: `return:0`: 1
- `cache_tag_bits_kernel`: `return:0`: 1
- `memory_address_bits_kernel`: `return:0`: 1
- `memory_kernel`: `return:0`: 1
- `memory_page_kernel`: `return:0`: 1
- `memory_stride_kernel`: `return:0`: 1
- `sobel_image`: `return:1690`: 1

## Group 3: 2 states

- `6`: `faults/cache/modified-bit00-stuck-at-0-100.txt` (10 runs per test)
- `8`: `faults/cache/modified-bit00-bit-flip-100.txt` (10 runs per test)

Shared observed likelihoods:

- `cache_modified_kernel`: `return:1`: 1
- `cache_single_address_kernel`: `return:0`: 1
- `cache_tag_bits_kernel`: `return:0`: 1
- `memory_address_bits_kernel`: `return:0`: 1
- `memory_kernel`: `return:0`: 1
- `memory_page_kernel`: `return:2`: 1
- `memory_stride_kernel`: `return:17`: 1
- `sobel_image`: `return:1690`: 1

## Group 4: 2 states

- `60`: `faults/cache/tag-bit08-stuck-at-0-100.txt` (10 runs per test)
- `63`: `faults/cache/tag-bit08-stuck-at-0-50.txt` (10 runs per test)

Shared observed likelihoods:

- `cache_modified_kernel`: `return:0`: 1
- `cache_single_address_kernel`: `return:0`: 0.8, `timeout`: 0.2
- `cache_tag_bits_kernel`: `return:9`: 1
- `memory_address_bits_kernel`: `return:0`: 1
- `memory_kernel`: `return:0`: 1
- `memory_page_kernel`: `return:0`: 1
- `memory_stride_kernel`: `return:0`: 1
- `sobel_image`: `return:1690`: 1

## Group 5: 9 states

- `168`: `faults/memory/bit00-stuck-at-0-100.txt` (10 runs per test)
- `169`: `faults/memory/bit00-stuck-at-1-100.txt` (10 runs per test)
- `174`: `faults/memory/bit01-stuck-at-0-100.txt` (10 runs per test)
- `175`: `faults/memory/bit01-stuck-at-1-100.txt` (10 runs per test)
- `180`: `faults/memory/bit02-stuck-at-0-100.txt` (10 runs per test)
- `181`: `faults/memory/bit02-stuck-at-1-100.txt` (10 runs per test)
- `186`: `faults/memory/bit03-stuck-at-0-100.txt` (10 runs per test)
- `187`: `faults/memory-bit10-stuck-at-1.txt` (10 runs per test)
- `188`: `faults/memory/bit03-stuck-at-1-100.txt` (10 runs per test)

Shared observed likelihoods:

- `cache_modified_kernel`: `return:1`: 1
- `cache_single_address_kernel`: `return:0`: 1
- `cache_tag_bits_kernel`: `return:0`: 1
- `memory_address_bits_kernel`: `return:0`: 1
- `memory_kernel`: `return:0`: 1
- `memory_page_kernel`: `return:1`: 1
- `memory_stride_kernel`: `return:17`: 1
- `sobel_image`: `return:1690`: 1

## Group 6: 6 states

- `170`: `faults/memory/bit00-bit-flip-100.txt` (10 runs per test)
- `176`: `faults/memory/bit01-bit-flip-100.txt` (10 runs per test)
- `182`: `faults/memory/bit02-bit-flip-100.txt` (10 runs per test)
- `189`: `faults/memory/bit03-bit-flip-100.txt` (10 runs per test)
- `195`: `faults/memory/bit04-bit-flip-100.txt` (10 runs per test)
- `201`: `faults/memory/bit05-bit-flip-100.txt` (10 runs per test)

Shared observed likelihoods:

- `cache_modified_kernel`: `return:0`: 1
- `cache_single_address_kernel`: `return:0`: 1
- `cache_tag_bits_kernel`: `return:0`: 1
- `memory_address_bits_kernel`: `return:0`: 1
- `memory_kernel`: `return:0`: 1
- `memory_page_kernel`: `return:3073`: 1
- `memory_stride_kernel`: `return:3201`: 1
- `sobel_image`: `return:1690`: 1

## Group 7: 3 states

- `194`: `faults/memory/bit04-stuck-at-1-100.txt` (10 runs per test)
- `199`: `faults/memory/bit05-stuck-at-0-100.txt` (10 runs per test)
- `200`: `faults/memory/bit05-stuck-at-1-100.txt` (10 runs per test)

Shared observed likelihoods:

- `cache_modified_kernel`: `return:1`: 1
- `cache_single_address_kernel`: `return:0`: 1
- `cache_tag_bits_kernel`: `return:0`: 1
- `memory_address_bits_kernel`: `return:0`: 1
- `memory_kernel`: `return:0`: 1
- `memory_page_kernel`: `return:1`: 1
- `memory_stride_kernel`: `return:1`: 1
- `sobel_image`: `return:1690`: 1

## Group 8: 2 states

- `205`: `faults/memory/bit06-stuck-at-0-100.txt` (10 runs per test)
- `206`: `faults/memory/bit06-stuck-at-1-100.txt` (10 runs per test)

Shared observed likelihoods:

- `cache_modified_kernel`: `return:0`: 1
- `cache_single_address_kernel`: `return:0`: 1
- `cache_tag_bits_kernel`: `return:0`: 1
- `memory_address_bits_kernel`: `return:0`: 1
- `memory_kernel`: `return:0`: 1
- `memory_page_kernel`: `return:65`: 1
- `memory_stride_kernel`: `return:1`: 1
- `sobel_image`: `return:1690`: 1

## Group 9: 2 states

- `211`: `faults/memory/bit07-stuck-at-0-100.txt` (10 runs per test)
- `212`: `faults/memory/bit07-stuck-at-1-100.txt` (10 runs per test)

Shared observed likelihoods:

- `cache_modified_kernel`: `return:0`: 1
- `cache_single_address_kernel`: `return:0`: 1
- `cache_tag_bits_kernel`: `return:0`: 1
- `memory_address_bits_kernel`: `return:0`: 1
- `memory_kernel`: `return:0`: 1
- `memory_page_kernel`: `return:1`: 1
- `memory_stride_kernel`: `return:1`: 1
- `sobel_image`: `return:1690`: 1

## Group 10: 2 states

- `219`: `faults/memory/bit08-bit-flip-100.txt` (10 runs per test)
- `225`: `faults/memory/bit09-bit-flip-100.txt` (10 runs per test)

Shared observed likelihoods:

- `cache_modified_kernel`: `return:0`: 1
- `cache_single_address_kernel`: `return:0`: 0.7, `timeout`: 0.3
- `cache_tag_bits_kernel`: `return:0`: 1
- `memory_address_bits_kernel`: `return:0`: 1
- `memory_kernel`: `return:0`: 1
- `memory_page_kernel`: `return:3074`: 1
- `memory_stride_kernel`: `return:3201`: 1
- `sobel_image`: `return:1690`: 1

## Group 11: 3 states

- `223`: `faults/memory/bit09-stuck-at-0-100.txt` (10 runs per test)
- `229`: `faults/memory/bit10-stuck-at-0-100.txt` (10 runs per test)
- `230`: `faults/memory/bit10-stuck-at-1-100.txt` (10 runs per test)

Shared observed likelihoods:

- `cache_modified_kernel`: `return:0`: 1
- `cache_single_address_kernel`: `return:0`: 0.8, `timeout`: 0.2
- `cache_tag_bits_kernel`: `return:0`: 1
- `memory_address_bits_kernel`: `return:0`: 1
- `memory_kernel`: `return:0`: 1
- `memory_page_kernel`: `return:0`: 1
- `memory_stride_kernel`: `return:1`: 1
- `sobel_image`: `return:1690`: 1

## Group 12: 2 states

- `224`: `faults/memory/bit09-stuck-at-1-100.txt` (10 runs per test)
- `236`: `faults/memory/bit11-stuck-at-0-100.txt` (10 runs per test)

Shared observed likelihoods:

- `cache_modified_kernel`: `return:0`: 1
- `cache_single_address_kernel`: `return:0`: 0.9, `timeout`: 0.1
- `cache_tag_bits_kernel`: `return:0`: 1
- `memory_address_bits_kernel`: `return:0`: 1
- `memory_kernel`: `return:0`: 1
- `memory_page_kernel`: `return:0`: 1
- `memory_stride_kernel`: `return:1`: 1
- `sobel_image`: `return:1690`: 1

## Group 13: 3 states

- `235`: `faults/memory-bit11-stuck-at-0.txt` (10 runs per test)
- `237`: `faults/memory-bit11-stuck-at-1.txt` (10 runs per test)
- `238`: `faults/memory/bit11-stuck-at-1-100.txt` (10 runs per test)

Shared observed likelihoods:

- `cache_modified_kernel`: `return:0`: 1
- `cache_single_address_kernel`: `return:0`: 1
- `cache_tag_bits_kernel`: `return:0`: 1
- `memory_address_bits_kernel`: `return:0`: 1
- `memory_kernel`: `return:0`: 1
- `memory_page_kernel`: `return:0`: 1
- `memory_stride_kernel`: `return:1`: 1
- `sobel_image`: `return:1690`: 1
