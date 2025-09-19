# mcp-endpoint-exploration

A professional-development-day investigation. _(2025-September-15-Monday)_

Goal: to explore the process of setting up a [Model-Context-Protocol (MCP)][mcp] endpoint, using the [BDR-APIs][bdr-apis] as the target data-source.

For context... From a previous professional-development-day [investigation][pre-inv], I learned about MCP. In a nutshell, it's a protocol for how an LLM can use tools to look up information. In that investigation, I learned a bit about how to configure an LLM to access an MCP server, and installed endpoint-tools created by others.

In this investigation, I'd like to understand what's involved in _creating_ one of those MCP tools. I'd like to use the public BDR-APIs as the data-source for the tools. The idea is that one would be able to converse with an LLM, and depending upon what's asked, the LLM would know when (and how) it should query the BDR-MCP-tool -- and that tool would know how to use the BDR-APIs to get data to answer questions.

[mcp]: <https://en.wikipedia.org/wiki/Model_Context_Protocol>
[bdr-apis]: <https://github.com/Brown-University-Library/bdr_api_documentation>
[pre-inv]: <https://github.com/birkin/mcp_agent_tutorial_project>

on this page...
- preparatory research
- setting up ollama
- choosing a model
- confirming model is available via terminal
- mcp-server code

---


## preparatory research

Used chatgpt (gpt-5-thinking, in agent-mode) to investigate how I might use this professional-development-day to achieve the goal outlined above. The [result][gpt-prep].

[gpt-prep]: <https://chatgpt.com/share/68c8166e-8934-8006-bd09-3cbc960a3ddf>

---


## setting up ollama

([Ollama][ollama] is three things at once: a desktop app, a local LLM server/CLI, and a growing ecosystem that makes running open models practical on a laptop.) I'll be using it because there's an ollama-compatible `ollcmp` tool that can be used to "connect" the LLM managed by ollama -- with the MCP-server I'll be configuring with my test mcp-bdr-endpoint.

Checking my version -- I already had it installed, but hadn't used it in a long time...

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

The ollama app-icon showed an update was available, and offered a "Restart to update" menu-option. Selected that.

```bash
% ollama --version
ollama version is 0.11.10
```

[ollama]: <https://ollama.com/>


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


## mcp-server code

Switching gears to the mcp-server code. Based on the initial [chatgptresearch][gpt-prep], I'll be using the python [FastMCP][fastmcp] framework. This offers a simple way to:
- create an MCP server that can advertise tools (and resources/prompts) to an MCP-client.
- execute the tool-calls the LLM proposes and the MCP-client invokes.

