"""
=============================================================
  URANIUM ISOTOPES & NUCLEAR FISSION ANIMATION
  For Blender 3.x / 4.x
  
  Science topics covered:
    - 3 natural uranium isotopes with percentages
    - U-235 fissile material and chain reaction
    - U-238 fertile material
    - U-234 trace isotope
    - Fast neutrons → moderation → slow neutrons
    - Neutron absorption → U-236 (unstable)
    - Fission products: Ba-141 + Kr-92 + 3 neutrons + energy
    - Chain reaction visualization

  HOW TO RUN:
    1. Open Blender
    2. Go to the "Scripting" tab (top menu)
    3. Click "New" to create a new script
    4. Paste this entire script
    5. Click "Run Script" (triangle play button)
    6. Press SPACE in the 3D viewport to watch the animation
=============================================================
"""

import bpy
import math
import random

# ─────────────────────────────────────────────
#  SCENE CLEANUP
# ─────────────────────────────────────────────
def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for mat in bpy.data.materials:
        bpy.data.materials.remove(mat)

clear_scene()

# ─────────────────────────────────────────────
#  SCENE SETTINGS
# ─────────────────────────────────────────────
scene = bpy.context.scene
scene.frame_start  = 1
scene.frame_end    = 550
scene.render.fps   = 30

# Dark space background
world = bpy.context.scene.world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.01, 0.01, 0.04, 1.0)
    bg.inputs[1].default_value = 1.0

