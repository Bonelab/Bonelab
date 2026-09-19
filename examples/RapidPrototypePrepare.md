# Rapid prototype preparation

`blRapidPrototypePrepare` replaces `blRapidPrototypeModelGenerator`. The workflow
is **view → fill → cut/add**. Reinstall the editable package with `pip install -e .`
to register the renamed executable, or run
`python -m bonelab.cli.RapidPrototypePrepare` directly in the Bonelab environment.
There are no aliases for the previous command or subcommand names.

## Plan with view

```sh
blRapidPrototypePrepare view vertebra.aim \
  --primitive box 300 400 500 \
  --position principal_axes 250 -250 250 \
  --transform_output vertebra_xform.txt --overwrite
```

The viewer starts in camera mode. Press `a` for primitive controls (left drag
rotates; middle or shift-left drag translates), and `c` for camera controls.
Press `u` to save the complete transform, or `q` to save and quit. Press `x`
to exit without writing any files; anything already saved with `u` remains unchanged. Existing
transform files require `--overwrite`. Closing the window without `q` does not
save automatically. A suggested `cut` command is printed on exit.

To inspect a model without a primitive:

```sh
blRapidPrototypePrepare view vertebra_crop.aim
```

## Fill once

```sh
blRapidPrototypePrepare fill vertebra.aim vertebra_filled.aim \
  --close 10 --erode 6 --visualize --overwrite
```

`fill` closes the foreground, labels the zero-valued background, fills all but
the largest background component, erodes the filled body, and restores original
foreground values. New filled voxels have value 127. Closing defaults to **10**
and erosion to **6** voxels. Both use Euclidean ball morphology in voxel
coordinates; zero disables the corresponding operation.

Background labelling uses six-neighbor connectivity. Counts, sizes, and boundary
contact are reported. A warning is emitted for zero or one background component,
a largest component less than twice the second-largest, or a largest component
that does not touch the image boundary. These diagnostics cannot prove all pores
are separated. Increase `--close` and inspect if pores remain open to the exterior.
`fill` has no primitive, position, or transform options.

## Cut

```sh
blRapidPrototypePrepare cut vertebra_filled.aim vertebra_crop.aim \
  --primitive box 300 400 500 \
  --transform_file vertebra_xform.txt \
  --detail vertebra.aim 20 --visualize --overwrite
```

An ordinary cut sets the primitive interior to zero and preserves all other
input values. It does not fill or erode the model.

Optional `--detail REFERENCE_AIM BUFFER` restores the reference values (including
zeros) within BUFFER voxels outside the cut. The interior stays zero; beyond the
buffer the input is unchanged. BUFFER is a positive integer, and dilation has
rounded corners. The reference must match input dimensions, spacing, and physical
placement; it is never silently resampled. Expanded images from `add` therefore
need a reference on the same expanded grid before using `--detail`.

Cut output retains the input grid. If the primitive extends outside it, a clear
`WARNING: PRIMITIVE CLIPPED AT IMAGE BOUNDS` explains why the cutout may be smaller.

## Save the extracted piece

```sh
blRapidPrototypePrepare cut vertebra_filled.aim vertebra_remaining.aim \
  --primitive box 300 400 500 \
  --transform_file vertebra_xform.txt \
  --detail vertebra.aim 20 \
  --cutout_output vertebra_cutout.aim --visualize --overwrite
```

Without `--detail`, the remaining model and cutout are complementary: the
cutout keeps input values inside the primitive and is zero elsewhere.
With `--detail`, the cutout restores reference values (including zeros) in the
inner buffer between the primitive and its erosion by BUFFER voxels. Its deeper
interior retains the input values. The remaining model uses the existing outer
buffer. If erosion leaves no core, all cutout material uses reference detail;
this is reported. Empty cutouts are also reported and saved as empty AIMs.

