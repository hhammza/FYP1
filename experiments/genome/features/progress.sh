#!/bin/bash
# Live progress of download_genomes.py and run_amrfinder.py. Ctrl+C to exit;
# the jobs keep running.
#
#     bash experiments/genome/features/progress.sh

cd "$(dirname "$0")/../../.." || exit 1
TOTAL=$(find Data/fasta_output -name '*.fasta' | wc -l | tr -d ' ')
START=$(date +%s)
D0=$(ls Data/genomes_full/*.fna 2>/dev/null | wc -l | tr -d ' ')
A0=$(ls Data/amrfinder_output/*.tsv 2>/dev/null | wc -l | tr -d ' ')

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

while true; do
    D=$(ls Data/genomes_full/*.fna 2>/dev/null | wc -l | tr -d ' ')
    A=$(ls Data/amrfinder_output/*.tsv 2>/dev/null | wc -l | tr -d ' ')
    FAILS=$(cat Data/genomes_full/download.log Data/amrfinder_output/run.log 2>/dev/null | grep -c FAILED)
    clear
    echo "Genome features: live progress   $(date '+%H:%M:%S')   (Ctrl+C to exit)"
    echo
    printf 'Download     %s %5d / %d  %3d%%  (%s)\n' "$(bar "$D" "$TOTAL")" "$D" "$TOTAL" $(( D * 100 / TOTAL )) "$(status download_genomes.py)"
    echo "             $(eta "$D" "$D0" "$TOTAL")   disk $(du -sh Data/genomes_full 2>/dev/null | cut -f1)"
    echo
    printf 'AMRFinder    %s %5d / %d  %3d%%  (%s)\n' "$(bar "$A" "$TOTAL")" "$A" "$TOTAL" $(( A * 100 / TOTAL )) "$(status run_amrfinder.py)"
    echo "             $(eta "$A" "$A0" "$TOTAL")"
    echo
    echo "Failures so far: $FAILS"
    echo
    echo "Latest download log:"
    tail -3 Data/genomes_full/download.log 2>/dev/null | sed 's/^/  /'
    echo "Latest AMRFinder log:"
    tail -3 Data/amrfinder_output/run.log 2>/dev/null | sed 's/^/  /'
    sleep 5
done
