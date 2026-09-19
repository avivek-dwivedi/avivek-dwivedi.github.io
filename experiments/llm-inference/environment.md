# Experiment Environment

Fill with actual experiment environment before publishing benchmark claims.
Do not expose this template on the website as placeholder text.

- **Model:** _fill with actual model name and revision_
- **GPU:** _fill with GPU model_
- **GPU count:** _fill with count_
- **CUDA:** _fill with CUDA version_
- **Driver:** _fill with driver version_
- **vLLM:** _fill with installed vLLM version_
- **Python:** _fill with Python version_
- **dtype:** _fill (e.g. auto, bfloat16, float16)_
- **max model length:** _fill_
- **OS:** _fill_
- **Benchmark date:** _fill with ISO-8601 date_

## Notes

- Record the exact `vllm serve` flags used.
- Record the exact `vllm bench serve` flags used.
- Record GPU memory capacity and any tensor-parallel size.
- This file is for the repository record. The article should not quote numbers until this is populated and a results file exists.