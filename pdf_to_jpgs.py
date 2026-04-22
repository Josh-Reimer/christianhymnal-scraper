from pdf2image import convert_from_path

images = convert_from_path("pdfs/christianhymnal-1.pdf")

for i in range(len(images)):
    images[i].save(f"songscroller/img/songscroller{i}","JPEG")