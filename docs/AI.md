# Responsibility-aware AI organisation

Core tracking, photos, review, scheduling, and factual reporting work with `AI_PROVIDER=disabled`. The interface shows AI as unconfigured; it never substitutes fabricated photo analysis.

## Local model through Ollama

Install [Ollama](https://ollama.com/) separately and select a vision-capable model supported by your hardware and permitted by its license. Follow the model’s current installation instructions. Confirm that its chat endpoint accepts images before connecting it to company evidence.

Configure `.env`:

```dotenv
AI_PROVIDER=ollama
AI_BASE_URL=http://127.0.0.1:11434
AI_MODEL=YOUR_INSTALLED_VISION_MODEL
AI_EXTERNAL_ENABLED=false
```

Restart the application. Saving tasks, notes or photos automatically queues analysis after a short delay. Open a task to see category, responsibility, priority and related-work suggestions. Confirm selected changes to apply them. Existing tasks have an Analyse work button. Analysis history is under Manage. Failed jobs can be retried. The actual model must already be installed; this application does not download one automatically.

The adapter uses Ollama’s [chat endpoint](https://docs.ollama.com/api/chat) with image content according to its [vision interface](https://docs.ollama.com/capabilities/vision). Requests use a 180-second timeout. AI jobs process one at a time. The dashboard remains independent of the provider request.

## Hardware

No GPU is assumed. Local vision models consume model storage, RAM, and CPU/GPU time. Some may run on CPU with considerable delay; model size, image count, context size, and concurrency change requirements. Use the chosen model’s documented requirements and test a representative photo before deploying it. A practical local vision trial may require substantially more memory than the core application; no universal memory or speed guarantee is made.

## Explicit external provider

An OpenAI-compatible chat-completions provider may be configured explicitly:

```dotenv
AI_PROVIDER=external
AI_EXTERNAL_ENABLED=true
AI_BASE_URL=https://YOUR_APPROVED_PROVIDER/v1
AI_MODEL=YOUR_VISION_MODEL
AI_API_KEY=YOUR_PRIVATE_KEY
```

The base URL must use HTTPS. Setting only `AI_PROVIDER=external` is insufficient; transmission is blocked unless `AI_EXTERNAL_ENABLED=true`. Your department must approve the provider, its data handling, and its costs. Credentials stay in `.env` and are never returned to the browser.

A configured request may transmit the selected task or report snapshot, department responsibility knowledge, team names, up to 30 authorized candidate tasks, member notes, photo captions, and up to eight image thumbnails. Originals are retained on your server. Permission checks occur before queueing and before processing. Newer images added after the request are excluded from that job. Related records whose access has been revoked are excluded at processing time.

## Suggestions and acceptance

- Tasks: title, description, action summary, category, owner and priority suggestions, missing details, observations, assumptions, and next actions.
- Reports: summary wording based on stored source tasks, including blockers, priority work, and repeated-fault context where linked equipment/related records provide it.
- The application keeps provider, model, processing duration, attempt count, source snapshot/version, result, status, and accepted-field history.
- Output is labelled as AI-generated. Original notes remain in history. Members may confirm category and related work. Managers may also confirm priority and assignment to an active account. Title, description and report-summary acceptance remain available in the manager API/history; the model never assigns, approves, closes, deletes, or changes permissions.
- Acceptance fails if the source record has changed. Request a fresh analysis or make a documented manual edit after reviewing the suggestion.
- Uploaded text and images are treated as untrusted source data in the provider instruction. The provider has no tools or direct write access. Photo observations never establish that a repair, backup, restoration, or test succeeded.

## Verification boundary

The automated provider test uses a controlled response to verify the adapter, job lifecycle, separation from source records, permission checks, and explicit acceptance. A real local model and a real external provider were **not** configured or tested. Model accuracy, hardware capacity, response formats, network certificates, costs, and provider-specific limits must be validated before use.

## Background knowledge and minimal navigation

The supplied IT_Department_Responsibilities.xlsx provides 43 job responsibilities and 6 manager reviews. These are background reference data, never instructions or dashboard tabs. Managers maintain them under Manage > Review / edit knowledge. Imports retain original source row numbers and checksum. No tasks or schedules are created from this reference. The older 51 schedule templates remain under Manage > Recurring work for compatibility.

Main navigation: Overview, Work, Reports and Manage. Members: Overview, Work and More. New work starts as Uncategorized; optional fields and filters are collapsed. Related-work analysis considers up to 30 authorized candidates, prioritizing existing links and matching equipment; it is not exhaustive semantic search.

Analysis is debounced eight seconds. New versions supersede outdated suggestions. A configured provider is not proof of a working model connection. No real model is currently connected or tested. Android source includes online suggestion viewing and category confirmation; APK compilation and device checks remain outstanding.
