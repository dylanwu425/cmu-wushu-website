Giving Day tier pictures
========================

The four files here are the pictures on the tier cards. They are not loose
crops: each one is a named region of a full-resolution original that is NOT in
this repository (the originals live in the gallery folders on your computer and
are gitignored for size), cut to 4:5 and printed in the page's two colours.

Rebuild recipe, if one of these ever has to be made again:

  1. Open the source photograph listed below at full resolution.
  2. Crop the box given as x, y, width, height in that file's own pixels.
  3. Resize to 720 x 900.
  4. Duotone it: greyscale, stretch the 1st-99th percentile to full range, a
     contrast nudge of 1.18, then map 0-255 across #1B1A17 (shadows) and
     #EFE7D8 (highlights) -- the page's --ink and --paper.
  5. Save as progressive JPEG, quality 74.

  tier-10.jpg    mid-autumn-2025/PXL_20251001_231714393.jpg    802, 1289, 896, 1119
  tier-25.jpg    ds-2026/wushu-31.jpg                         1710,  810, 1053, 1316
  tier-50.jpg    penguins-2026/DSCF6013.JPG                   1740, 1407, 1269, 1586
  tier-100.jpg   penguins-2026/DSCF6131.JPG                    413, 1879, 2080, 2601

Every box is 4:5 to within a tenth of a percent and every one is wider than
720px, so each file is a genuine downscale -- none of them is upscaled. The
boxes were chosen by framing 4:5 around a detected face with room left above
the head, which is why nobody is cut off at the forehead and no head sits in
the bottom third of the frame, where the card fades the picture into the paper.

tier-10.jpg has one extra constraint: it is the flagged card, and the red
ribbon lies across the top of the picture, covering roughly its top 12%. A
crop whose subject's head sits near the top edge gets that head cut in half by
the ribbon. This one starts the face 22% down the frame for exactly that
reason. If you swap this file, check it on the card, not on its own.

If you replace one, keep it 4:5. The CSS box is 4:5 to match, and if the two
disagree, object-fit: cover crops the difference out of the middle of the
picture -- which is where the person is.

These are photographs of real members. Before the page goes public, check that
the people in them are happy to appear on a fundraising page.
