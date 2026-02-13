import PIL.Image
import os

def resize_image(input_path, output_path, max_width=800):
    try:
        with PIL.Image.open(input_path) as img:
            # Calculate new height to maintain aspect ratio
            width_percent = (max_width / float(img.size[0]))
            h_size = int((float(img.size[1]) * float(width_percent)))
            
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            # Resize
            img = img.resize((max_width, h_size), PIL.Image.Resampling.LANCZOS)
            
            # Save with high quality
            img.save(output_path, quality=90, optimize=True)
            
            print(f"Successfully resized {input_path} to {output_path}")
            print(f"Original size: {os.path.getsize(input_path) / 1024:.2f} KB")
            print(f"New size: {os.path.getsize(output_path) / 1024:.2f} KB")
            
    except Exception as e:
        print(f"Error resizing image: {e}")

if __name__ == "__main__":
    resize_image("profilepc.jpg", "profilepc_optimized.jpg")
