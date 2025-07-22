Next steps:

- Authentication
- Notebook Access via API -> ChatGPT frontend
- Move Postgres to Server








Backlog: 

Ai improvements:
- auto enrich ai_notes using a mini GPT, e.g. adding tags or a summary or condensing the symbol description
- batch upload notes to vector storage

Usability:
- add file reference to Basket, so that a quick .save() can be implemented
- let each Note have a .symbol field
- let notes be able to refer to other note .refer(note-id)
- let notes have shorter id fields, should still be unqiue, though

Plugins:
- Ath() numerical field for ATH
- Price() latest price
- Something is weird with RAGR Plugin: AIT has 0.36 ? Doesn't make sense .. PAA has 0.1 sigma? it's crazy volatile

Allow: AAPL(MohtlyClose() >> Plot())
--> requires a __call__ on BasketItem which creates a basket and hands over to Basket.__call__

Inject Info(<symbol>) into BasketItem somehow..

