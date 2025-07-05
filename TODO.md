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