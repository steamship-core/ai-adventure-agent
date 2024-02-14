# AI ADVENTURE -- Server-side Agent  ✨✨

This project contains the server-side Dungeon Master for Steamship's [AI Adventure Game (Web Project Link)](https://github.com/steamship-core/ai-adventure).

This is an experiment: we're building a full game engine out of AI Agents. It has:

- 🪄 Everything generated on the fly: story, images, & music
- 🎭 Swappable generative models

In the accompanying [web interface](https://github.com/steamship-core/ai-adventure), we have:

- 📱 Mobile-first layout
- 💰 Payment-ready
- 🚀 Sharing-ready -- share generated adventure storybooks on Twitter

We're working actively on making this extensible enough for anyone to create their own amazing quest.

Email us!  support [at] steamship [dot] com.

## You might not need this Repository

You can run the whole game without modifying this project using the Agent that we've already deployed.

[Instructions for that are here.](https://github.com/steamship-core/ai-adventure)

This repository is where you should be if you want to modify the core logic of the Dungeon Master.

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

## Testing

Run:

```bash
ship run local
```

## Deployment

Run:

```bash
ship deploy
```

And select a name for your package the first time. This name should be **all lowercase plus dashes**.

## Connecting to the Web UI

In your NextJS project, Change the `STEAMSHIP_AGENT_VERSION` environment variable in this Vercel project to match your own game engine's handle.
If you want to pin it to a specific version, use `handle@version` format.




