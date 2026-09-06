"""
Sanity-check plot for smr_neutronics_dataset.csv: k-effective vs. control
rod height, sliced two ways.

Panel 1: enrichment varies (0.03, 0.045, 0.07), pitch held at baseline (1.26)
Panel 2: pitch varies (1.10, 1.26, 1.42), enrichment held at baseline (0.045)

What a healthy result looks like:
  - Each curve should be smoothly monotonic decreasing as rod height
    increases from 0 (fully inserted) toward 60 (fully withdrawn) is
    WRONG -- higher rod height means MORE withdrawn, i.e. LESS absorber
    in the channel, so k-eff should INCREASE with rod height. If your
    curves decrease instead, that's a sign the insertion convention got
    flipped somewhere -- worth checking before trusting the dataset.
  - Curves should not cross each other in panel 1: higher enrichment
    should sit above lower enrichment at every rod height.
  - Curves should not cross each other in panel 2: wider pitch (more
    moderator) should generally sit above tighter pitch, for this
    under-moderated regime.
  - Error bars should be small relative to the spacing between curves --
    if they're comparable, the enrichment/pitch separation you saw in the
    Day 51 sanity check might not hold at every rod height in this grid.

Run with:
    python plot_sweep_results.py
(In Colab, plots render inline automatically.)
"""
import pandas as pd
import matplotlib.pyplot as plt

CSV_PATH = "/content/drive/MyDrive/SMR-AI-DigitalTwin/smr_neutronics_dataset.csv"
# Adjust the path above if your CSV lives somewhere else.

df = pd.read_csv(CSV_PATH)
print(f"Loaded {len(df)} rows.")
print(df.describe())

BASELINE_PITCH = 1.26
BASELINE_ENRICHMENT = 0.045

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

# --- Panel 1: vary enrichment, pitch fixed at baseline ---
subset1 = df[df["pin_pitch_cm"] == BASELINE_PITCH]
for enrichment, group in subset1.groupby("enrichment"):
    group = group.sort_values("control_rod_height_cm")
    ax1.errorbar(
        group["control_rod_height_cm"],
        group["k_effective_mean"],
        yerr=group["k_effective_std"],
        marker="o",
        capsize=3,
        label=f"enrichment={enrichment}",
    )
ax1.set_xlabel("Control rod height (cm) -- 0=inserted, 60=withdrawn")
ax1.set_ylabel("k-effective")
ax1.set_title(f"k-eff vs. rod height by enrichment (pitch={BASELINE_PITCH} cm)")
ax1.legend()
ax1.grid(alpha=0.3)

# --- Panel 2: vary pitch, enrichment fixed at baseline ---
subset2 = df[df["enrichment"] == BASELINE_ENRICHMENT]
for pitch, group in subset2.groupby("pin_pitch_cm"):
    group = group.sort_values("control_rod_height_cm")
    ax2.errorbar(
        group["control_rod_height_cm"],
        group["k_effective_mean"],
        yerr=group["k_effective_std"],
        marker="o",
        capsize=3,
        label=f"pitch={pitch} cm",
    )
ax2.set_xlabel("Control rod height (cm) -- 0=inserted, 60=withdrawn")
ax2.set_ylabel("k-effective")
ax2.set_title(f"k-eff vs. rod height by pitch (enrichment={BASELINE_ENRICHMENT})")
ax2.legend()
ax2.grid(alpha=0.3)

plt.tight_layout()
plt.savefig("/content/drive/MyDrive/SMR-AI-DigitalTwin/sweep_sanity_plot.png", dpi=150)
plt.show()

print("\nSaved plot to sweep_sanity_plot.png in your project folder.")
