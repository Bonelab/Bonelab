# ImageFilter

All four `blImageFilter` subcommands accept `.aim`, `.nii`, and `.nii.gz`.
They use shared I/O and print input/output information. `exam` also prints a
histogram. Existing outputs prompt before replacement unless `--overwrite` is
specified. The input file cannot be overwritten in place.

## Reduce

```sh
blImageFilter reduce vertebra.aim --factor 2
blImageFilter reduce vertebra.nii.gz --factor 3
```

These produce `vertebra_R02.aim` and `vertebra_R03.nii.gz`. The input format is
retained. The factor must be an integer >= 2 and cannot exceed any dimension.
Every non-overlapping N×N×N block becomes one voxel:

- Char (signed or unsigned 8-bit): majority vote. Values must be zero plus at
  most one positive foreground value in 1–127. That foreground value is retained.
  A tied vote becomes background. Multiple foreground labels are rejected.
- Signed short (16-bit): arithmetic mean, rounded to the nearest integer.
  Exact half-way values round to the even integer. Accumulation uses 64-bit
  integers to avoid short-integer overflow. Short data is averaged even if all
  values happen to lie within 0–127.

Other scalar types are rejected by `reduce`. Scalar encoding is preserved.
Dimensions not divisible by N are trimmed at their upper boundaries; the command
prints the number trimmed on each axis. No partial blocks or padding are used.

Output spacing is N times input spacing. The requested first output voxel center
is the center of the first block: input first-voxel center plus (N−1)/2 input
voxels along each axis. NIfTI qform/sform shifts and orientations, QFac, and
intensity scaling are preserved.

**AIM position limitation:** AIM stores position in whole output voxels. A
block-center shift may therefore be rounded by the AIM writer. The command warns
when the requested position is not representable, records the requested origin
in the AIM processing log, and prints the actual stored geometry after writing.
For exact block-center alignment, reduce a NIfTI image.

## Threshold

```sh
blImageFilter thres vertebra.aim threshold.aim --range 100 127
```

Keep original values inside the inclusive range and replace other values with
zero. Negative bounds are allowed. The default range is 0–10. The scalar type
and spatial geometry are retained.

## Subvolume

```sh
blImageFilter subvol vertebra.aim crop.aim \
  --voi 10 49 20 59 30 69
```

The six indices are inclusive XMIN XMAX YMIN YMAX ZMIN ZMAX. They must lie inside
the input extent. Output indices start at zero, with spatial metadata shifted
so the retained voxels remain at their original physical locations.

## Examine

```sh
blImageFilter exam vertebra.aim
```

## Format-specific metadata

AIM-to-AIM operations preserve the processing log and append the operation.
NIfTI-to-NIfTI operations preserve qform, sform, slice ordering, and intensity
scaling. `thres` and `subvol` select output format by extension; conversion to AIM
is rejected if it would lose unsupported scalar encoding, nonidentity NIfTI
orientation, or intensity scaling. Only three-dimensional scalar images are
supported.

```sh
python -m unittest tests.cli.test_ImageFilter -v
```
