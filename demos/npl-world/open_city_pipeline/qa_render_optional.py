#!/usr/bin/env python3
"""Separate optional non-denoising CPU visual audit."""
import bpy
from pathlib import Path
scene=bpy.context.scene
scene.render.engine="BLENDER_WORKBENCH"
scene.display.shading.light="STUDIO"
scene.display.shading.color_type="MATERIAL"
scene.render.resolution_x=900
scene.render.resolution_y=520
scene.render.resolution_percentage=65
scene.render.filepath=str(Path("output/QA_Aerial.png").resolve())
bpy.ops.render.render(write_still=True)
