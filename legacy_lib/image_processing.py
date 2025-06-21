from PIL import Image

def compress_png(file_path, output_path, new_width=150, to_8_bit=True):
    try:
        img = Image.open(file_path)

        width, height = img.size
        new_height = int((new_width / width) * height)
        img = img.resize((new_width, new_height))

        if to_8_bit:
            img = img.convert("P")

        img.save(output_path, format="PNG", optimize=True)
        return output_path

    except Exception as e:
        print(f"Failed to compress {file_path}: {e}")
        raise

