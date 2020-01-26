# -*- coding: utf-8 -*-
"""
lc_circuit_autogen.py

Copyright (c) 2020 @RR_Inyo
Released under the MIT license.
https://opensource.org/licenses/mit-license.php
"""

# ------------------------------
# Preparations
# ------------------------------
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import scipy.interpolate as interp
import subprocess
import ltspice

# Constants, etc.
print('Setting the constants...')

## LTspice XVII path
LTSPICE_PATH = 'C:\Program Files\LTC\LTspiceXVII\XVIIx86.exe'

## Netlist
NETLIST_PATH = 'lc_circuit_autogen.net'
NETLIST_NAME = 'LC Circuit Automatically Generated from Python'
BR = '\r\n'

## Circuit elements
### Series elements
LS_PER_METER = 100e-6
CS_PER_METER = 20e-9
RS_PER_METER = 10e-6

### Parallel elements
GP_PER_METER = 0
CP_PER_METER = 10e-9

### Length and the number of stages
LENGTH = 20
N_STAGES = 100
LINE_TYPE = 'LC-ladder'

### Signal source
SOURCE_TYPE = 'direct'
SOURCE_TEXT = 'V1 1 mid PULSE(0 1 30u 1n 1n 100u 1 1)' + BR\
    + 'V2 mid 0 SINE (0 1 80k 200u 0 0 16)'
V_SOURCE = 1
F_SOURCE = 80e3
T_START_SOURCE = 30e-6
T_END_SOURCE = 100e-6
T_RISE_SOURCE = 1e-9
T_FALL_SOURCE = 1e-9
N_CYCLES_SOURCE = 20
R_SOURCE = 100

### Load
R_LOAD = 300

### Simulation condition
T_SIM = 500e-6

## Plots and animation
FIGSIZE_X = 8
FIGSIZE_Y = 8
N_FRAMES = 1000
INTERVAL = 80
REPEAT_DELAY = 1000
LIM_NEG_V = -1.5
LIM_POS_V = 1.5
LIM_NEG_I = -0.015
LIM_POS_I = 0.015
LINE_WIDTH_BAR = 0.5

# ------------------------------
# Generating the netlist
# ------------------------------
print('Generating the net list for LTspice XVII...')

## Circuit parameters per stages
if LINE_TYPE == 'LC-ladder' or 'CL-ladder':
    LS_PER_STAGE = LS_PER_METER * LENGTH / N_STAGES
    CS_PER_STAGE = CS_PER_METER * LENGTH / N_STAGES
    RS_PER_STAGE = RS_PER_METER * LENGTH / N_STAGES
    GP_PER_STAGE = GP_PER_METER * LENGTH / N_STAGES
    CP_PER_STAGE = CP_PER_METER * LENGTH / N_STAGES
elif LINE_TYPE == 'T-type':
    LS_PER_STAGE = LS_PER_METER * LENGTH / N_STAGES
    CS_PER_STAGE = CS_PER_METER * LENGTH / N_STAGES
    RS_PER_STAGE = RS_PER_METER * LENGTH / N_STAGES
    GP_PER_STAGE = GP_PER_METER * LENGTH / (N_STAGES - 1)
    CP_PER_STAGE = CP_PER_METER * LENGTH / (N_STAGES - 1)
elif LINE_TYPE == 'pi-type':
    LS_PER_STAGE = LS_PER_METER * LENGTH / N_STAGES
    CS_PER_STAGE = CS_PER_METER * LENGTH / N_STAGES
    RS_PER_STAGE = RS_PER_METER * LENGTH / N_STAGES
    GP_PER_STAGE = GP_PER_METER * LENGTH / (N_STAGES + 1)
    CP_PER_STAGE = CP_PER_METER * LENGTH / (N_STAGES + 1)

## Generating a string to contain the netlist
netlist = NETLIST_NAME + BR

## Signal source
if SOURCE_TYPE == 'sine':
    src = f'V1 1 0 SINE(0 {V_SOURCE} {F_SOURCE} {T_START_SOURCE} 0 0 {N_CYCLES_SOURCE})' + BR
elif SOURCE_TYPE == 'pulse':
    src = f'V1 1 0 PULSE(0 {V_SOURCE} {T_START_SOURCE} {T_RISE_SOURCE} {T_FALL_SOURCE} {T_END_SOURCE - T_START_SOURCE} {N_CYCLES_SOURCE})' + BR
elif SOURCE_TYPE == 'direct':
    src = SOURCE_TEXT + BR
else:
    src = ''
    
src += f'RS 1 2 {R_SOURCE}' + BR

netlist += src