# ─────────────────────────────────────────────
#  HELPER: CREATE GLOWING SPHERE
# ─────────────────────────────────────────────
def make_sphere(name, loc, radius, color, glow=0.0, metallic=0.3):
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=radius, location=loc, segments=48, ring_count=24
    )
    obj = bpy.context.active_object
    obj.name = name

    mat = bpy.data.materials.new(name + "_mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out  = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value  = (*color, 1.0)
    bsdf.inputs['Metallic'].default_value    = metallic
    bsdf.inputs['Roughness'].default_value   = 0.35

    if glow > 0:
        mix   = nodes.new('ShaderNodeMixShader')
        emit  = nodes.new('ShaderNodeEmission')
        emit.inputs['Color'].default_value    = (*color, 1.0)
        emit.inputs['Strength'].default_value = glow
        links.new(bsdf.outputs['BSDF'],  mix.inputs[1])
        links.new(emit.outputs['Emission'], mix.inputs[2])
        links.new(mix.outputs['Shader'],  out.inputs['Surface'])
    else:
        links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

    obj.data.materials.append(mat)
    return obj


# ─────────────────────────────────────────────
#  HELPER: ADD 3D TEXT LABEL
# ─────────────────────────────────────────────
def make_label(text, loc, size=0.28, color=(1, 1, 1), bold=False):
    bpy.ops.object.text_add(location=loc)
    obj = bpy.context.active_object
    obj.data.body       = text
    obj.data.size       = size
    obj.data.align_x    = 'CENTER'
    obj.data.align_y    = 'CENTER'
    if bold:
        obj.data.body_format[0].use_bold = True

    mat = bpy.data.materials.new(text[:12] + "_lbl")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    out  = nodes.new('ShaderNodeOutputMaterial')
    emit = nodes.new('ShaderNodeEmission')
    emit.inputs['Color'].default_value    = (*color, 1.0)
    emit.inputs['Strength'].default_value = 3.0
    mat.node_tree.links.new(emit.outputs['Emission'], out.inputs['Surface'])
    obj.data.materials.append(mat)
    return obj


# ─────────────────────────────────────────────
#  HELPER: KEYFRAME SHORTCUTS
# ─────────────────────────────────────────────
def kf_loc(obj, frame, loc):
    obj.location = loc
    obj.keyframe_insert('location', frame=frame)

def kf_scale(obj, frame, s):
    sc = s if hasattr(s, '__iter__') else (s, s, s)
    obj.scale = sc
    obj.keyframe_insert('scale', frame=frame)

def kf_hide(obj, frame, hidden):
    obj.hide_viewport = hidden
    obj.hide_render   = hidden
    obj.keyframe_insert('hide_viewport', frame=frame)
    obj.keyframe_insert('hide_render',   frame=frame)

def kf_rot(obj, frame, rot):
    obj.rotation_euler = rot
    obj.keyframe_insert('rotation_euler', frame=frame)

def kf_alpha(obj, frame, alpha):
    for mat in obj.data.materials:
        if mat.use_nodes:
            for node in mat.node_tree.nodes:
                if node.type == 'BSDF_PRINCIPLED':
                    node.inputs['Alpha'].default_value = alpha
                    node.inputs['Alpha'].keyframe_insert('default_value', frame=frame)


# ═══════════════════════════════════════════════════════════════
#  PHASE 1 — THREE URANIUM ISOTOPES  (frames 1 → 110)
#  U-238 (99.27% fertile) | U-235 (0.72% fissile) | U-234 (0.005% trace)
# ═══════════════════════════════════════════════════════════════

# U-238  — large, steel-blue (fertile)
u238 = make_sphere("U238", (-6, 0, 0), 1.8, (0.25, 0.40, 0.70), glow=0.3)
u238_l1 = make_label("U-238",    (-6, 0,  2.6), 0.38, (0.50, 0.75, 1.00))
u238_l2 = make_label("99.27%",   (-6, 0,  2.0), 0.30, (0.50, 0.75, 1.00))
u238_l3 = make_label("Fertile",  (-6, 0,  1.5), 0.26, (0.40, 0.60, 0.90))
u238_l4 = make_label("(Absorbs neutrons\n→ becomes Pu-239)", (-6, 0, -2.4), 0.20, (0.40, 0.60, 0.90))

# U-235  — medium, golden-orange (fissile ★)
u235 = make_sphere("U235", (0, 0, 0), 1.3, (1.00, 0.60, 0.10), glow=1.5)
u235_l1 = make_label("U-235",          (0, 0,  2.2), 0.40, (1.00, 0.85, 0.20))
u235_l2 = make_label("0.72%",          (0, 0,  1.65), 0.30, (1.00, 0.85, 0.20))
u235_l3 = make_label("★ FISSILE ★",   (0, 0,  1.15), 0.28, (1.00, 0.50, 0.10))
u235_l4 = make_label("Splits & releases\nimmense energy!", (0, 0, -2.1), 0.21, (1.00, 0.70, 0.20))

# U-234  — tiny, violet (trace)
u234 = make_sphere("U234", (5, 0, 0), 0.45, (0.60, 0.20, 0.85), glow=0.8)
u234_l1 = make_label("U-234",     (5, 0,  1.1), 0.28, (0.80, 0.45, 1.00))
u234_l2 = make_label("0.005%",    (5, 0,  0.7), 0.22, (0.80, 0.45, 1.00))
u234_l3 = make_label("Trace",     (5, 0,  0.3), 0.20, (0.65, 0.30, 0.85))

# Gentle pulse on U-235 to draw attention
for f in range(1, 111, 22):
    kf_scale(u235, f,      1.0)
    kf_scale(u235, f + 11, 1.12)

# Fade all isotope objects in from scale 0
for obj in [u238, u235, u234]:
    kf_scale(obj, 1,  0.0)
    kf_scale(obj, 30, obj.scale[0])   # restore natural radius ratio

# Hide isotope scene at frame 120 (zoom into U235 for fission)
isotope_objs = [u238, u235, u234,
                u238_l1, u238_l2, u238_l3, u238_l4,
                u234_l1, u234_l2, u234_l3,
                u235_l1, u235_l2, u235_l3, u235_l4]

for obj in isotope_objs:
    kf_hide(obj, 119, False)
    kf_hide(obj, 120, True)


# ═══════════════════════════════════════════════════════════════
#  PHASE 2 — FAST NEUTRON FIRED  (frames 120 → 170)
# ═══════════════════════════════════════════════════════════════

# Nucleus (U-235) re-appears centred for fission sequence
nucleus = make_sphere("Nucleus_U235", (0, 0, 0), 1.3, (1.00, 0.60, 0.10), glow=1.5)
nuc_lbl = make_label("U-235 nucleus", (0, 0, 1.9), 0.28, (1.00, 0.80, 0.20))
kf_hide(nucleus, 119, True)
kf_hide(nucleus, 120, False)
kf_hide(nuc_lbl, 119, True)
kf_hide(nuc_lbl, 120, False)

# Phase title
ph2_title = make_label("STEP 1 — Fast Neutron Released", (0, 0, 4.0), 0.32, (0.80, 0.80, 0.80))
kf_hide(ph2_title, 119, True)
kf_hide(ph2_title, 120, False)
kf_hide(ph2_title, 165, False)
kf_hide(ph2_title, 166, True)

# Fast neutron — bright white, comes from far left very quickly
fast_n = make_sphere("FastNeutron", (-14, 0, 0), 0.22, (1.0, 1.0, 0.9), glow=6.0)
fast_n_lbl = make_label("Fast Neutron\n(high energy)", (-10, 0, 0.7), 0.22, (0.9, 0.9, 1.0))

kf_hide(fast_n,     119, True)
kf_hide(fast_n,     120, False)
kf_hide(fast_n_lbl, 119, True)
kf_hide(fast_n_lbl, 120, False)

# Fast — covers 11 units in 20 frames
kf_loc(fast_n, 120, (-14, 0, 0))
kf_loc(fast_n, 140, (-3,  0, 0))   # stops just before moderator
kf_loc(fast_n_lbl, 120, (-10, 0, 0.7))
kf_loc(fast_n_lbl, 140, (-3,  0, 0.7))

kf_hide(fast_n,     159, False)
kf_hide(fast_n,     160, True)
kf_hide(fast_n_lbl, 159, False)
kf_hide(fast_n_lbl, 160, True)


# ═══════════════════════════════════════════════════════════════
#  PHASE 3 — MODERATOR SLOWS NEUTRON  (frames 160 → 230)
# ═══════════════════════════════════════════════════════════════

ph3_title = make_label("STEP 2 — Moderator Slows the Neutron", (0, 0, 4.0), 0.32, (0.80, 0.80, 0.80))
kf_hide(ph3_title, 159, True)
kf_hide(ph3_title, 160, False)
kf_hide(ph3_title, 229, False)
kf_hide(ph3_title, 230, True)

# Moderator block — translucent cyan (water or graphite)
bpy.ops.mesh.primitive_cube_add(size=1, location=(-2, 0, 0))
mod_block = bpy.context.active_object
mod_block.name = "Moderator"
mod_block.scale = (2.0, 1.5, 1.5)
kf_hide(mod_block, 159, True)
kf_hide(mod_block, 160, False)

mod_mat = bpy.data.materials.new("Mod_mat")
mod_mat.use_nodes = True
nodes = mod_mat.node_tree.nodes
links = mod_mat.node_tree.links
nodes.clear()
out_m  = nodes.new('ShaderNodeOutputMaterial')
bsdf_m = nodes.new('ShaderNodeBsdfPrincipled')
bsdf_m.inputs['Base Color'].default_value  = (0.10, 0.55, 0.90, 1.0)
bsdf_m.inputs['Alpha'].default_value       = 0.30
bsdf_m.inputs['Roughness'].default_value   = 0.05
mod_mat.blend_method = 'BLEND'
links.new(bsdf_m.outputs['BSDF'], out_m.inputs['Surface'])
mod_block.data.materials.append(mod_mat)

mod_lbl = make_label("Moderator\n(Water / Graphite)", (-2, 0, -2.5), 0.24, (0.30, 0.75, 1.00))
kf_hide(mod_lbl, 159, True)
kf_hide(mod_lbl, 160, False)

# Slow neutron — same sphere reused, now orange (lower energy colour)
slow_n = make_sphere("SlowNeutron", (-4, 0, 0), 0.22, (1.0, 0.55, 0.10), glow=3.0)
slow_n_lbl = make_label("Slow Neutron\n(thermal)", (-4, 0, 0.7), 0.22, (1.0, 0.70, 0.20))
kf_hide(slow_n,     159, True)
kf_hide(slow_n,     160, False)
kf_hide(slow_n_lbl, 159, True)
kf_hide(slow_n_lbl, 160, False)

# Slow — covers 4 units in 60 frames (much slower!)
kf_loc(slow_n, 160, (-4, 0, 0))
kf_loc(slow_n, 220, ( 0, 0, 0))   # reaches nucleus
kf_loc(slow_n_lbl, 160, (-4, 0, 0.7))
kf_loc(slow_n_lbl, 220, ( 0, 0, 0.7))

kf_hide(slow_n,     224, False)
kf_hide(slow_n,     225, True)
kf_hide(slow_n_lbl, 224, False)
kf_hide(slow_n_lbl, 225, True)


# ═══════════════════════════════════════════════════════════════
#  PHASE 4 — NEUTRON ABSORBED → U-236 UNSTABLE  (230 → 290)
# ═══════════════════════════════════════════════════════════════

ph4_title = make_label("STEP 3 — Neutron Absorbed → U-236 (Unstable!)", (0, 0, 4.0), 0.28, (0.80, 0.80, 0.80))
kf_hide(ph4_title, 229, True)
kf_hide(ph4_title, 230, False)
kf_hide(ph4_title, 289, False)
kf_hide(ph4_title, 290, True)

# Nucleus swells to represent U-236
kf_scale(nucleus, 225, 1.0)
kf_scale(nucleus, 245, 1.35)   # absorbs neutron — grows

# Hide moderator
kf_hide(mod_block, 229, False)
kf_hide(mod_block, 230, True)
kf_hide(mod_lbl,   229, False)
kf_hide(mod_lbl,   230, True)

# Swap label to U-236
kf_hide(nuc_lbl, 229, False)
kf_hide(nuc_lbl, 230, True)

u236_lbl = make_label("U-236\n(UNSTABLE!)", (0, 0, 2.2), 0.34, (1.0, 0.25, 0.10))
kf_hide(u236_lbl, 229, True)
kf_hide(u236_lbl, 230, False)
kf_hide(u236_lbl, 289, False)
kf_hide(u236_lbl, 290, True)

# Wobble nucleus to show instability — 8 cycles
for i, f in enumerate(range(245, 292, 6)):
    angle = 0.12 * (1 if i % 2 == 0 else -1)
    kf_rot(nucleus, f,   (0,       0,     0))
    kf_rot(nucleus, f+3, (angle, angle/2, 0))

# Change nucleus colour toward red as it becomes unstable
for mat in nucleus.data.materials:
    if mat.use_nodes:
        for nd in mat.node_tree.nodes:
            if nd.type == 'BSDF_PRINCIPLED':
                nd.inputs['Base Color'].default_value = (1.0, 0.60, 0.10, 1.0)
                nd.inputs['Base Color'].keyframe_insert('default_value', frame=230)
                nd.inputs['Base Color'].default_value = (1.0, 0.15, 0.05, 1.0)
                nd.inputs['Base Color'].keyframe_insert('default_value', frame=290)


# ═══════════════════════════════════════════════════════════════
#  PHASE 5 — FISSION REACTION!  (290 → 400)
#  U-236 → Ba-141 + Kr-92 + 3 fast neutrons + γ energy
# ═══════════════════════════════════════════════════════════════

ph5_title = make_label("STEP 4 — FISSION! Nucleus Splits", (0, 0, 4.5), 0.36, (1.0, 0.50, 0.10))
kf_hide(ph5_title, 289, True)
kf_hide(ph5_title, 290, False)
kf_hide(ph5_title, 399, False)
kf_hide(ph5_title, 400, True)

# U-236 nucleus disappears at fission moment
kf_scale(nucleus, 290, (1.35, 1.35, 1.35))
kf_scale(nucleus, 291, (0.0,  0.0,  0.0))
kf_hide(nucleus,  290, False)
kf_hide(nucleus,  291, True)

# ── Fission fragment 1: Barium-141 (larger, red-orange) ──
ba141 = make_sphere("Ba141", (0, 0, 0), 0.90, (0.95, 0.30, 0.10), glow=3.0)
ba141_lbl = make_label("Ba-141\n(Barium)", (3.5, 0, 1.6), 0.26, (1.0, 0.50, 0.20))
kf_hide(ba141,     290, True)
kf_hide(ba141,     291, False)
kf_hide(ba141_lbl, 290, True)
kf_hide(ba141_lbl, 291, False)
kf_loc(ba141, 291, (0, 0, 0))
kf_loc(ba141, 360, (4, 0, 0.5))

# ── Fission fragment 2: Krypton-92 (smaller, green) ──
kr92 = make_sphere("Kr92", (0, 0, 0), 0.65, (0.20, 0.85, 0.30), glow=3.0)
kr92_lbl = make_label("Kr-92\n(Krypton)", (-3.5, 0, 1.6), 0.26, (0.30, 1.0, 0.40))
kf_hide(kr92,     290, True)
kf_hide(kr92,     291, False)
kf_hide(kr92_lbl, 290, True)
kf_hide(kr92_lbl, 291, False)
kf_loc(kr92, 291, (0, 0, 0))
kf_loc(kr92, 360, (-4, 0, -0.5))

# ── 3 new fast neutrons fly out in different directions ──
neutron_dirs = [
    ( 6,  4,  1.0),
    ( 6, -4, -0.5),
    (-6,  5,  0.5),
]
new_neutrons = []
for i, (nx, ny, nz) in enumerate(neutron_dirs):
    nn = make_sphere(f"FreeNeutron_{i}", (0, 0, 0), 0.20, (1.0, 1.0, 0.85), glow=7.0)
    nn_lbl = make_label(f"Fast\nNeutron", (nx*0.55, ny*0.55, nz+0.5), 0.18, (0.9, 0.9, 1.0))
    kf_hide(nn,     290, True)
    kf_hide(nn,     291, False)
    kf_hide(nn_lbl, 290, True)
    kf_hide(nn_lbl, 291, False)
    kf_loc(nn, 291, (0, 0, 0))
    kf_loc(nn, 380, (nx, ny, nz))
    new_neutrons.append(nn)

# ── Energy burst ring ──
bpy.ops.mesh.primitive_torus_add(
    location=(0, 0, 0),
    major_radius=0.3, minor_radius=0.06,
    major_segments=64, minor_segments=16
)
energy_ring = bpy.context.active_object
energy_ring.name = "EnergyRing"
e_mat = bpy.data.materials.new("Energy_mat")
e_mat.use_nodes = True
e_nodes = e_mat.node_tree.nodes
e_nodes.clear()
e_out  = e_nodes.new('ShaderNodeOutputMaterial')
e_emit = e_nodes.new('ShaderNodeEmission')
e_emit.inputs['Color'].default_value    = (1.0, 0.90, 0.20, 1.0)
e_emit.inputs['Strength'].default_value = 12.0
e_mat.node_tree.links.new(e_emit.outputs['Emission'], e_out.inputs['Surface'])
energy_ring.data.materials.append(e_mat)
kf_hide(energy_ring, 290, True)
kf_hide(energy_ring, 291, False)
kf_scale(energy_ring, 291, 0.05)
kf_scale(energy_ring, 340, 10.0)
kf_hide(energy_ring, 340, False)
kf_hide(energy_ring, 341, True)

energy_lbl = make_label("IMMENSE ENERGY\nReleased! (γ rays + heat)", (0, 0, -3.2), 0.35, (1.0, 0.95, 0.10))
kf_hide(energy_lbl, 290, True)
kf_hide(energy_lbl, 295, False)
kf_hide(energy_lbl, 399, False)
kf_hide(energy_lbl, 400, True)


# ═══════════════════════════════════════════════════════════════
#  PHASE 6 — CHAIN REACTION  (400 → 550)
# ═══════════════════════════════════════════════════════════════

ph6_title = make_label("STEP 5 — Chain Reaction Begins!", (0, 0, 5.5), 0.38, (1.0, 0.40, 0.10))
kf_hide(ph6_title, 399, True)
kf_hide(ph6_title, 400, False)

chain_note = make_label("Each fission releases 3 neutrons\n→ each can split another U-235 nucleus\n→ exponential energy release!", (0, 0, -4.5), 0.24, (0.90, 0.90, 0.70))
kf_hide(chain_note, 399, True)
kf_hide(chain_note, 420, False)

# Three secondary nuclei that get hit
secondary_positions = [(6, 4, 1), (6, -4, -0.5), (-6, 5, 0.5)]
for i, (sx, sy, sz) in enumerate(secondary_positions):
    sec_nuc = make_sphere(f"SecNucleus_{i}", (sx, sy, sz), 1.1, (1.0, 0.60, 0.10), glow=1.0)
    sec_lbl = make_label("U-235", (sx, sy, sz + 1.6), 0.22, (1.0, 0.85, 0.20))
    kf_hide(sec_nuc, 399, True)
    kf_hide(sec_nuc, 400, False)
    kf_hide(sec_lbl, 399, True)
    kf_hide(sec_lbl, 400, False)

    # Each secondary nucleus is hit and explodes
    hit_frame = 440 + i * 20
    kf_scale(sec_nuc, hit_frame,     1.0)
    kf_scale(sec_nuc, hit_frame + 5, 1.4)
    kf_scale(sec_nuc, hit_frame + 6, 0.0)
    kf_hide(sec_nuc, hit_frame + 6, True)

    # Mini energy burst for each
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.3, location=(sx, sy, sz))
    mini_burst = bpy.context.active_object
    mini_burst.name = f"MiniBurst_{i}"
    mini_burst.data.materials.append(e_mat)
    kf_hide(mini_burst, hit_frame + 5, True)
    kf_hide(mini_burst, hit_frame + 6, False)
    kf_scale(mini_burst, hit_frame + 6, 0.1)
    kf_scale(mini_burst, hit_frame + 20, 4.0)
    kf_hide(mini_burst, hit_frame + 20, False)
    kf_hide(mini_burst, hit_frame + 21, True)


