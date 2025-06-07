import os
import sys

# Add paths to the modules
sys.path.insert(1, '/home/raul/project-vit/codes/pre-detect')
sys.path.insert(1, '/home/raul/project-vit/codes/detect')

from injection_final import inject_signal_into_real_data
from make_framecache_final import generate_framecache
from make_SFT_function import run_make_sfts_script
from algortihm_final import load_sfts, preprocess_data, apply_notches_on_cshuster, run_viterbi, run_fit_on_viterbi_track

# -------------------- PARAMETERS --------------------
m1 = 1.2e-2
m2 = 1.2e-2
distance = 0.005
ifo = 'H1'
t_start = 1250070528
frame_length = 4096
num_frames = 8
coal_time = t_start + 33000

input_dir = "/home/raul/project-vit/O3-data/H1-sampling_512"
channel_name = 'DCS-CALIB_STRAIN_C01'

# -------------------- 1. INJECT SIGNAL --------------------
print('------------ Starting to inject the signal in the O3 data ------------')
inject_signal_into_real_data(
    m1, m2, distance,
    ra=1.7, dec=1.7, pol=0.2, inc=0,
    ifo=ifo, t_start=t_start, num_frames=num_frames, frame_length=frame_length,
    input_dir=input_dir, channel_name=channel_name
)
print('------------ Finishing injection of the O3 data ------------')

# -------------------- 2. GENERATE FRAMECACHE --------------------
output_injected_dir = input_dir.replace("sampling_512", f"{ifo}-injected-mchirp_1e-02-dl-0_005")
framecache_path = generate_framecache(
    input_dir=output_injected_dir,
    distance=distance,
    det=ifo[0],
    num_frames=num_frames,
    frame_length=frame_length,
    t_start=t_start,
    coal_time=coal_time
)

# -------------------- 3. GENERATE SFTs --------------------
sft_output_path = "/home/raul/project-vit/O3-data/sft-8-injected-mchirp_10e-2-dl-0005"
bash_script_path = "/ruta/a/tu/make_sfts_parallel.sh"
t_end = t_start + frame_length * num_frames

run_make_sfts_script(
    bash_script_path=bash_script_path,
    t_start=t_start,
    t_end=t_end,
    sft_output_path=sft_output_path,
    framecache_path=framecache_path
)

# -------------------- 4. RUN VITERBI DETECTION --------------------
nbins = 1024
fmin = 61
fmax = 128
N0 = int(fmin / 8)
Nmax = int(fmax / 8)
notches = [(101, 1)]

nsft = num_frames
sftdirH1 = sft_output_path
dataH1 = load_sfts(sftdirH1, t_start, 8, nbins, nsft)
CShusterH1, freqs_filtered = preprocess_data(dataH1, 8, fmin, fmax)
CShusterH1 = apply_notches_on_cshuster(CShusterH1, freqs_filtered, notches)
track_freqs, _ = run_viterbi(CShusterH1, freqs_filtered, 8, fmin, fmax)

# -------------------- 5. FIT DETECTION --------------------
path_txt = "vit-track-dl-0005-notch-filtered.txt"
run_fit_on_viterbi_track(path_txt)

print("Pipeline completed successfully.")
