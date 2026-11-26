"""Afterwards check for the Python rocket run: does Panda3D's built-in default font lay out text in the same install? (Measures the text width; nothing is drawn.) (No window, no GPU.)
Run with the interpreter of the rocket project's virtual environment: <venv>/bin/python accept/p_default_font_check.py"""
from panda3d.core import loadPrcFileData
loadPrcFileData("", "window-type none")
from panda3d.core import TextNode, PandaSystem
t = TextNode("hud")
t.setText("hello")
w = t.getWidth()
print("Panda3D", PandaSystem.getVersionString(), "| TextNode with the default font, text 'hello': width", round(w, 3), "| lays out text:", w > 0)
