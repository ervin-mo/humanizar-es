# Third-party software and models

The code in this repository is MIT (see `LICENSE`). `scripts/install_model.py` downloads two
third-party files separately. They are not part of the repository.

| File | What it is | License | Source |
|---|---|---|---|
| `Qwen3-4B-Base.Q8_0.gguf` | Alibaba's (Qwen team) Qwen3-4B-Base base model, quantized to GGUF Q8_0 by mradermacher | Apache-2.0 | [Qwen/Qwen3-4B-Base](https://huggingface.co/Qwen/Qwen3-4B-Base) · [GGUF](https://huggingface.co/mradermacher/Qwen3-4B-Base-GGUF) |
| `hip-qwen3-4b-base.gguf` | The HIP (*Humanization by Iterative Paraphrasing*) LoRA adapter by Yixuan Even Xu, Ziqian Zhong and co-authors, converted from safetensors to GGUF q8_0 with llama.cpp's `convert_lora_to_gguf.py`. No other modification | Apache-2.0 | [YixuanEvenXu/Qwen3-4B-Base-HIP-adapter](https://huggingface.co/YixuanEvenXu/Qwen3-4B-Base-HIP-adapter) · [conversion published here](https://github.com/ervin-mo/humanizar-es/releases/tag/modelo-hip) |

The HIP method and training code (MIT) belong to their authors:
[github.com/YixuanEvenXu/humanization-by-iterative-paraphrasing](https://github.com/YixuanEvenXu/humanization-by-iterative-paraphrasing).
Paper: Xu et al., 2026, *Base Models Look Human To AI Detectors*,
[arXiv:2605.19516](https://arxiv.org/abs/2605.19516).

`rewrite.py` runs the models with [llama.cpp](https://github.com/ggml-org/llama.cpp) (MIT),
which you install yourself.
