# Keep package initialization deliberately small. Importing every UI component
# here made one missing optional helper prevent the entire Streamlit app from
# starting. Pages should import the components they actually use.
from ui.styles import inject_css

__all__ = ["inject_css"]
