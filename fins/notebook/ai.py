"""
OpenAI Assistant Integration for Notebook

This module provides integration with OpenAI's Assistant API to create an AI assistant
that can access and analyze all notes in the notebook system.
"""

from io import BytesIO
from openai import OpenAI
from openai.types import VectorStoreSearchResponse

from openai.types.beta.assistant import ToolResources, ToolResourcesFileSearch
from openai.types.responses import ResponseTextDeltaEvent, WebSearchToolParam, FileSearchToolParam, \
    ResponseFileSearchToolCall, ResponseOutputMessage
from openai.types.responses.file_search_tool_param import RankingOptions

from fins.config import get_openai_api_key, get_assistant_config, set_assistant_config
from fins.entities import Note
from fins.notebook import notebook, Notebook

instructions = """
### 🧠 **FINS Assistant Instructions**

**Purpose**:
You are a structured, non-fluffy assistant for a high-conviction long-term investor.
You support a systematic, data-driven investment framework (FINS - Financial Intelligence and Notetaking System), combining macro regime awareness, quality filters, Bayesian reasoning, and low-noise capital allocation.

---

### 🎯 **Core Functions**

1. **Interpret Notes**

   * Parse atomic notes (facts, insights, trades, theses, etc.)
   * Understand relationships across time, symbols, and themes
   * Highlight contradictions, gaps, reinforcements

2. **Contextual Retrieval**

   * Answer user queries with filtered, thematically grouped notes
   * Prioritize relevance over recency
   * Use metadata (tags, type, symbol, macro regime) to guide retrieval

3. **Portfolio Reasoning**

   * Support asset scoring across filters (quality, volatility, growth, liquidity-sensitivity)
   * Help rank and assemble long-term portfolios (winter/summer regimes)
   * Suggest capital rotation ideas when constraints are triggered (e.g. no cash)

4. **Macro Mapping**

   * Reason about macro seasons using time-lagged liquidity, inflation, CB action, positioning
   * Summarize trends in user's thinking (via note time series)
   * Use Bayesian framing: update priors, suggest posterior adjustments
   * Consider the theoretical insights of 
     - Julian Bittel (macro liquidity cycles, positioning, forward signals),
     - Lyn Alden (multi-layer macro reasoning, valuation, fiscal-monetary dynamics),
     - Raoul Pal (liquidity regimes, crypto cycles, narrative rotation),
     - Ray Dalio (debt cycles and system dynamics),
     - Michael Howell (global liquidity architecture), and
     - Hugh Hendry (contrarian macro reasoning, nonlinear thinking, regime awareness).

---

### 🧱 **Constraints**

* Never recommend trades; only reason from the user’s framework
* Use clear, analytical language — no hype, no sentiment
* Be brief unless asked for detail
* Only answer from user's data and structured notes — do not hallucinate

---

### 🔧 Style

* Talk to the user like a trusted analyst with deep context
* Mirror their precision, speed, and curiosity
* Respect their intelligence — no simplifications, no lectures
"""



