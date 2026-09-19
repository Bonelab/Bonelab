# Rapid prototype model generation

`blRapidPrototypeModelGenerator` prepares a segmented AIM for subsequent STL
conversion with `blRapidPrototype img2stl`. Activate the Bonelab environment and
run `pip install -e .` after adding the new console entry point. Alternatively,
use `python -m bonelab.cli.RapidPrototypeModelGenerator` directly.

## Place a primitive

```sh
blRapidPrototypeModelGenerator visualize input.aim --primitive cube --dimension 100 --transform_output placement.txt
```

The viewer starts in camera mode. The primitive starts at the centroid of all
positive voxels. Press `a` for
primitive controls (left drag rotates; middle or shift-left drag translates),
`c` for camera controls, `u` to save the complete placement, and `q` to save
the placement and quit. Quitting with `q` uses the same overwrite rules as `u`.
Use `--overwrite` to permit replacing an existing transform. Scaling is disabled.
Omit the primitive and dimension to view only the AIM.

Choose `sphere` instead of `cube` for a spherical cutout. Dimension is the cube
edge length or sphere diameter in voxels. With anisotropic spacing the displayed
physical shape is correspondingly stretched. Transform translations are in AIM
physical coordinates. Transforms use the same two-line header and 4x4 matrix
format as RapidPrototype. Invertible affine transforms are accepted, including
the anisotropic principal-axis mapping.

## Generate the output

```sh
blRapidPrototypeModelGenerator apply input.aim output.aim --primitive cube --dimension 100 --transform_file placement.txt --close 2 --erode 5 --buffer 8
```

Add `--visualize` to `apply` to preview the resulting AIM with camera controls
before saving. Close the viewer or press `q` to continue writing the output.
Press `x` to close the preview and cancel without writing; an existing output
file is preserved even when `--overwrite` is set.
The preview shows the processed image without a primitive overlay.

Without a transform, placement defaults to the foreground centroid. Use
`--relative_to_centroid X Y Z` for an offset in image-axis voxel coordinates, or
`--position_at_centroid` to select the default explicitly. These placement
options are mutually exclusive. Supply the same primitive type and dimension
used for visualization; a transform file stores only placement.

The primitive interior becomes zero. Its surrounding buffer preserves original
values, including zeros. Beyond the buffer, enclosed background cavities are
filled, the body is eroded, and the original foreground is restored. Newly
filled voxels have value 127. Output size, spacing, and spatial placement match
the input; operations are clipped to the input grid.

Closing defaults to 0 (disabled), erosion to 5, and buffer thickness to 8 (minimum
1). All are integer radii in voxels and use Euclidean ball morphology, so cube
buffers have rounded corners. Cube rasterization uses half-open bounds at voxel
centers; a grid-aligned cube of integer dimension D contains D voxels per axis.
Spheres include voxel centers on their boundary.

Inputs must contain integer values 0–127 and at least one positive voxel. Zero
is background. This validates the expected segmentation convention, but cannot
distinguish a grayscale image that happens to use the same range.

Background labelling uses six-neighbor connectivity. Component counts, sizes,
and boundary contact are reported. A warning is emitted for zero or one
background component, a largest component less than twice the second-largest,
or a largest component that does not touch the image boundary. These are
heuristics, not proof that all pores were separated. Increase `--close` and
inspect the result if internal pores remain connected to the exterior.

Output cannot replace the input itself. Other existing outputs require
`--overwrite`. Processing parameters and the resolved transform are appended
to the input processing log.

## Validation

```sh
python -m unittest tests.cli.test_RapidPrototypeModelGenerator -v
```

Numerical tests need NumPy and SciPy; generated AIM integration tests additionally
need vtkbone. Desktop visualization needs a working OpenGL context. Large AIMs
can expand to hundreds of millions of voxels despite small compressed files;
morphology uses overlapping slabs and the buffer uses a cropped region to
reduce temporary memory, but full-volume component labels are still required.

## Principal-axis placement

Add `--principal_axes` to either `visualize` or `apply` to align the primitive
with the foreground's first, second, and third principal axes, ordered by
decreasing variance. PCA uses voxel coordinates and equal weight for all
positive voxels. With this option, `--relative_to_centroid X Y Z` specifies
voxel-coordinate offsets along those principal axes. Without an offset, the
primitive is centered at the foreground centroid.

```sh
blRapidPrototypeModelGenerator visualize vertebra.aim \
  --primitive cube --dimension 500 \
  --principal_axes --relative_to_centroid 250 -250 250 \
  --transform_output vertebra_xform.txt --overwrite
```

Axis signs are chosen consistently from their largest image-axis components,
with the third axis adjusted to keep the frame right-handed. Near-equal
variances trigger an ambiguity warning; axes are geometric, not anatomical.

For anisotropic spacing S and voxel-space rotation R, the physical transform
uses S R S^-1. The same mapping is used for rendering and cutting. Exported
transforms include this alignment and the offset; pass the transform to `apply`
without `--principal_axes`. Those two options cannot be combined. Interactive
rotation still operates in physical space, and its final placement is exported.

When principal-axis placement is enabled, visualization and the output preview
show unlabeled arrows at the original model centroid: first (red), second
(green), and third (blue). Lengths are proportional to the square roots of the
PCA variances, with the longest physical arrow equal to half the diagonal of
the foreground bounding box (including voxel extents). They remain fixed when
the primitive moves. Axes are orthogonal in voxel
coordinates; anisotropic spacing can make their physical display nonorthogonal,
consistent with the primitive alignment and offset directions.

## Foreground fragment removal

After assembling the cutout, `apply` keeps only the largest connected foreground
component before previewing or writing. `--remove_fragments` is on by default;
use `--no-remove_fragments` to retain all components. Connectivity includes face,
edge, and corner neighbors (26-connected). Retained voxel labels are unchanged.
This final cleanup can remove disconnected original foreground in the buffer.
The terminal reports the number of fragments and voxels removed.
