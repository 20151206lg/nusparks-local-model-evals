# Prompts

`G.txt` (Godot track) and `P.txt` (Python/Panda3D track) are the exact prompts we gave the agents, with three project-specific document names replaced by placeholders:

- `GODOT_HANDOFF_DOC`: a document describing the Godot game task (rules, controls, acceptance expectations);
- `AGENT_NOTES`: the project's agent-instructions file;
- `PYTHON_CHALLENGE_DOC`: the Python-track assignment document.

`bin/run_cell.sh` fills them from environment variables of the same names and refuses to start if one is empty. The Python prompt asks for all three milestones in one go.