## LC network
lc_ntwk = ''
for i in range(N_STAGES):
    ### First stage consideration for parallel elements
    if i == 0 and (LINE_TYPE == 'CL-ladder' or LINE_TYPE == 'pi-type'):
        lc_ntwk += f'C{i} {i + 2} 0 {CP_PER_STAGE}' + BR
        if GP_PER_STAGE != 0:
            lc_ntwk = f'R{i}P {i + 2} 0 {1 / GP_PER_STAGE}' + BR

    ### RL-CS
    if RS_PER_STAGE != 0:
        lc_ntwk += f'R{i + 1} {i + 2} {i + 2}m{i + 3} {RS_PER_STAGE}' + BR
        lc_ntwk += f'L{i + 1} {i + 2}m{i + 3} {i + 3} {LS_PER_STAGE}' + BR
    else:
        lc_ntwk += f'L{i + 1} {i + 2} {i + 3} {LS_PER_STAGE}' + BR
    if CS_PER_STAGE != 0:
        lc_ntwk += f'C{i + 1}S {i + 2} {i + 3} {CS_PER_STAGE}' + BR
    
    ### CG in intermediate nodes
    if i != N_STAGES - 1:
        lc_ntwk += f'C{i + 1} {i + 3} 0 {CP_PER_STAGE}' + BR
        if GP_PER_STAGE != 0:
            lc_ntwk += f'R{i + 1}P {i + 3} 0 {1 / GP_PER_STAGE}' + BR
    
    ### Final stage consideration for parallel elements
    if i == N_STAGES - 1 and (LINE_TYPE == 'LC-ladder' or LINE_TYPE == 'pi-type'):
        lc_ntwk += f'C{i + 1} {i + 3}  0 {CP_PER_STAGE}' + BR
        if GP_PER_STAGE != 0:
            lc_ntwk += f'R{i + 1}P {i + 3}  0 {1 / GP_PER_STAGE}' + BR

netlist += lc_ntwk

### Load
load = f'RL {N_STAGES + 2} 0 {R_LOAD}' + BR
netlist += load

### Simulation configuration
cond = f'.tran {T_SIM}' + BR +'.backanno' + BR + '.end'
netlist += cond

# ------------------------------
# Executing LTspice XVII
# ------------------------------

## Writing the netlist to a file
print('Writing the .net file for LTspice XVII...')
file = NETLIST_PATH
with open(file, mode = 'w') as f:
    f.write(netlist)

## Executing LTspice XVII in batch mode
## (Possibly, handling of error is needed.)
print('Running LTspice XVII...')
subprocess.call([LTSPICE_PATH, '-b', file])
print('LTspice XVII simulation successfully completed!')

## Loading the simulation results
print('Loading the resulting .raw file...')
l = ltspice.Ltspice(file.replace('.net', '.raw'))
l.parse()
time = l.getTime()

## Node and branch settings
node = range(N_STAGES + 1)
xt = [n / N_STAGES * LENGTH for n in node]
branch = range(N_STAGES)
xb = [(n + 0.5) / N_STAGES * LENGTH for n in branch]

## Obtaining waveform: Signal source
v_source = l.getData('V(1)')

## Obtaining waveform: Node voltages
vn, vn_interp = [], []
for i in node:
    vn.append(l.getData(f'V({i + 2})'))
    vn_interp.append(interp.interp1d(time, vn[i], kind='linear'))

## Obtaining waveform: Branch currents
ib, ib_interp = [], []
for i in branch:
    ib.append(l.getData(f'I(L{i + 1})'))
    ib_interp.append(interp.interp1d(time, ib[i], kind='linear'))
    
## Plot setting
print('Creating the Figure and Axes objects...')
fig, ax = plt.subplots(3, figsize = (FIGSIZE_X, FIGSIZE_Y))

## Definition of updating function for animation
def update(frame):

    ### Clearing the areas
    ax[0].cla()
    ax[1].cla()
    ax[2].cla()

    ### Simulation time instant
    t = T_SIM / N_FRAMES * frame
    
    ### Title
    # fig.suptitle(f'LC ladder circuit: t = {t}')
       
    ### Plotting: Signal source and output
    ax[0].plot(time, v_source, label = 'Input')
    ax[0].plot(time, vn[-1], label ='Output')
    ax[0].plot([t, t], [LIM_NEG_V, LIM_POS_V], color = 'red', lw = LINE_WIDTH_BAR)
    ax[0].text(T_SIM / 2, LIM_POS_V * 0.9, 'Time-domain input/output voltages', va = 'top', ha = 'center')
    ax[0].set_xlim(0, T_SIM)
    ax[0].set_ylim(LIM_NEG_V, LIM_POS_V)
    ax[0].legend(loc = 'upper right')
    ax[0].grid()
    
    ### Plotting: Node voltages
    v_nodes = []
    for i in node:
        v_nodes.append(vn_interp[i](t))

    ax[1].plot(xt, v_nodes, marker = '.')
    ax[1].text(LENGTH / 2, LIM_POS_V * 0.9, 'Voltage distribution', va = 'top', ha ='center')
    ax[1].set_xlim(0, LENGTH)
    ax[1].set_ylim(LIM_NEG_V, LIM_POS_V)
    ax[1].grid()
    
    ### Plotting: Branch current
    i_branches = []
    for i in branch:
        i_branches.append(ib_interp[i](t))

    ax[2].plot(xb, i_branches, marker = '.')
    ax[2].text(LENGTH / 2, LIM_POS_I * 0.9, 'Current distribution', va = 'top', ha ='center')
    ax[2].set_xlim(0, LENGTH)
    ax[2].set_ylim(LIM_NEG_I, LIM_POS_I)
    ax[2].grid()
    
    print(f'Frame: {frame}/{N_FRAMES}')

# Creating animation
ani = animation.FuncAnimation(fig, update, frames = N_FRAMES, interval = INTERVAL, repeat_delay = REPEAT_DELAY)

print('Saving the animation as an .mp4 file...')
ani.save('lc_wave_autogen.mp4', writer = 'ffmpeg', dpi = 80)