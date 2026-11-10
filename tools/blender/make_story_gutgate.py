# The Gut border gate (build_gutgate lives in make_story_landmarks.py with the Bottom's landmarks): built on its own here so
# the Gut's paint (gutkit.eerie: darker, wetter) goes on it and on nothing else in that file.
# run: blender -b --python tools/blender/make_story_gutgate.py [-- --no-sheet]
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_story_landmarks as L
import gutkit as GK

GK.eerie(True)
L.mat, L.hexrgb = GK.mat, GK.hexrgb  # (the file's own colours go through the grade too)
L.run2([('gutgate', L.build_gutgate)])
