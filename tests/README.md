## Overview

This folder contains mod scripts to generate the path for specific games.

We recommend having them in pairs:
- `game.rpy`, the actual mod that will call the different functions defined in `path.rpy`
- `game.py` to deploy the mod in the proper folder

To help you, an example for [Doki Doki Literature Club](https://store.steampowered.com/app/698780/Doki_Doki_Literature_Club/) is provided.

## Custom script

Creating your own script is quite simple:

1. Create a copy of `ddlc.py` named after your game (`game.py`).
2. Edit the file to adapt the different values.
   - `root` is the path to the base of your game (where the executable is).
   - `executable` is the name of the executable that should be ran.
   - `modfile` is the name of the file that we are going to create afterwards.
3. Create a `game.rpy` file. I recommend just copying the `ddlc.rpy` one.
4. If you know how, edit the file to reflect your needs.
   - If you don't know how, don't worry, the default content should do everything you need

## Why DDLC as example?

- It is a free game
- It is available on multiple plateforms
- It is available on multiple stores
- It is well known
- It contains a variety of elements that challenges the program
  - *Perhaps a bit too much challenge, might even be impossible*