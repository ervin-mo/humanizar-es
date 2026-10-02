# Software y modelos de terceros

El código de este repositorio es MIT (ver `LICENSE`). `scripts/instalar_hip.py` descarga,
aparte, dos archivos de terceros. No están dentro del repo.

| Archivo | Qué es | Licencia | Origen |
|---|---|---|---|
| `Qwen3-4B-Base.Q8_0.gguf` | El modelo base Qwen3-4B-Base de Alibaba (equipo Qwen), cuantizado a GGUF Q8_0 por mradermacher | Apache-2.0 | [Qwen/Qwen3-4B-Base](https://huggingface.co/Qwen/Qwen3-4B-Base) · [GGUF](https://huggingface.co/mradermacher/Qwen3-4B-Base-GGUF) |
| `hip-qwen3-4b-base.gguf` | El adaptador LoRA de HIP (*Humanization by Iterative Paraphrasing*) de Yixuan Even Xu, Ziqian Zhong y coautores, convertido de safetensors a GGUF q8_0 con `convert_lora_to_gguf.py` de llama.cpp. Sin otra modificación | Apache-2.0 | [YixuanEvenXu/Qwen3-4B-Base-HIP-adapter](https://huggingface.co/YixuanEvenXu/Qwen3-4B-Base-HIP-adapter) · [conversión publicada aquí](https://github.com/ervin-mo/humanizar-es/releases/tag/modelo-hip) |

El método y el código de entrenamiento de HIP (MIT) son de sus autores:
[github.com/YixuanEvenXu/humanization-by-iterative-paraphrasing](https://github.com/YixuanEvenXu/humanization-by-iterative-paraphrasing).
Artículo: Xu et al., 2026, *Base Models Look Human To AI Detectors*,
[arXiv:2605.19516](https://arxiv.org/abs/2605.19516).

`hip.py` corre los modelos con [llama.cpp](https://github.com/ggml-org/llama.cpp) (MIT),
que instalas tú.
