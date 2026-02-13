# Add OpenRouter Free LLMs to Cursor Agent

Cursor doesn't natively list OpenRouter. Use this workaround to get OpenRouter free models into the agent model dropdown (alongside Composer 1.5, Claude, etc.).

## Method: Override OpenAI base URL

Cursor uses an OpenAI-compatible API. OpenRouter exposes `https://openrouter.ai/api/v1`, which is compatible.

### Steps

1. **Open Cursor Settings**
   - `File` → `Preferences` → `Cursor Settings` (or `Ctrl+,` → search "Cursor")

2. **Go to Models**
   - Open **Models** in the left sidebar

3. **Configure OpenAI override**
   - Find the **OpenAI** (or "OpenAI API") section
   - Enable **Override OpenAI Base URL**
   - Set **Base URL** to: `https://openrouter.ai/api/v1`
   - Set **API Key** to your OpenRouter API key (get one at [openrouter.ai/keys](https://openrouter.ai/keys))

4. **Add custom models**
   - In Models, click **Add model** (or equivalent) to add models manually
   - For each model, use the OpenRouter model ID as the model name

### OpenRouter free model IDs (paste into Cursor)

| Display name        | Model ID (use this in Cursor)      |
|---------------------|------------------------------------|
| DeepSeek R1 T2 Chimera | `tngtech/deepseek-r1t2-chimera:free` |
| Arcee Trinity Large | `arcee-ai/trinity-large-preview:free` |
| StepFun Step 3.5 Flash | `stepfun/step-3.5-flash:free` |
| DeepSeek R1 0528    | `deepseek/deepseek-r1-0528:free` |
| Meta Llama 3.3 70B  | `meta-llama/llama-3.3-70b-instruct:free` |
| Z.ai GLM 4.5 Air    | `z-ai/glm-4.5-air:free` |
| TNG R1T Chimera     | `tngtech/deepseek-r1t-chimera:free` |
| OpenRouter Aurora Alpha | `openrouter/aurora-alpha` |
| NVIDIA Nemotron 3 Nano 30B | `nvidia/nemotron-3-nano-30b-a3b:free` |
| Upstage Solar Pro 3 | `upstage/solar-pro-3:free` |
| Qwen3 Coder 480B    | `qwen/qwen3-coder:free` |
| Arcee Trinity Mini  | `arcee-ai/trinity-mini:free` |
| OpenAI gpt-oss-120b | `openai/gpt-oss-120b:free` |

### Caveats

- You may need to **disable** built-in Cursor models that aren't available via OpenRouter, or Cursor may fall back incorrectly
- Some users report that overriding the base URL can break other models; test and toggle off if needed
- Free models have rate limits and can be slower than paid Cursor models

### Alternative: Local proxy

If the direct override causes issues, run a local proxy (e.g. [cursor-openrouter-proxy](https://github.com/pezzos/cursor-openrouter-proxy)) and point Cursor's base URL to `http://localhost:9000/v1` instead.

---

*Last updated: 2026-02*