[Here's][mcp-server-code] the code I ended up with, after lots of experimentation. I'll say more about this later.


[gpt-prep]: <https://chatgpt.com/share/68c8166e-8934-8006-bd09-3cbc960a3ddf>

[fastmcp]: <https://github.com/jlowin/fastmcp>

[mcp-server-code]: <https://github.com/birkin/mcp_endpoint_exploration/blob/main/a__mcp_server_code.py>

---
---


## the mcp-client

From the research-tutorial, and given my past experience with ollama, I'll use [ollcmp][ollcmp]. From the readme:

_MCP Client for Ollama (ollmcp) is a modern, interactive terminal application (TUI) for connecting local Ollama LLMs to one or more Model Context Protocol (MCP) servers, enabling advanced tool use and workflow automation. With a rich, user-friendly interface, it lets you manage tools, models, and server connections in real time—no coding required. Whether you're building, testing, or just exploring LLM tool use, this client streamlines your workflow with features like fuzzy autocomplete, advanced model configuration, MCP servers hot-reloading for development, and Human-in-the-Loop safety controls._

`ollmcp`, in this PDDay experiment, acts as the "conductor", orchestrating the interaction between the LLM and the MCP-server.

The command I'll run:

```
% ollmcp --servers-json "/path/to/mcp_endpoint_exploration_stuff/mcp_servers.json" --model qwen3:8b
```

What this does:
- Behind the scenes, it reads that json file. An example of that json file is [here][mcp-servers-json].
- Behind the scenes, it runs that `uv` command, pointing to the mcp-server code I wrote referred to above. That starts up the mcp-server.
- `ollmcp` communicates with the `fastmcp` server to discover the tools and resources it offers.
- `ollmcp` loads the `qwen3:8b` LLM.
- `ollmcp` communicates to the LLM the information about the tools available, so the LLM can decide if, when, and how to use them.


## example session

```
% ollmcp --servers-json "/path/to/mcp_endpoint_exploration_stuff/mcp_servers.json" --model qwen3:8b

Found server in config: bdr
Connecting to server: bdr
Successfully connected to bdr with 2 tools

╭─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│                                                           Welcome to the MCP Client for Ollama 🦙                                                           │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭──────────────────────────────────────────────────────────────────── 🔧 Available Tools ─────────────────────────────────────────────────────────────────────╮
│ ✓ bdr.search_bdr                                                            ✓ bdr.get_bdr_item                                                              │
╰───────────────────────────────────────────────────────────────────── 2/2 tools enabled ─────────────────────────────────────────────────────────────────────╯
╭────────────────────────────╮
│ 🧠 Current model: qwen3:8b │
╰────────────────────────────╯
╭────────────────────────────────── Help ───────────────────────────────────╮
│ Available Commands:                                                       │
│                                                                           │
│ Model:                                                                    │
│ • Type model or m to select a model                                       │
│ • Type model-config or mc to configure system prompt and model parameters │
│ • Type thinking-mode or tm to toggle thinking mode                        │
│ • Type show-thinking or st to toggle thinking text visibility             │
│ • Type show-metrics or sm to toggle performance metrics display           │
│                                                                           │
│ MCP Servers and Tools:                                                    │
│ • Type tools or t to configure tools                                      │
│ • Type show-tool-execution or ste to toggle tool execution display        │
│ • Type human-in-the-loop or hil to toggle Human-in-the-Loop confirmations │
│ • Type reload-servers or rs to reload MCP servers                         │
│                                                                           │
│ Context:                                                                  │
│ • Type context or c to toggle context retention                           │
│ • Type clear or cc to clear conversation context                          │
│ • Type context-info or ci to display context info                         │
│                                                                           │
│ Configuration:                                                            │
│ • Type save-config or sc to save the current configuration                │
│ • Type load-config or lc to load a configuration                          │
│ • Type reset-config or rc to reset configuration to defaults              │
│                                                                           │
│ Basic Commands:                                                           │
│ • Type help or h to show this help message                                │
│ • Type clear-screen or cls to clear the terminal screen                   │
│ • Type quit, q, exit, bye, or Ctrl+D to exit the client                   │
│                                                                           │
╰───────────────────────────────────────────────────────────────────────────╯

  qwen3/2-tools❯ 

 qwen3/2-tools❯ does the bdr have anything on abraham lincoln?
```

The terminal then shows the model "thinking":
 
_First, I need to use the search function provided. The function is called bdr.search_bdr, which allows querying the BDR's Solr API. The goal is to find items related to Abraham Lincoln._

_The user might be looking for documents, images, or other materials related to Lincoln. Since the search function can take fielded queries, I should use a specific field to ensure accurate results. The primary_title field is a good choice here. So, the query should be primary_title:"Abraham Lincoln"._
 
_I should also consider including other fields like abstract or ir_collection_name to capture any mentions in those areas. But to start, focusing on the primary title makes sense._
 
_Wait, the function parameters allow for fields to be specified. Maybe including fields like title, abstract, and ir_collection_name could help capture more relevant results. However, the user's main query is about the title, so starting with that is better._
 
_Another thing: the example given in the tool description uses primary_title and rel_is_member_of_collection_ssim. So using primary_title is appropriate here._

_I should structure the query as primary_title:"Abraham Lincoln" to ensure it's a precise match. Also, since the user might want a broad search, maybe using OR with other fields like abstract could help, but the initial search should be focused._

_So, the function call will use the search_bdr function with the query parameter set to "primary_title:"Abraham Lincoln"". That should retrieve items where Abraham Lincoln is the primary title._
 
_I need to make sure that the query is properly formatted as a string, with escaped quotes. The parameters for the function include 'query' as a required field._

_Therefore, the correct tool call is to use bdr.search_bdr with the query "primary_title:"Abraham Lincoln"". This should return the relevant items from the BDR._

And then the terminal shows:

```
╭──────── 🔧 Executing Tool bdr.search_bdr ────────╮
│                                                  │
│  Arguments:                                      │
│                                                  │
│                                                  │
│  {                                               │
│    "query": "primary_title:\"Abraham Lincoln\""  │
│  }                                               │
│                                                  │
╰──────────────────────────────────────────────────╯

🧑‍💻 Human-in-the-Loop Confirmation
Tool to execute: bdr.search_bdr
Arguments:
  • query: primary_title:"Abraham Lincoln"

Options:
  y/yes - Execute the tool call
  n/no - Skip this tool call
  disable - Disable HIL confirmations permanently

What would you like to do? (y): 
```

After typing "y" and pressing enter, the terminal shows:

```
What would you like to do? (y): y
Tip: Use 'human-in-loop' or 'hil' to disable these confirmations

╭────────────────────── ✅ Tool Response bdr.search_bdr ──────────────────────╮
│                                                                             │
│  Arguments:                                                                 │
│                                                                             │
│                                                                             │
│  {                                                                          │
│    "query": "primary_title:\"Abraham Lincoln\""                             │
│  }                                                                          │
│                                                                             │
│  Response:                                                                  │
│                                                                             │
│                                                                             │
│  {                                                                          │
│    "query": "primary_title:\"Abraham Lincoln\"",                            │
│    "request_url": "https://repository.library.brown.edu/api/search/?q=prim  │
│    "num_found": 1067,                                                       │
│    "returned": 10,                                                          │
│    "docs": [                                                                │
│      {                                                                      │
│        "pid": "bdr:70680",                                                  │
│        "title": "Abraham Lincoln -- [bdr:70680]",                           │
│        "abstract": [                                                        │
│          "From 1860 Hesler photograph, Chicago. (From duplicate negative i  │
│        ],                                                                   │
│        "ir_collection_name": [                                              │
│          "Brown University Library",                                        │
│          "Lincoln Graphics"                                                 │
│        ],                                                                   │
│        "_score": null                                                       │
│      },                                                                     │
│      {                                                                      │
│        "pid": "bdr:70921",                                                  │
│        "title": "Abraham Lincoln -- [bdr:70921]",                           │
│        "abstract": [                                                        │
│          "Reproduction of a photograph of Abraham Lincoln (after an 1860 M  │
│        ],                                                                   │
│        "ir_collection_name": [                                              │
│          "Brown University Library",                                        │
│          "Lincoln Graphics"                                                 │
│        ],                                                                   │
│        "_score": null                                                       │
│      },                                                                     │
│      {                                                                      │
│        "pid": "bdr:41675",                                                  │
│        "title": "Abraham Lincoln -- [bdr:41675]",                           │
│        "abstract": [                                                        │
│          "Facsimile of a letter in booklet form from John Hay to William H  │
│        ],                                                                   │
│        "ir_collection_name": [                                              │
│          "Brown University Library",                                        │
│          "Brown Olio"                                                       │
│        ],                                                                   │
│        "_score": null                                                       │
│      },                                                                     │
│      {                                                                      │
│        "pid": "bdr:70295",                                                  │
│        "title": "Abraham Lincoln -- [bdr:70295]",                           │
│        "abstract": [                                                        │
│          "From 1864 photograph (probably by Berger, though previously attr  │
│        ],                                                                   │
│        "ir_collection_name": [                                              │
│          "Brown University Library",                                        │
│          "Lincoln Graphics"                                                 │
│        ],                                                                   │
│        "_score": null                                                       │
│      },                                                                     │
│      {                                                                      │
│        "pid": "bdr:70289",                                                  │
│        "title": "Abraham Lincoln -- [bdr:70289]",                           │
│        "abstract": [                                                        │
│          "Photograph of Bachmann's 1929 Lincoln statue in Minneapolis, Min  │
│        ],                                                                   │
│        "ir_collection_name": [                                              │
│          "Brown University Library",                                        │
│          "Lincoln Graphics"                                                 │
│        ],                                                                   │
│        "_score": null                                                       │
│      },                                                                     │
│      {                                                                      │
│        "pid": "bdr:70670",                                                  │
│        "title": "Abraham Lincoln -- [bdr:70670]",                           │
│        "abstract": [                                                        │
│          "Reproduction of lithograph published by Currier & Ives in 1860 b  │
│        ],                                                                   │
│        "ir_collection_name": [                                              │
│          "Brown University Library",                                        │
│          "Lincoln Graphics"                                                 │
│        ],                                                                   │
│        "_score": null                                                       │
│      },                                                                     │
│      {                                                                      │
│        "pid": "bdr:70365",                                                  │
│        "title": "Abraham Lincoln -- [bdr:70365]",                           │
│        "abstract": [                                                        │
│          "Photoprint of line drawing by Manuel from June 1860 Hesler photo  │
│        ],                                                                   │
│        "ir_collection_name": [                                              │
│          "Brown University Library",                                        │
│          "Lincoln Graphics"                                                 │
│        ],                                                                   │
│        "_score": null                                                       │
│      },                                                                     │
│      {                                                                      │
│        "pid": "bdr:70301",                                                  │
│        "title": "Abraham Lincoln -- [bdr:70301]",                           │
│        "abstract": [                                                        │
│          "Head of Lincoln in marble with beard. From Mid Week Pictorial, J  │
│        ],                                                                   │
│        "ir_collection_name": [                                              │
│          "Brown University Library",                                        │
│          "Lincoln Graphics"                                                 │
│        ],                                                                   │
│        "_score": null                                                       │
│      },                                                                     │
│      {                                                                      │
│        "pid": "bdr:70675",                                                  │
│        "title": "Abraham Lincoln -- [bdr:70675]",                           │
│        "abstract": [                                                        │
│          "By Eaton from Timothy Cole's engraving based on 1863 Gardner pho  │
│        ],                                                                   │
│        "ir_collection_name": [                                              │
│          "Brown University Library",                                        │
│          "Lincoln Graphics"                                                 │
│        ],                                                                   │
│        "_score": null                                                       │
│      },                                                                     │
│      {                                                                      │
│        "pid": "bdr:297123",                                                 │
│        "title": "Abraham Lincoln -- [bdr:297123]",                          │
│        "abstract": null,                                                    │
│        "ir_collection_name": [                                              │
│          "Brown University Library",                                        │
│          "Lincoln Graphics"                                                 │
│        ],                                                                   │
│        "_score": null                                                       │
│      }                                                                      │
│    ],                                                                       │
│    "warnings": [                                                            │
│      "Query returned 1067 hits but only 10 were fetched. Refine the query   │
│    ],                                                                       │
│    "took_ms": 566.87                                                        │
│  }                                                                          │
│                                                                             │
╰─────────────────────────────────────────────────────────────────────────────╯
```

The terminal then shows the model thinking about the results:

```
Looking at the query, it's searching for primary_title "Abraham Lincoln" and   
returning 10 results. The num_found is 1067, which means there are a lot of    
items, but only 10 are shown. The user might want to know if there are         
resources related to Lincoln in the BDR.                                       

The docs section lists each item. Let me go through each entry:                

  1 bdr:70680: A photo from 1860 by Hesler, Chicago. Part of Lincoln Graphics  
    collection. This is a primary source image.                                
  2 bdr:70921: Reproduction of a 1860 Mathew Brady photo. Also in Lincoln      
    Graphics. Another image.                                                   
  3 bdr:41675: Facsimile of a letter from John Hay to Herndon. This is a       
    document related to Lincoln's personal life.                               
  4 bdr:70295: 1864 photograph by Berger (attributed to Brady). Part of a      
    book's frontispiece. Another image.                                        
  5 bdr:70289: 1929 statue by Bachmann in Minneapolis. This is a sculpture, so 
    art-related.                                                               
  6 bdr:70670: Currier & Ives lithograph from 1860. Souvenir from a Lincoln    
    exhibition. Image.                                                         
  7 bdr:70365: Photoprint of a line drawing from Hesler's 1860 photo. Image.   
  8 bdr:70301: Marble head of Lincoln from 1924. Artwork.                      
  9 bdr:70675: Engraving based on Gardner's 1863 photo. Includes text of the   
    Gettysburg Address. This combines image and text.                          
 10 bdr:297123: No abstract provided. Maybe an incomplete entry or another     
    image.                                                                     


So, the BDR has a variety of materials: photographs, lithographs, sculptures,  
facsimiles of letters, and even the Gettysburg Address text. The user might be 
interested in primary sources, historical images, or documents. They might be a
student, researcher, or history enthusiast looking for visual or textual       
materials on Lincoln. The answer should highlight the different types of       
resources available and suggest checking the full collection for more items.   
Also, mention that the query only returned 10 of 1067 results, so refining the 
search or increasing rows could help find more materials. 
```

And then the response:

```
The Brown University Library's Digital Repository (BDR) has a significant      
collection of materials related to Abraham Lincoln, though the search results  
provided only show a sample of 10 out of 1,067 total items. Here's a breakdown 
of the types of resources available:                                           

───────────────────────────────────────────────────────────────────────────────
                             Key Resources Found:                              

 1 Photographs and Portraits:                                                  
    • 1860 Hesler photograph (Chicago Historical Society).                     
    • Reproductions of Mathew Brady's 1860 Lincoln photos.                     
    • 1864 photograph by Berger (attributed to Brady).                         
    • Currier & Ives lithograph (1860) based on Brady's photo.                 
    • Line drawings and photoprints from Hesler's 1860 photo.                  
 2 Art and Sculpture:                                                          
    • Bachmann's 1929 Lincoln statue in Minneapolis (based on Augustus         
      Saint-Gaudens' design).                                                  
    • Marble head of Lincoln (1924).                                           
 3 Documents and Letters:                                                      
    • Facsimile of a letter from John Hay to William Henry Herndon (addressing 
      Lincoln's characteristics).                                              
    • Reproduction of Lincoln's Gettysburg Address text (from a 1922 folder).  
 4 Books and Publications:                                                     
    • Frontispiece of Das Leben Abraham Lincolns (1865), a German biography.   
    • Souvenirs from a 1959 Lincoln Sesquicentennial exhibition.               

───────────────────────────────────────────────────────────────────────────────
                            How to Explore Further:                            

 • Refine the Search: The query only returned 10 of 1,067 results. To find     
   more, you could:                                                            
    • Filter by specific formats (e.g., "letters," "photographs").             
    • Use additional fields like ir_collection_name to focus on collections    
      like "Lincoln Graphics" or "Brown Olio."                                 
    • Increase the rows parameter in the API to fetch more results.            
 • Visit the Repository: Brown University Library Digital Repository for full  
   access.                                                                     

───────────────────────────────────────────────────────────────────────────────
                               Why This Matters:                               

These materials provide primary sources for studying Lincoln's life,           
presidency, and cultural legacy. The photographs, especially, are invaluable   
for historical research, while the facsimile letters and Gettysburg Address    
text offer insights into his personal and political life.                      

Let me know if you'd like help refining the search or exploring specific items!

qwen3/2-tools❯ 
```

---


[mcp_servers.json]: <https://github.com/birkin/mcp_endpoint_exploration/blob/main/b__mcp_servers.json>

[ollcmp]: <https://github.com/jonigl/mcp-client-for-ollama>
