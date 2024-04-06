# Blender add-on to export animations as Reaper automations

Blender add-on designed to export Blender object animation (location and rotation) to Reaper automation file (.ReaperAutoItem)

## How to use

Set the various parameters of the add-on (description below) and click on "Export Animation To Disk"

The exported .ReaperAutoItem can then be loaded in Reaper by left clicking on the bottom of an automation curve (automation item) and selecting "load".

## Add-on parameters description

Object: the object which position and rotation will be exported

DAW BPM: the bpm value of the Reaper project in which the automation will be imported

Folder: the folder in which will be saved the automation files

Boundary: a rectangle object in the scene that will be used by the add-on during the mapping from blender coordinates to 0-1 automation values. Seen from the top view (numpad 7 in blender), the bottom left of that rectangle will correspond to xy = [0, 0], the top right to xy = [1, 1]. (the boundary allows to define both scale and offset of the mapping)

Project: project name, used as prefix for ReaperAutoItem files naming

## Export folder suggestion

By default, Reaper will search for automation items in a specific location. Saving your .ReaperAutoItem files there will allow you to directly select them from the load drop down menu in Reaper.

- default MacOS path:
~/Library/Application Support/REAPER/AutomationItems on MacOS
