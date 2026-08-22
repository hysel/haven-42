# Common Words

Haven 42 explains unfamiliar words where you first see them. This page is a
quick reference if you want a little more detail.

| Word | What it means |
|---|---|
| AI model | The set of files that reads your request and creates a response. Different models have different strengths and computer requirements. |
| Ollama | The local AI engine Haven 42 uses to load a text model and run it on your computer or another computer you trust. |
| AI server | A computer running Ollama. It can be this computer or another computer on your private network. |
| Token | A small piece of text processed by the model. Token totals and tokens per second help describe response length and speed. |
| Local | Running on your computer, without sending the request to a public cloud AI service. |
| Portable package | A folder you extract and run without a traditional installer. Haven 42 keeps its managed files inside that folder. |
| Guided setup | The recommended setup that checks the computer, explains required downloads, asks permission, and chooses a suitable model. |
| Advanced | An optional choice intended for people who already manage an AI server or need technical controls. |
| Loopback | A private connection that stays on the same computer. Haven 42 commonly shows it as `127.0.0.1`. |
| API key | A secret used to authenticate to an AI server. Haven 42 keeps a supplied key in memory for the current session and requires HTTPS when the server is on another computer. Never put a key in a public issue. |
| CPU | The computer's general-purpose processor. A model can run on a CPU when compatible graphics acceleration is unavailable, usually at a lower speed. |
| GPU | A graphics processor that can accelerate a compatible AI model. Available graphics memory limits which model sizes fit. |
| CUDA | NVIDIA's software path for running supported work on an NVIDIA GPU. A CUDA result does not apply to an Intel or AMD graphics card. |
| Runtime | The software that loads and runs a model. Ollama is Haven 42's managed text-model runtime in the current Alpha. |
| Backend or accelerator route | The software path that connects a runtime to hardware, such as CUDA, Vulkan, ROCm/HIP, SYCL, or Metal. A result on one route does not prove another. |
| Quantization | A way to make a model smaller so it can fit on more computers. Haven 42 selects an already prepared size; the Alpha does not modify models on the tester's computer. |
| Quantization label | A model-size label such as `Q4_K_M` or `Q8_0`. It identifies how the model was prepared and affects memory use and output quality. Results for one label do not automatically apply to another. |
| Context window | The amount of prompt, attachment, conversation, and generated text a model can consider in one request. Larger configured context usually needs more memory. |
| Full GPU residency | A test result showing that the required model data fit on the intended GPU during the measured run. It does not by itself prove output quality or long-run stability. |
| Evidence cell | One exact combination of model artifact, runtime, version, operating system, hardware, backend, and task. Changing one of those details creates a separate result. |
| Soak test | A test that runs for a set period to look for failures that may not appear in a short check. |
| Checksum or artifact digest | A fixed-length value used to identify exact file contents. A changed file has a different value. |
| Release candidate | A specific package being considered for release. It still must pass its stated checks before publication. |
| Unsigned package | A development package that has not yet received a publisher signature. Windows may display an extra warning before it runs. |

If a message is still unclear, see [[Troubleshooting|Troubleshooting]].
