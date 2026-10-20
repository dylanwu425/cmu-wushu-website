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

                                                      x     y     w     h   ceiling  sharpen  gamma
  tier-10.jpg    mid-autumn-2025/PXL_20251001_231714393.jpg   850, 1285,  800, 1000   0.86     0.70     1.0
  tier-25.jpg    ds-2026/wushu-31.jpg                        1767,  714,  940, 1175   1.0      0.35     1.0
  tier-100.jpg   penguins-2026/DSCF6131.JPG                   613, 1879, 1680, 2100   1.0      0        0.92

Gamma below 1 lifts the midtones, and it is there to make the four print as
one run. Measured on the rendered cards, the photo areas sat at 159 / 162 /
143 / 140 out of 255 and the two right-hand cards read as a darker pair; the
$50's lift lives in its own builder and the $100's is above, which brings them
to 151 and 144.

tier-50.jpg is not a crop at all. It is one figure made of two people: a
sister on the left of the frame and her brother on the right, joined down the
middle of the face. Both halves come from the same frame of the same group
doing the same move -- penguins-2026/DSCF6013.JPG -- which is why the join
reads as one person rather than as two: she has an arm raised and he has an
arm extended, so the composite comes out as a complete stance.

  half     crop box in the source     eye spacing   scale
  left     2069, 1266,  608, 1496       31 px        1.000
  right    2921,  978,  816, 2006       36 px        0.861

He was standing closer to the camera, so his half is scaled by 0.861 until the
two faces measure the same. The two eye lines are put on the same row, 225px
down the finished file, and the halves cross-fade over ten pixels at x=360.
Contrast 1.18, gamma 0.87, no sharpening -- that frame is sharp already.

Scaling his half to match the faces is a deliberate choice and it has a cost:
his arm and sleeve come out a little smaller than hers. The alternative, both
halves at their own scale, gives a better body and a face that is wider on one
side than the other. The club chose the matched faces.

The alt text has to say what this is. A composite of two real people described
as "a club member" would be a small lie on a page asking for money.

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
ribbon lies across the top of the picture, covering its top 9.8% on a desktop
and 7.3% on a phone. A crop whose subject's head sits near the top edge gets
that head cut in half by the ribbon. This one puts the face 34% down the
frame, which is a tenth lower than the other three -- and that is the point:
measured against the part of the picture the ribbon leaves visible, it sits at
27%, in line with them. The performer's hair is spiky, so the clearance that
matters is to the hair and not to the forehead: the first real ink in the
middle of the frame starts 13.6% down, which leaves 3.8% of the picture
between the ribbon and the first dreadlock, about 12px on a desktop card.
If you swap this file, check it on the card, not on its own.

If you replace one, keep it 4:5. The CSS box is 4:5 to match, and if the two
disagree, object-fit: cover crops the difference out of the middle of the
picture -- which is where the person is.

These are photographs of real members. Before the page goes public, check that
the people in them are happy to appear on a fundraising page.
