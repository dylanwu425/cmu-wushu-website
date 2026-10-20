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
     contrast nudge of 1.18, multiply by the ceiling in the table below, then
     map 0-255 across #1B1A17 (shadows) and #EFE7D8 (highlights) -- the page's
     --ink and --paper.
  5. Save as progressive JPEG, quality 74.

                                                      x     y     w     h   ceiling
  tier-10.jpg    mid-autumn-2025/PXL_20251001_231714393.jpg   850, 1364,  800, 1000   0.86
  tier-25.jpg    ds-2026/wushu-31.jpg                        1767,  714,  940, 1175   1.0
  tier-50.jpg    penguins-2026/DSCF6013.JPG                  1824, 1300, 1103, 1379   1.0
  tier-100.jpg   penguins-2026/DSCF6131.JPG                   613, 1879, 1680, 2100   1.0

The ceiling is step 4's one variable: how close that file's highlights are
allowed to get to paper. tier-10.jpg was shot against a white wall, and mapped
all the way up, its background came out the same colour as the card -- the
picture read as half-printed rather than as a figure standing on paper.
Holding its highlights at 0.86 gives the wall its tone back. Measured, the
near-white share of the band between the subject and the bottom fade went from
13.4% to 0.4%, in line with the other three.

The four are framed to sit as a set: each performer's face lands a quarter of
the way down its frame (18% on the $100, which cannot move -- see below) and
takes up 14-18% of the frame's height, so the four heads line up across the
row at the same size instead of stepping up and down. Tightening the $25 and
$50 to reach that also pushed a bystander off the right edge of each, which
was the other thing making those two read as snapshots.

Every box is 4:5 to within a tenth of a percent and every one is wider than
720px, so each file is a genuine downscale -- none of them is upscaled. The
boxes were chosen by framing 4:5 around a detected face with room left above
the head, which is why nobody is cut off at the forehead and no head sits in
the bottom third of the frame, where the card fades the picture into the paper.

tier-100.jpg has a constraint of its own: it was taken at a hockey game, and a
sponsor's banner hangs just above the crop. Moving this frame up by even 3% of
its height brings the word HIGHMARK across the top of the card. That is why
this one is framed by tightening from a fixed top edge rather than by sliding
the box up like the other three.

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