# ═══════════════════════════════════════════════════════════════
#  BRANDING 1 — REACTOR LAB WALL (background set dressing)
#  "GYRUS SULCUS" engraved/glowing on the back wall
# ═══════════════════════════════════════════════════════════════

# Back wall — dark concrete-style panel
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 10, 0))
back_wall = bpy.context.active_object
back_wall.name = "ReactorWall"
back_wall.scale = (22, 1, 12)
back_wall.rotation_euler = (math.radians(90), 0, 0)

wall_mat = bpy.data.materials.new("WallMat")
wall_mat.use_nodes = True
wn = wall_mat.node_tree.nodes
wl = wall_mat.node_tree.links
wn.clear()
w_out  = wn.new('ShaderNodeOutputMaterial')
w_bsdf = wn.new('ShaderNodeBsdfPrincipled')
w_bsdf.inputs['Base Color'].default_value  = (0.06, 0.07, 0.10, 1.0)
w_bsdf.inputs['Roughness'].default_value   = 0.85
w_bsdf.inputs['Metallic'].default_value    = 0.1
wl.new(w_bsdf.outputs['BSDF'], w_out.inputs['Surface'])
back_wall.data.materials.append(wall_mat)

# Floor panel
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -3))
floor = bpy.context.active_object
floor.name = "ReactorFloor"
floor.scale = (22, 14, 1)
floor.data.materials.append(wall_mat)

