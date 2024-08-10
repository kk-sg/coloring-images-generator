import streamlit as st
import os
import datetime
from openai import OpenAI
import requests
from typing import List
import zipfile
import io
from PIL import Image


def get_api_key() -> str:
    """
    Retrieves the OpenAI API key from the user via a password input field.

    Returns:
        str: The user-provided OpenAI API key.
    """
    return st.text_input(
        "Enter your OpenAI API key (don't worry, we won't peek)",
        type='password',
        key="api_key_input"
    )


def generate_themes(client) -> list[str]:
    """
    Generates a list of themes for children's coloring book pages using the OpenAI client.

    If the themes are already generated and stored in the session state, returns the cached result.
    Otherwise, sends a prompt to the OpenAI model to generate the themes and stores them in the session state.

    Args:
        client: The OpenAI client instance.

    Returns:
        list[str]: A list of themes for children's coloring book pages.
    """
    if 'themes' not in st.session_state:
        prompt = "Generate a list of 10 suitable themes for children's coloring book pages."
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        themes = [
            theme.strip('- ')
            for theme in response.choices[0].message.content.strip().split('\n')
        ]
        st.session_state.themes = themes
    return st.session_state.themes


def image_prompt(theme: str) -> str:
    """
    Generates a prompt for creating a children's coloring book page image based on the given theme.

    Args:
        theme: The theme for the coloring book page.

    Returns:
        str: A prompt for creating a children's coloring book page image.
    """
    prompt = f"""
    Create a black and white line drawing suitable for a children's coloring book page.
    The image should feature a simple, cute cartoon-style in a balanced composition.
    The theme is '{theme}'.
    Ensure the design has clear, bold lines and simple shapes that will look good when scaled up for printing on A4 paper.
    Avoid intricate details that may be lost when printed.
    """
    return prompt


def generate_image(client, prompt: str) -> str:
    """
    Generates an image using the DALL-E model based on the given prompt.

    Args:
        client: The OpenAI client instance.
        prompt: The prompt for generating the image.

    Returns:
        str: The URL of the generated image.
    """
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1
    )
    if response.data:
        return response.data[0].url
    else:
        raise ValueError("No image generated")


def save_image(url: str, folder_name: str, image_number: int) -> str | None:
    """
    Saves an image from a URL to a local file.

    Args:
        url: The URL of the image to save.
        folder_name: The name of the folder to save the image in.
        image_number: The number to use in the filename.

    Returns:
        str | None: The path to the saved image file, or None if the image could not be saved.
    """
    os.makedirs(folder_name, exist_ok=True)
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error downloading image: {e}")
        return None

    file_path = os.path.join(
        folder_name, f"generated_image_{image_number}.png")
    try:
        with open(file_path, 'wb') as file:
            file.write(response.content)
    except IOError as e:
        print(f"Error saving image: {e}")
        return None

    return file_path


def create_zip_file(folder_name: str) -> io.BytesIO:
    """
    Creates a ZIP file from the contents of a folder.

    Args:
        folder_name: The name of the folder to zip.

    Returns:
        io.BytesIO: A bytes buffer containing the ZIP file data.
    """
    zip_buffer = io.BytesIO()
    
    # compression parameter to the ZipFile constructor to make it explicit that we're using DEFLATE compression.
    with zipfile.ZipFile(zip_buffer, 'w', compression=zipfile.ZIP_DEFLATED) as zip_file:
        for root, _, files in os.walk(folder_name):
            for file in files:
                file_path = os.path.join(root, file)
                
                # relative_path variable to preserve the directory structure of the files in the ZIP file.
                relative_path = os.path.relpath(file_path, folder_name)
                zip_file.write(file_path, relative_path)
    # reset the buffer's position to the beginning, so that the caller can read the ZIP file data from the start.
    zip_buffer.seek(0)
    return zip_buffer



