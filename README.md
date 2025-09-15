# mcp-endpoint-exploration

A professional-development-day investigation. _(2025-September-15-Monday)_

Goal: to explore the process of setting up a [Model-Context-Protocol (MCP)][mcp] endpoint, using the [BDR-APIs][bdr-apis] as the target data-source.

For context... From a previous professional-development-day [investigation][pre-inv], I learned about MCP. In a nutshell, it's a protocol for how an LLM can use tools to look up information. In that investigation, I learned a bit about how to configure an LLM to access an MCP server, and installed endpoint-tools created by others.

In this investigation, I'd like to understand what's involved in _creating_ one of those MCP tools. I'd like to use the public BDR-APIs as the data-source for the tools. The idea is that one would be able to converse with an LLM, and depending upon what's asked, the LLM would know when (and how) it should query the BDR-MCP-tool -- and that tool would know how to use the BDR-APIs to get data to answer questions.

[mcp]: <https://en.wikipedia.org/wiki/Model_Context_Protocol>
[bdr-apis]: <https://github.com/Brown-University-Library/bdr_api_documentation>
[pre-inv]: <https://github.com/birkin/mcp_agent_tutorial_project>

on this page...
- coming...

---


## preparatory research

Used chatgpt (gpt-5-thinking, in agent-mode) to investigate how I might use this professional-development-day to achieve the goal outlined above. The [result][gpt-prep].

[gpt-prep]: <https://chatgpt.com/share/68c8166e-8934-8006-bd09-3cbc960a3ddf>

---


## setting up ollama

Checking my version...

```bash
% ollama --version
Warning: could not connect to a running Ollama instance
Warning: client version is 0.7.0
```

Opened the Mac app (it disappears after a moment, showing the ollama icon in the menu bar).

Trying the version again...

```
% ollama --version
ollama version is 0.7.0
```

The icon shows an update is available, and offers a "Restart to update" menu-option. Selecting that.

```bash
% ollama --version
ollama version is 0.11.10
```


## choosing a model

The Ollama menu-bar icon has an "Open Ollama" menu-option. Selecting that. It opens an interactive chat-window, and shows a listing of models available.

I selected the "qwen3:4b" model. I know from previous experience qwen-3 is a reasoning mode. But I'd used qwen3:7b, and though it was _much_ more impressive than qwen2.5:7b, it was a bit slow -- so I figured I'd try the  qwen3:4b model, to see if it's fast enough for the development phase. (The research doc recommends using qwen2.5:7b for development, then switching over to qwen3 once things are properly hooked up.) I may still do that. Quck benchmarks:
- qwen3:4b query (fresh session): "hi"; it thought for 4 seconds.
- qwen3:4b query: "what's the first line of the gettysburg address?"; it thought for 11 seconds
- those queries on qwen2.5:7b (fresh session) had immediate responses.

So I'll use qwen2.5:7b for initial development.


## confirming model is available via terminal

The docs suggest this:
```
curl -X POST localhost:11434/api/generate -d '{"model":"qwen2.5:7b", "prompt":"", "stream":false}'
```

...but that seems to load the model into memory, not just check to see if it's loaded. From some research, for my reference, some other useful commands:

List installed models (on disk):
```
curl localhost:11434/api/tags | jq
```

List models loaded into memory:
```
curl localhost:11434/api/ps | jq
```


## se
---
---