# Side wall panels (left & right — subtle)
for sx in [-18, 18]:
    bpy.ops.mesh.primitive_plane_add(size=1, location=(sx, 3, 0))
    sw = bpy.context.active_object
    sw.name = f"SideWall_{sx}"
    sw.scale = (1, 8, 10)
    sw.rotation_euler = (0, math.radians(90), 0)
    sw.data.materials.append(wall_mat)

# Glowing "GYRUS SULCUS" text on the back wall — large, dim, professional
bpy.ops.object.text_add(location=(0, 9.5, 1.5))
wall_brand = bpy.context.active_object
wall_brand.name = "WallBrand"
wall_brand.data.body      = "GYRUS SULCUS"
wall_brand.data.size      = 0.90
wall_brand.data.align_x   = 'CENTER'
wall_brand.data.align_y   = 'CENTER'
wall_brand.data.extrude   = 0.04   # slight 3D depth — engraved look
wall_brand.rotation_euler = (math.radians(90), 0, 0)

wb_mat = bpy.data.materials.new("WallBrand_mat")
wb_mat.use_nodes = True
wbn = wb_mat.node_tree.nodes
wbl = wb_mat.node_tree.links
wbn.clear()
wb_out  = wbn.new('ShaderNodeOutputMaterial')
wb_emit = wbn.new('ShaderNodeEmission')
wb_emit.inputs['Color'].default_value    = (0.35, 0.65, 1.00, 1.0)  # cool blue glow
wb_emit.inputs['Strength'].default_value = 1.2   # dim — non-distracting
wbl.new(wb_emit.outputs['Emission'], wb_out.inputs['Surface'])
wall_brand.data.materials.append(wb_mat)