class NotebookAi:
    """
    OpenAI Assistant integration for the FINS notebook system.

    Manages assistant creation, file uploads, and state persistence.
    Uses file search approach with comprehensive file uploads.
    """

    model = "gpt-4o"


    def __init__(self):
        """
        Initialize the gpt-powered notebook assistant.
        """

        # connect to openAI
        self.api_key = get_openai_api_key()
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set it in assistant.yaml config file.")
        self.client = OpenAI(api_key=self.api_key)

        # init vector store
        vector_store_id = get_assistant_config("vector_store" + ("_test" if Notebook.is_test_mode() else ""))
        if vector_store_id:
            self._vector_store = self.client.vector_stores.retrieve(vector_store_id)
        else:
            self._vector_store = self.client.vector_stores.create(name="FINS Notes")
            set_assistant_config("vector_store", self._vector_store.id)

        self._response_id = None

    def ask(self, message: str) -> None:
        print(f"user> {message}")

        if self._response_id is None:
            response_params = {"instructions": instructions}
        else:
            response_params = {"previous_response_id": self._response_id}

        mode_stream = True
        res = self.client.responses.create(
            model= self.model,
            input=message,
            stream=mode_stream,
            tools=[
                WebSearchToolParam(type="web_search_preview", search_context_size="medium"),
                FileSearchToolParam(
                    type="file_search",
                    vector_store_ids=[self._vector_store.id, ],
                    max_num_results=50,
                    ranking_options=RankingOptions(
                        ranker="auto",
                        score_threshold=0.5,
                    )
                ),
            ],
            include=["file_search_call.results"],
            **response_params
        )

        if mode_stream:
            response = None
            print(f"fins> ", end="", flush=True)
            for event in res:
                if response is None:
                    response = event.response
                    self._response_id = response.id
                if isinstance(event, ResponseTextDeltaEvent):
                    print(event.delta, end="", flush=True)
            return
        else:
            self._response_id = res.id
            for output in res.output:
                if isinstance(output, ResponseFileSearchToolCall):
                    for result in output.results:
                        print(f"related note! file: {result.filename}, score: {result.score}, text: {result.text}")
                    continue
                if isinstance(output, ResponseOutputMessage):
                    for result in output.content:
                        print(result.text)
                    continue




    def sync_notes(self, force: bool = False):
        """
        Sync all notes to the assistant using file search approach.
        This should be done at startup.

        Args:
            force: If True, re-upload all notes even if already uploaded
        """
        print("Sync notes..")
        notes = notebook().list_notes(limit=10000)
        vs_file_ids_local = set()
        for note in notes:
            if note.vector_store_file_id is None:
                res = self.client.vector_stores.files.upload(vector_store_id=self._vector_store.id, file=(note.id + ".json", BytesIO(note.to_ai_note())))
                note.vector_store_file_id = res.id
                vs_file_ids_local.add(res.id)

        vs_files = self.client.vector_stores.files.list(vector_store_id=self._vector_store.id)
        vs_file_ids_online = set([d.id for d in vs_files.data])

        vs_file_ids_delete = vs_file_ids_online - vs_file_ids_local
        vs_file_ids_attach = vs_file_ids_local - vs_file_ids_local

        for vs_file_id in vs_file_ids_delete:
            res = self.client.vector_stores.files.delete(vector_store_id=self._vector_store.id, file_id=vs_file_id)
            if res.deleted:
                print(f"✓ Deleted Note {vs_file_id}")
        for vs_file_id in vs_file_ids_attach:
            res = self.client.vector_stores.files.create(vector_store_id=self._vector_store.id, file_id=vs_file_id)

        print("✓ Notes are now available for file search")

    def sync_note(self, note: Note):
        """ sync a single to vector storage - this will modify the vector store file id! save not to db after this action"""
        if note.vector_store_file_id is not None:
            res = self.client.vector_stores.files.delete(vector_store_id=self._vector_store.id, file_id=note.vector_store_file_id)
            if res.deleted:
                print(f"✓ Deleted old version of Note from vector store")

        res = self.client.vector_stores.files.upload(vector_store_id=self._vector_store.id, file=(note.id + ".json", BytesIO(note.to_ai_note())))
        note.vector_store_file_id = res.id
        print(f"✓ Note {note.vector_store_file_id} uploaded to vector store")

    def search(self, query: str):
        """ search the vector store for notes """
        res = self.client.vector_stores.search(self._vector_store.id, query=query)
        print(f"{len(res.data)} notes found")
        for hit in res.data:
            if isinstance(hit, VectorStoreSearchResponse):
                if len(hit.content) != 1:
                    raise ValueError("unexpected content")
                content = hit.content[0].text
                note = Note.from_json(content)
                print(f"Score: {hit.score}\n{note}")