def main():
    st.title("🪄 AI Coloring Book Generator 🖍️")

    st.markdown("""
    Welcome to the cutest corner of the internet! This Streamlit app is your magical gateway to creating adorable coloring pages that will make children (and let's be honest, adults too) squeal with delight.

    ## 🌟 What's This All About?""")
    
    # Load and display the image
    image = Image.open('./images/magic_garden.png')
    st.image(image, caption='Its magical')

    # Load and display the image
    image = Image.open('./images/super.png')
    st.image(image, caption='Its super')
    
    st.markdown("""
    Ever wished you could summon an army of cute, colorable images with just a few clicks? Well, now you can! Our app uses the power of AI to generate custom coloring book pages faster than you can say "pass the crayons!"

    ## 🚀 Features

    - 🎨 Generate unique coloring pages with various themes
    - 🔢 Choose how many masterpieces you want (up to 10!)
    - 📥 Download your creations as a zip file
    - 🌈 Perfect for rainy days, birthday parties, or when you just need a dose of cuteness

    ## 🔑 Getting Your OpenAI API Key

    Before you can start generating cute images, you'll need an OpenAI API key. Here's how to get one:

    1. Visit [OpenAI's website](https://platform.openai.com/)
    2. Sign up or log in: If you don't have an account, click "Sign up" and create one. If you already have an account, click "Log in".
    3. Navigate to API keys: Once logged in, look for your account name or icon in the top-right corner of the page. Click on it to open a dropdown menu.
    4. Select "Your Profile".
    5. Select "User API keys".
    6. Create a new API key: Look for a button that says "Create new secret key" or "+ New secret key".
    7. Name your key (optional): You may have the option to give your API key a name.
    8. Copy and save your API key: After creating the key, you'll see it displayed once. Make sure to copy it immediately and store it securely, as you won't be able to see it again.
    9. Set up billing: Before you can use your API key, you need to set up billing. Look for a "Billing" or "Payment" section in the account settings or main menu.
    10. Set usage limits (optional): In the billing section, you may be able to set usage limits to control your spending.
    """)

    st.markdown("---")  # This adds a horizontal line for separation

    # Initialize session state for theme if it doesn't exist
    if 'selected_theme' not in st.session_state:
        st.session_state.selected_theme = None

    api_key = get_api_key()
    if api_key:
        client = OpenAI(api_key=api_key)

        # Generate themes only if they don't exist in session state
        if 'themes' not in st.session_state:
            generate_themes(client)

        # Use session state to maintain the selected theme
        selected_theme = st.selectbox("Select a theme", st.session_state.themes, key="theme_selector", index=st.session_state.themes.index(
            st.session_state.selected_theme) if st.session_state.selected_theme in st.session_state.themes else 0)

        # Update session state when a new theme is selected
        if selected_theme != st.session_state.selected_theme:
            st.session_state.selected_theme = selected_theme

        num_images = st.slider("Number of images to generate",
                               min_value=1, max_value=10, value=3, key="num_images_slider")

        st.warning(
            f"You've chosen to generate {num_images} images. Please note that generating more images will increase your API usage and costs.")

        if st.button("Generate Images", key="generate_button"):
            st.write(
                f"Creating images based on '{st.session_state.selected_theme}'")

            folder_name = f"{st.session_state.selected_theme.replace(' ', '_')}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            generated_file_paths = []

            progress_bar = st.progress(0)
            for i in range(num_images):
                generate_image_prompt = image_prompt(
                    st.session_state.selected_theme)
                image_url = generate_image(client, generate_image_prompt)
                file_path = save_image(image_url, folder_name, i + 1)
                generated_file_paths.append(file_path)
                progress_bar.progress((i + 1) / num_images)

            st.write(
                f"Generated {num_images} images for theme: {st.session_state.selected_theme}")
            for file_path in generated_file_paths:
                st.image(file_path)

            zip_buffer = create_zip_file(folder_name)
            st.download_button(
                label="Download Images",
                data=zip_buffer.getvalue(),
                file_name=f"{folder_name}.zip",
                mime="application/zip",
                key="download_button"
            )

            st.info("Note: These images are generated at 1024x1024 pixels. For best print quality on A4 paper, you may need to scale them up slightly using an image editing software.")


if __name__ == "__main__":
    main()