# Subtle tagline below on wall
bpy.ops.object.text_add(location=(0, 9.4, 0.35))
wall_tag = bpy.context.active_object
wall_tag.name = "WallTagline"
wall_tag.data.body     = "Science Education"
wall_tag.data.size     = 0.28
wall_tag.data.align_x  = 'CENTER'
wall_tag.data.align_y  = 'CENTER'
wall_tag.rotation_euler = (math.radians(90), 0, 0)

wt_mat = bpy.data.materials.new("WallTag_mat")
wt_mat.use_nodes = True
wtn = wt_mat.node_tree.nodes
wtl = wt_mat.node_tree.links
wtn.clear()
wt_out  = wtn.new('ShaderNodeOutputMaterial')
wt_emit = wtn.new('ShaderNodeEmission')
wt_emit.inputs['Color'].default_value    = (0.25, 0.45, 0.75, 1.0)
wt_emit.inputs['Strength'].default_value = 0.8
wtl.new(wt_emit.outputs['Emission'], wt_out.inputs['Surface'])
wall_tag.data.materials.append(wt_mat)

# Decorative reactor warning stripes on floor
for i, fx in enumerate([-8, -4, 0, 4, 8]):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(fx, 4, -2.98))
    stripe = bpy.context.active_object
    stripe.name = f"FloorStripe_{i}"
    stripe.scale = (0.3, 6, 1)
    s_mat = bpy.data.materials.new(f"Stripe_{i}_mat")
    s_mat.use_nodes = True
    sn = s_mat.node_tree.nodes
    sn.clear()
    s_out  = sn.new('ShaderNodeOutputMaterial')
    s_emit = sn.new('ShaderNodeEmission')
    col = (0.9, 0.6, 0.05, 1.0) if i % 2 == 0 else (0.05, 0.05, 0.05, 1.0)
    s_emit.inputs['Color'].default_value    = col
    s_emit.inputs['Strength'].default_value = 0.5
    s_mat.node_tree.links.new(s_emit.outputs['Emission'], s_out.inputs['Surface'])
    stripe.data.materials.append(s_mat)


