def drawrect(drawcontext, xy, outline=None, width=1):
    (x1, y1), (x2, y2) = xy
    offset = 1
    for i in range(0, width):
        drawcontext.rectangle(((x1, y1), (x2, y2)), outline=outline)
        x1 = x1 - offset
        y1 = y1 + offset
        x2 = x2 + offset
        y2 = y2 - offset


def ShowBoundingBox(draw, box, width, height, boxColor, seq):
    left = width * box['Left']
    top = height * box['Top']
    drawrect(draw, [(left, top), (left + (width * box['Width']),
                                  top + (height * box['Height']))], outline=boxColor, width=5)

    text_pos = (left, top - 30)
    draw.text(text_pos, f'Figure-{seq}', "red", font_size=14)


def image_crop(image, box, local_image_path):
    width, height = image.size
    left = width * box['Left']
    top = height * box['Top']
    crop_img = image.crop((left, top, left + width * box['Width'], top + height * box['Height']))
    crop_img.save(local_image_path, format="PNG")
    return local_image_path
