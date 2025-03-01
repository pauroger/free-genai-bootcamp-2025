# Streamlit Custom Theme

A reusable custom theme for Streamlit applications based on the brand color
(#90cdec). This theme provides consistent styling across your applications with
customizable components.

## 🎨 Features

- **Global Theme**: Apply a consistent look and feel across all your Streamlit apps
- **Color Customization**: Easy customization of the primary color
- **Custom Components**: Pre-styled cards, info boxes, and highlights
- **Helper Classes**: CSS utility classes for quick styling
- **Responsive Design**: Optimized for different screen sizes

## 📝 Usage

### Basic Usage

```python
import streamlit as st
from streamlit_theme import apply_custom_theme

# Apply the theme at the start of your app
apply_custom_theme()  # Uses default color #90cdec

# Rest of your Streamlit app code
st.title("My App with Custom Theme")
```

### Custom Primary Color

```python
# Apply with a custom color
apply_custom_theme(primary_color="#4287f5")
```

### Using Theme Components

```python
import streamlit as st
from streamlit_theme import (
    apply_custom_theme, 
    card, 
    highlight, 
    info_box, 
    success_box, 
    warning_box, 
    error_box
)

# Apply theme
apply_custom_theme()

# Use a card with title
card(
    "This is content inside a styled card component.",
    title="Card Title"
)

# Use a highlight container
highlight("This text is highlighted for emphasis.")

# Use alert boxes
info_box("This is an information message.")
success_box("This operation was successful!")
warning_box("Warning: Please check your input.")
error_box("Error: Something went wrong.")
```

### Using CSS Helper Classes

The theme includes several CSS helper classes that you can use with the `st.markdown` function:

```python
st.markdown('<div class="card p-3 shadow">Custom card with padding and shadow</div>', unsafe_allow_html=True)

st.markdown('<p class="text-primary">This text uses the primary color</p>', unsafe_allow_html=True)

st.markdown('<div class="bg-primary-light rounded p-3 m-3">Styled container</div>', unsafe_allow_html=True)
```

## 🔧 Customization

1. Add more custom components
2. Adjust color schemes and styles
3. Create additional helper classes
4. Add animations or transitions

## 📋 Available Components

- **`apply_custom_theme(primary_color)`**: Main function to apply the theme
- **`card(content, title)`**: Display content in a styled card
- **`highlight(content)`**: Display content in a highlighted container
- **`info_box(content, icon)`**: Display an info alert box
- **`success_box(content, icon)`**: Display a success alert box
- **`warning_box(content, icon)`**: Display a warning alert box
- **`error_box(content, icon)`**: Display an error alert box

## 📌 CSS Helper Classes

- Text alignment: `text-center`
- Text colors: `text-primary`, `text-secondary`
- Borders: `border-primary`, `rounded`
- Backgrounds: `bg-primary-light`
- Spacing: `p-3` (padding), `m-3` (margin)
- Effects: `shadow`, `animate-fadeIn`

## 🔄 Integration with Existing Apps

To integrate this theme with your existing Streamlit apps:

1. Import the theme module
2. Call `apply_custom_theme()` at the beginning of your app
3. Replace standard elements with themed components where appropriate
4. Use CSS helper classes for additional styling

## 📚 Best Practices

- Apply the theme at the very beginning of your app
- Use consistent spacing and layout patterns
- Combine themed components with standard Streamlit elements
- Maintain a consistent color scheme across your application