# ═══════════════════════════════════════════════════════════════
#  BRANDING 2 — ROAMING OVERLAY WATERMARK
#  "GYRUS SULCUS" floats gently across the scene — non-intrusive
# ═══════════════════════════════════════════════════════════════

bpy.ops.object.text_add(location=(-5, -15, -1.5))
watermark = bpy.context.active_object
watermark.name = "Watermark_GS"
watermark.data.body    = "© GYRUS SULCUS"
watermark.data.size    = 0.32
watermark.data.align_x = 'CENTER'

wm_mat = bpy.data.materials.new("Watermark_mat")
wm_mat.use_nodes = True
wmn = wm_mat.node_tree.nodes
wml = wm_mat.node_tree.links
wmn.clear()
wm_out  = wmn.new('ShaderNodeOutputMaterial')
wm_emit = wmn.new('ShaderNodeEmission')
wm_emit.inputs['Color'].default_value    = (0.75, 0.88, 1.00, 1.0)
wm_emit.inputs['Strength'].default_value = 0.6   # very dim — brand not obstruction
wml.new(wm_emit.outputs['Emission'], wm_out.inputs['Surface'])
wm_mat.blend_method = 'BLEND'
watermark.data.materials.append(wm_mat)

# Roaming path — watermark drifts slowly across 4 waypoints across full animation
# Stays in bottom-left corner area, moves gently so it's hard to crop out
watermark_path = [
    (1,   (-5,  -15, -1.5)),   # bottom left
    (140, ( 3,  -15, -1.8)),   # drift right
    (280, ( 4,  -15,  1.0)),   # drift up-right
    (420, (-2,  -15,  1.2)),   # drift left-up
    (550, (-5,  -15, -1.5)),   # return — loops cleanly
]
for frame, loc in watermark_path:
    kf_loc(watermark, frame, loc)

