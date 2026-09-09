#!/usr/bin/env python3
"""
Derive real narration-sync offsets from a recorded video's actual scene
cuts, correcting drift in the recording script's logged manifest.json.

Usage:
  1. Detect scene cuts in the rendered video:
       ffmpeg -i raw/output.webm \
         -filter:v "select='gt(scene,0.15)',metadata=print:file=scenecuts.txt" \
         -f null - -v error
       grep pts_time scenecuts.txt \
         | sed -E 's/.*pts_time:([0-9.]+).*/\\1/' > cut_times.txt

  2. python3 sync_offsets.py manifest.json cut_times.txt real_offsets.json

  3. Manually patch any scene sync_offsets.py fell back to the raw
     manifest value for (no nearby cluster found) — see
     references/narration-sync.md step 3 for the binary-search method.
"""
import json
import sys


def cluster(cuts, gap=1.5):
    cuts = sorted(cuts)
    clusters = []
    for c in cuts:
        if clusters and c - clusters[-1][-1] <= gap:
            clusters[-1].append(c)
        else:
            clusters.append([c])
    return [c[0] for c in clusters]


def main(manifest_path, cut_times_path, out_path,
         search_before=4.0, search_after=9.0):
    manifest = json.load(open(manifest_path))
    cuts = [float(x) for x in open(cut_times_path) if x.strip()]
    cluster_starts = cluster(cuts)

    real_offsets = {}
    used = -1e9
    unresolved = []
    for m in manifest:
        target = m["offsetMs"] / 1000
        best = None
        for cs in cluster_starts:
            if cs <= used:
                continue
            if target - search_before <= cs <= target + search_after:
                if best is None or abs(cs - target) < abs(best - target):
                    best = cs
        if best is None:
            best = target
            unresolved.append(m["id"])
        real_offsets[m["id"]] = round(best, 2)
        used = best

    json.dump(real_offsets, open(out_path, "w"), indent=2)
    print(json.dumps(real_offsets, indent=2))
    if unresolved:
        print(
            f"\n[!] No detected cut matched for: {', '.join(unresolved)} "
            "-- these fell back to the raw manifest offset. Hand-verify "
            "with binary-search frame extraction (see narration-sync.md "
            "step 3) and patch real_offsets.json manually if needed.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3])
