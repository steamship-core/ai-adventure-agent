# AI Adventure Game

## Getting Started

You can be up and running in under a minute.

Clone this repository, then set up a Python virtual environment with:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -r requirements.dev.txt
```

> [!NOTE]
> Requirements you put in `requirements.txt` are what will be run along with the game agent when you deploy.
> The dependencies in `requirements.dev.txt` have been prepopulated with packages you may need while developing on your machine.

## Design Notes


## TODOs

- Narration should just be kicked out to an API. That saves us from having to figure out how to do it
- Interrupt the user mid-quest to ask them to solve their problem
- Asset generation for quests
- Need to have something that announces the TRANSITION
- Need to have something that allows the agent to initiate a conversation.
- Permit the NPC Agent to initiate quest -- it's weird you have to go back to camp

## Next week

- Profiling would be useful to understand if we can shave time