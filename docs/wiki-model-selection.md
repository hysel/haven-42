# Choose a Model

_For Haven 42 users. Model availability depends on the Ollama server you connect._

Haven 42 can recommend an installed model, but it never changes models or
downloads one without your involvement.

## Choose an installed model

1. Connect Haven 42 to your Ollama server.
2. Open **Models**.
3. Choose what you want the model to do, such as conversation or writing.
4. Review the installed models shown for that task.
5. Keep **Automatic** or deliberately select another installed model.

**Automatic** uses committed compatibility evidence when the model name,
immutable digest, and capability all match. Other installed models remain
available as advanced choices and are labeled when Haven 42 has not verified
them for the selected task.

## Find a model that is not installed

Use **Search public catalog** when you deliberately want online discovery.
Results identify which models are already installed locally. Changing the
**Configure model for** selection clears the old results and searches for
choices relevant to the new task.

Catalog search does not install or run anything. Haven 42 may display an Ollama
pull instruction, but you must review and run that instruction yourself in the
Ollama environment you manage. Reconnect after installation to refresh the
installed-model list.

## Choosing well

- Start with the recommended installed model.
- Prefer a smaller model when responsiveness matters more than maximum depth.
- Use larger models only when the provider has enough memory and performance.
- Treat an unverified model as an experiment, especially for long documents,
  structured output, or tool-oriented work.
- Compare provider-reported token counts and timing in **Run details**.

Haven 42 never hides an installed model merely because it is not recommended.
The recommendation is guidance, not a restriction.

## More detail

- [[Using Haven 42|Using-Haven-42]]
- [[Online Model Discovery|Online-Model-Discovery]]
- [[Hardware-Aware Recommendations|Hardware-Aware-Recommendations]]
- [[Engineering Model Selection|Engineering-Model-Selection]]
