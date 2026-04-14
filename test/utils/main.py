import os
from PIL import Image


def split_image(image_path, chunks, direction, output_dir):
    img = Image.open(image_path)
    width, height = img.size

    os.makedirs(output_dir, exist_ok=True)

    if direction == "vertical":
        chunk_width = width // chunks

        for i in range(chunks):
            left = i * chunk_width
            right = (i + 1) * chunk_width if i != chunks - 1 else width

            crop = img.crop((left, 0, right, height))
            crop.save(os.path.join(output_dir, f"chunk_{i}.png"))

    elif direction == "horizontal":
        chunk_height = height // chunks

        for i in range(chunks):
            top = i * chunk_height
            bottom = (i + 1) * chunk_height if i != chunks - 1 else height

            crop = img.crop((0, top, width, bottom))
            crop.save(os.path.join(output_dir, f"chunk_{i}.png"))

    else:
        raise ValueError("Direction must be 'vertical' or 'horizontal'")

    print(f"\nSaved {chunks} chunks to '{output_dir}'")


def main():
    print("=== Image Splitter CLI ===\n")

    # Step 1: Image path
    image_path = input("Enter image path: ").strip()
    if not os.path.exists(image_path):
        print("Invalid path.")
        return

    # Step 2: Number of chunks
    try:
        chunks = int(input("Enter number of chunks: "))
        if chunks <= 0:
            raise ValueError
    except ValueError:
        print("Chunks must be a positive integer.")
        return

    # Step 3: Direction
    direction = input("Split direction (vertical/horizontal): ").strip().lower()
    if direction not in ["vertical", "horizontal"]:
        print("Invalid direction.")
        return

    # Step 4: Output directory
    output_dir = input("Output directory (default: output_chunks): ").strip()
    if output_dir == "":
        output_dir = "output_chunks"

    # Run
    split_image(image_path, chunks, direction, output_dir)


if __name__ == "__main__":
    main()