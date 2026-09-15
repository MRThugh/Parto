# editor.py
from PIL import Image, ImageEnhance

class EditorEngine:
    def __init__(self):
        self.current_image = None
        self.filepath = None
        self.undo_stack = []
        self.redo_stack = []
        
    def load_image(self, filepath: str):
        """
        Load image path and clean undo/redo history.
        """
        self.filepath = filepath
        with Image.open(filepath) as img:
            self.current_image = img.copy()
        self.undo_stack.clear()
        self.redo_stack.clear()
        
    def save_image(self, filepath: str, img_format=None):
        """
        Save the current processed image state to disk.
        """
        if self.current_image:
            self.current_image.save(filepath, format=img_format)
            self.filepath = filepath
            
    def _commit_state(self):
        """
        Snapshot current state before performing an operation.
        """
        if self.current_image:
            self.undo_stack.append(self.current_image.copy())
            if len(self.undo_stack) > 20:  # Limit history depth to optimize memory
                self.undo_stack.pop(0)
            self.redo_stack.clear()
            
    def undo(self) -> bool:
        if self.undo_stack:
            self.redo_stack.append(self.current_image.copy())
            self.current_image = self.undo_stack.pop()
            return True
        return False
        
    def redo(self) -> bool:
        if self.redo_stack:
            self.undo_stack.append(self.current_image.copy())
            self.current_image = self.redo_stack.pop()
            return True
        return False
        
    def rotate(self, angle: int):
        if self.current_image:
            self._commit_state()
            self.current_image = self.current_image.rotate(angle, expand=True)
            
    def flip_horizontal(self):
        if self.current_image:
            self._commit_state()
            self.current_image = self.current_image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            
    def flip_vertical(self):
        if self.current_image:
            self._commit_state()
            self.current_image = self.current_image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            
    def resize(self, width: int, height: int):
        if self.current_image:
            self._commit_state()
            self.current_image = self.current_image.resize((width, height), Image.Resampling.LANCZOS)
            
    def crop(self, box: tuple):
        if self.current_image:
            self._commit_state()
            self.current_image = self.current_image.crop(box)
            
    def get_adjusted_preview(self, brightness=1.0, contrast=1.0, saturation=1.0) -> Image.Image:
        """
        Produce a real-time preview of adjustments without altering the main state.
        """
        if not self.current_image:
            return None
        img = self.current_image
        if brightness != 1.0:
            img = ImageEnhance.Brightness(img).enhance(brightness)
        if contrast != 1.0:
            img = ImageEnhance.Contrast(img).enhance(contrast)
        if saturation != 1.0:
            img = ImageEnhance.Color(img).enhance(saturation)
        return img
        
    def apply_adjustments(self, brightness=1.0, contrast=1.0, saturation=1.0):
        """
        Commit real-time preview modifications.
        """
        if self.current_image:
            self._commit_state()
            self.current_image = self.get_adjusted_preview(brightness, contrast, saturation)