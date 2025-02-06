#!/usr/bin/env python
from __future__ import annotations

import argparse
import os
import sys

import matplotlib.pyplot as plt

from PIL import Image
from torchvision import transforms


def load_images(image_dir: str):
    """
    Load images from the specified directory with specific extensions.

    Args:
    ----
        image_dir (str): Path to the directory containing images.

    Returns:
    -------
        List[Image.Image]: List of loaded images.
    """
    valid_extensions = ('.png', '.PNG', '.jpg', '.JPG', '.jpeg', '.JPEG')

    images = []
    for filename in os.listdir(image_dir):
        if filename.endswith(valid_extensions):
            try:
                with Image.open(os.path.join(image_dir, filename)) as img:
                    images.append(img.copy())
            except OSError:
                print(f"Error opening {filename}")

    if not images:
        print(f"No valid images found in {image_dir}")
        print("Valid extensions are: .png, .PNG, .jpg, .JPG, .jpeg, .JPEG")
        sys.exit(1)

    return images

def save_transformed_images(images, transform, output_filename="comparison.jpg"):
    """
    Saves all images with their transformed versions.

    Args:
    ----
        images (List[Image.Image]): List of PIL Image objects.
        transform: Transforms to apply to images.
        output_filename (str): Name of the output file.
    """
    n = len(images)
    fig, axs = plt.subplots(n, 2, figsize=(10, 5*n))

    for i, img in enumerate(images):
        # Original image
        axs[i, 0].imshow(img)
        axs[i, 0].set_title(f"Original\nSize: {img.size}")
        axs[i, 0].axis('off')

        # Transform image
        transformed_img = transform(img)

        # Convert tensor to numpy array for plotting
        transformed_img_np = transformed_img.permute(1, 2, 0).numpy()

        # Normalize the image for display
        transformed_img_np = (transformed_img_np - transformed_img_np.min()) / (transformed_img_np.max() - transformed_img_np.min())

        axs[i, 1].imshow(transformed_img_np)
        axs[i, 1].set_title(f"Transformed\nSize: {transformed_img_np.shape}")
        axs[i, 1].axis('off')

    plt.tight_layout()
    plt.savefig(output_filename)
    print(f"Comparison image saved as {output_filename}")

def main(image_directory: str):
    """
    Main function to load images, transform them, and save the comparison.

    Args:
    ----
        image_directory (str): Path to the directory containing images.
    """
    # Define your transform
    data_transform = transforms.Compose([
        transforms.Resize(size=(256, 256), interpolation=transforms.InterpolationMode.BILINEAR),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.ToTensor()
    ])

    # Load images
    images = load_images(image_directory)

    # Save transformed images
    save_transformed_images(images, transform=data_transform, output_filename="comparison.jpg")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transform and compare images from a directory.")
    parser.add_argument("image_directory", help="Path to the directory containing images to transform.")
    args = parser.parse_args()

    main(args.image_directory)
