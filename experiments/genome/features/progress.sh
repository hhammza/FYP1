#!/bin/bash
# Live progress of download_genomes.py and run_amrfinder.py. Ctrl+C to exit;
# the jobs keep running.
#
#     bash experiments/genome/features/progress.sh               # watch + auto-restart
#     bash experiments/genome/features/progress.sh --no-restart  # watch only
#     AMR_JOBS=4 bash experiments/genome/features/progress.sh    # restart with 4 jobs
#
# While it is open it also:
#   * keeps the Mac awake (caffeinate; closing the lid still sleeps it)
#   * restarts run_amrfinder.py when it has stopped and downloaded genomes are
#     still waiting to be searched, at most once every 10 minutes, so genomes
#     that keep failing cannot make it restart in a tight loop

cd "$(dirname "$0")/../../.." || exit 1

AUTO_RESTART=1
[ "$1" = "--no-restart" ] && AUTO_RESTART=0
AMR_JOBS=${AMR_JOBS:-8}
AMR_THREADS=${AMR_THREADS:-1}
COOLDOWN=600          # seconds between automatic restarts
LAST_RESTART=0
RESTARTS=0

# Keep the Mac awake for as long as this script runs (-w: until it exits)
command -v caffeinate >/dev/null && caffeinate -i -s -w $$ &
# Every genome known to the manifest or on the lab list (select_lab_genomes.py)
TOTAL=$(cut -d, -f1 Data/genomes_full/manifest.csv experiments/genome/features/lab_genomes.csv 2>/dev/null \
        | grep -v '^genome_id$' | sort -u | wc -l | tr -d ' ')
START=$(date +%s)
# count with ls | grep, not a glob: 20,000+ file names overflow the argument list
count() { ls "$1" 2>/dev/null | grep -c "$2"; }
D0=$(count Data/genomes_full '\.fna$')
A0=$(count Data/amrfinder_output '\.tsv$')
CORES=$(sysctl -n hw.ncpu 2>/dev/null || nproc)

bar() {  # bar <done> <total>
    local width=40 filled=$(( $1 * 40 / $2 ))
    printf '['; printf '%*s' "$filled" '' | tr ' ' '#'
    printf '%*s' $(( width - filled )) '' | tr ' ' '.'; printf ']'
}

eta() {  # eta <done> <done at start> <total>
    local elapsed=$(( $(date +%s) - START )) gained=$(( $1 - $2 ))
    if [ "$gained" -le 0 ] || [ "$elapsed" -lt 30 ]; then echo 'measuring...'; return; fi
    local left=$(( ($3 - $1) * elapsed / gained ))
    printf '%.1f/min, about %dh %02dm left' "$(echo "$gained * 60 / $elapsed" | bc -l)" \
        $(( left / 3600 )) $(( left % 3600 / 60 ))
}

status() { pgrep -f "$1" >/dev/null && echo running || echo stopped; }

# Cores in use = summed %CPU / 100 of every process whose command line
# matches. For AMRFinderPlus that includes the blast and hmmer programs it
# starts, which live in the amrfinder conda environment.
cores_used() {
    ps -A -o %cpu=,command= | grep -- "$1" | grep -v grep \
        | awk '{s += $1} END {printf "%.1f", s / 100}'
}

# The --jobs and --threads a run was started with
setting() {
    pgrep -fl run_amrfinder.py | grep -v caffeinate | head -1 \
        | awk '{for (i = 1; i <= NF; i++) {if ($i == "--jobs") j = $(i+1); if ($i == "--threads") t = $(i+1)}}
               END {if (j) printf "set to %s jobs x %s threads", j, (t ? t : 2)}'
}

start_amrfinder() {
    nohup caffeinate -i .venv/bin/python -u experiments/genome/features/run_amrfinder.py \
        --jobs "$AMR_JOBS" --threads "$AMR_THREADS" >> Data/amrfinder_output/run.log 2>&1 &
    LAST_RESTART=$(date +%s)
    RESTARTS=$(( RESTARTS + 1 ))
}

restart_note() {
    if [ "$AUTO_RESTART" = 0 ]; then echo "auto-restart: off"; return; fi
    local note="auto-restart: on ($AMR_JOBS jobs x $AMR_THREADS threads)"
    [ "$RESTARTS" -gt 0 ] && note="$note, restarted $RESTARTS time(s), last at $(date -r "$LAST_RESTART" '+%H:%M')"
    echo "$note"
}

while true; do
    D=$(count Data/genomes_full '\.fna$')
    A=$(count Data/amrfinder_output '\.tsv$')
    # Downloaded but not yet searched: restart AMRFinderPlus if it has stopped
    if [ "$AUTO_RESTART" = 1 ] && [ "$D" -gt "$A" ] && ! pgrep -f run_amrfinder.py >/dev/null \
       && [ $(( $(date +%s) - LAST_RESTART )) -ge "$COOLDOWN" ]; then
        start_amrfinder
    fi
    FAILS=$(cat Data/genomes_full/download.log Data/amrfinder_output/run.log 2>/dev/null | grep -c FAILED)
    clear
    echo "Genome features: live progress   $(date '+%H:%M:%S')   (Ctrl+C to exit)"
    echo
    printf 'Download     %s %5d / %d  %3d%%  (%s)\n' "$(bar "$D" "$TOTAL")" "$D" "$TOTAL" $(( D * 100 / TOTAL )) "$(status download_genomes.py)"
    echo "             $(eta "$D" "$D0" "$TOTAL")   disk $(du -sh Data/genomes_full 2>/dev/null | cut -f1)"
    echo "             cores in use: $(cores_used download_genomes) of $CORES (waits on the network, not the CPU)"
    echo
    printf 'AMRFinder    %s %5d / %d  %3d%%  (%s)\n' "$(bar "$A" "$TOTAL")" "$A" "$TOTAL" $(( A * 100 / TOTAL )) "$(status run_amrfinder.py)"
    echo "             $(eta "$A" "$A0" "$TOTAL")"
    echo "             cores in use: $(cores_used amrfinder) of $CORES   $(setting)"
    echo "             $(restart_note)"
    echo
    echo "Failures so far: $FAILS        Mac kept awake while this view is open"
    echo
    echo "Latest download log:"
    tail -3 Data/genomes_full/download.log 2>/dev/null | sed 's/^/  /'
    echo "Latest AMRFinder log:"
    tail -3 Data/amrfinder_output/run.log 2>/dev/null | sed 's/^/  /'
    sleep 5
done