# Make all interpolation smooth (LINEAR → BEZIER already default)
# Slight scale pulse to make it noticeable but not annoying
for frame in range(1, 551, 80):
    kf_scale(watermark, frame,      (1.0, 1.0, 1.0))
    kf_scale(watermark, frame + 40, (1.08, 1.08, 1.08))


# ─────────────────────────────────────────────
#  LIGHTING
# ─────────────────────────────────────────────
bpy.ops.object.light_add(type='POINT', location=( 6, -8, 10))
bpy.context.active_object.data.energy = 1200
bpy.context.active_object.name = "KeyLight"

bpy.ops.object.light_add(type='POINT', location=(-8,  6,  6))
bpy.context.active_object.data.energy = 600
bpy.context.active_object.name = "FillLight"

bpy.ops.object.light_add(type='POINT', location=( 0,  0, -5))
bpy.context.active_object.data.energy = 300
bpy.context.active_object.name = "RimLight"


# ─────────────────────────────────────────────
#  CAMERA
# ─────────────────────────────────────────────
bpy.ops.object.camera_add(location=(0, -22, 4))
cam = bpy.context.active_object
cam.name = "MainCamera"
cam.rotation_euler = (math.radians(80), 0, 0)
cam.data.lens = 40
bpy.context.scene.camera = cam