Both outputs keep the input grid, spacing, and physical origin. `--overwrite`
applies to both files; neither may replace the input, reference, or each other.
Both paths are checked before processing. `--remove_fragments`, when enabled,
cleans each piece independently, so the pieces may no longer reconstruct the
original image. Files are staged before replacing existing outputs.

With `--visualize`, the remaining model appears on the left and the cutout on
the right. Both views share a camera. `q` or closing the window writes both;
`x` cancels both without changing either output file.

## Add

```sh
blRapidPrototypePrepare add vertebra_crop.aim vertebra_added.aim \
  --primitive cylinder 100 300 --position centroid 0 0 0 \
  --visualize --overwrite
```

`add` writes 127 to every voxel inside the primitive and preserves input values
elsewhere. Image bounds expand on any side needed to contain the primitive.
Spacing is preserved and the origin is adjusted so existing anatomy stays at
its original physical coordinates. Newly allocated background is zero. A
primitive may be disconnected from the original model. `clean_fit` is not implemented.

## Shared primitive and placement options

| Shape | Syntax | Positive integer voxel dimensions |
| --- | --- | --- |
| Sphere | `--primitive sphere 100` | Diameter |
| Cube | `--primitive cube 100` | Edge length |
| Box | `--primitive box 100 200 300` | Local X, Y, Z edge lengths |
| Cylinder | `--primitive cylinder 100 300` | Diameter, length along local Z |

All primitives are centered at their local origin. Put input/output filenames
before the primitive option. `view`, `cut`, and `add` use the same definitions.
Voxel centers determine membership. Boxes use half-open bounds on each axis;
cylinders use half-open length bounds and include radial boundary points.
Spheres include their boundary points.

- `--position origin X Y Z`: offsets from the first input voxel along image axes.
- `--position centroid X Y Z`: image-axis offsets from the foreground centroid.
- `--position principal_axes X Y Z`: alignment and offsets along the model's
  first, second, and third principal axes, anchored at the foreground centroid.

Default placement is `origin 0 0 0`, regardless of whether that voxel is
foreground. Offsets can be negative or fractional. `--transform_file` loads a
complete placement instead of `--position`; they are mutually exclusive.

PCA uses voxel coordinates and equal weights for all positive voxels, ordered
by decreasing variance. Signs are chosen consistently with a right-handed
orientation; near-equal variances trigger an ambiguity warning. The viewer
shows unlabeled red/green/blue arrows at the model centroid. Lengths follow the
square roots of the variances, with the longest equal to half the foreground
bounds diagonal. With anisotropic spacing, physically displayed axes may not
be orthogonal, consistent with voxel-space placement.

For spacing S and voxel rotation R, the physical transform uses S R S^-1.
Saved transforms include initial placement and subsequent interactive movement
at full double precision. Use the same primitive sizes and input coordinate
frame when reloading. All four shapes have geometry and voxel-mask round-trip
tests, including anisotropic spacing and interactive actor adjustments.

## Output and validation

`fill`, `cut`, and `add` support `--visualize` to preview before writing. Press
`q` or close the window to write; `x` cancels and preserves any existing output.
`--remove_fragments` is **off by default**. Enabling it keeps only the largest
26-connected foreground component after processing, before preview or writing.
Retained labels are unchanged. This can remove intentional detached additions.

Outputs cannot replace their input or detail-reference AIM. Other existing
outputs require `--overwrite`. Parameters and resolved transforms are appended
to the processing log. Inputs are checked for integer values 0–127 and at least
one positive voxel. These checks enforce the segmentation convention but cannot
prove an image was segmented. Each read prints AIM information; each rendered
AIM reports its triangle count.

```sh
python -m unittest tests.cli.test_RapidPrototypePrepare -v
```

Numerical tests require NumPy/SciPy, AIM tests require vtkbone, and actual
interactive viewing requires a working OpenGL context. Large compressed AIMs
can expand to hundreds of millions of voxels; component labels still require
full-volume memory even though morphology uses slabs.
