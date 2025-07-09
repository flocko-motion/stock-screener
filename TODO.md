Next steps:

Working on Plugins. Implementing a first prototype Plugin "Industry()".

Clarify: how are generated fields stored? Are they part of the basket? Or are they transient pipeline data? Rather the latter... 

Idea: Have some archetypal Plugin superclasses derived from the base class: FilterPlugin, FieldPlugin, IndicatorPlugin, OutputPlugin. This 
could simplify implementation.

Goals:
- get Industry plugin running, implement basic plugin execution: Basket(..)(PluginA() >> (FilterPluginB() < threshold) >> PlotterPluginC())
- build a simple plotter
- build a simple filter


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