# ─────────────────────────────────────────────
#  RENDER SETTINGS (YouTube 1080p)
# ─────────────────────────────────────────────
render = scene.render
render.resolution_x   = 1920
render.resolution_y   = 1080
render.fps            = 30
render.image_settings.file_format = 'FFMPEG'
render.ffmpeg.format          = 'MPEG4'
render.ffmpeg.codec           = 'H264'
render.ffmpeg.constant_rate_factor = 'HIGH'
scene.eevee.use_bloom         = True
scene.eevee.bloom_intensity   = 0.5
scene.eevee.use_ssr           = True
render.engine = 'BLENDER_EEVEE'

print("")
print("=" * 55)
print("  NUCLEAR FISSION ANIMATION — SCRIPT COMPLETE!")
print("=" * 55)
print("")
print("  Timeline:")
print("  Frame   1 – 119  → 3 Uranium Isotopes (U-238/235/234)")
print("  Frame 120 – 159  → Fast Neutron fired")
print("  Frame 160 – 229  → Moderator slows neutron")
print("  Frame 230 – 289  → Absorption → U-236 unstable")
print("  Frame 290 – 399  → FISSION! Ba-141 + Kr-92 + 3n + energy")
print("  Frame 400 – 550  → Chain Reaction")
print("")
print("  Branding:
  ✔  GYRUS SULCUS engraved on reactor lab back wall
  ✔  © GYRUS SULCUS roaming watermark (full animation)

  ► Press SPACE in the 3D Viewport to play!")
print("=" * 55)
