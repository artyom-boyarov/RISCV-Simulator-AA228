# States with identical observed likelihoods

Source: `likelihood-campaign/likelihoods.npz`. 8 tests, 175 states, 579 observed outcome labels, 10 runs per test and state.

4 matching groups contain 36 states; the other 139 states have unique observed likelihoods.

States in each group have exactly the same empirical likelihood for every test and outcome, including timeouts and simulator failures when present. State indices and names refer to this campaign's saved enumeration.

These are comparisons of finite samples, not proof that the underlying probabilities are identical or different. With only this many runs, rare outcomes can be missed and sampling noise can make matching true distributions look different. Unique estimates do not guarantee reliable diagnosis; repeated tests and more samples may change the result.

## Group 1: 25 states

- `0`: `faults/cache/valid-bit00-stuck-at-0-100.txt`
- `2`: `faults/cache/valid-bit00-bit-flip-100.txt`
- `14`: `faults/cache/tag-bit00-bit-flip-100.txt`
- `26`: `faults/cache/tag-bit02-bit-flip-100.txt`
- `32`: `faults/cache/tag-bit03-bit-flip-100.txt`
- `38`: `faults/cache/tag-bit04-bit-flip-100.txt`
- `44`: `faults/cache/tag-bit05-bit-flip-100.txt`
- `50`: `faults/cache/tag-bit06-bit-flip-100.txt`
- `56`: `faults/cache/tag-bit07-bit-flip-100.txt`
- `62`: `faults/cache/tag-bit08-bit-flip-100.txt`
- `74`: `faults/cache/tag-bit10-bit-flip-100.txt`
- `80`: `faults/cache/tag-bit11-bit-flip-100.txt`
- `86`: `faults/cache/tag-bit12-bit-flip-100.txt`
- `92`: `faults/cache/tag-bit13-bit-flip-100.txt`
- `98`: `faults/cache/tag-bit14-bit-flip-100.txt`
- `104`: `faults/cache/tag-bit15-bit-flip-100.txt`
- `110`: `faults/cache/tag-bit16-bit-flip-100.txt`
- `116`: `faults/cache/tag-bit17-bit-flip-100.txt`
- `122`: `faults/cache/tag-bit18-bit-flip-100.txt`
- `128`: `faults/cache/tag-bit19-bit-flip-100.txt`
- `134`: `faults/cache/tag-bit20-bit-flip-100.txt`
- `140`: `faults/cache/tag-bit21-bit-flip-100.txt`
- `146`: `faults/cache/tag-bit22-bit-flip-100.txt`
- `152`: `faults/cache/tag-bit23-bit-flip-100.txt`
- `158`: `faults/cache/tag-bit24-bit-flip-100.txt`

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

- `1`: `faults/cache/valid-bit00-stuck-at-1-100.txt`
- `4`: `faults/cache/valid-bit00-stuck-at-1-50.txt`
- `7`: `faults/cache/modified-bit00-stuck-at-1-100.txt`
- `10`: `faults/cache/modified-bit00-stuck-at-1-50.txt`
- `172`: `faults/branch-predictor-100-percent.txt`
- `173`: `faults/branch-predictor-50-percent.txt`
- `174`: `no_fault`

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

- `6`: `faults/cache/modified-bit00-stuck-at-0-100.txt`
- `8`: `faults/cache/modified-bit00-bit-flip-100.txt`

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

- `169`: `faults/memory-bit11-stuck-at-0.txt`
- `170`: `faults/memory-bit11-stuck-at-1.txt`

Shared observed likelihoods:

- `cache_modified_kernel`: `return:0`: 1
- `cache_single_address_kernel`: `return:0`: 1
- `cache_tag_bits_kernel`: `return:0`: 1
- `memory_address_bits_kernel`: `return:0`: 1
- `memory_kernel`: `return:0`: 1
- `memory_page_kernel`: `return:0`: 1
- `memory_stride_kernel`: `return:1`: 1
- `sobel_image`: `return:1690`: 1
