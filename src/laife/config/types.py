"""Type aliases."""

# Position and Size are compatible with pygame.Rect.
# https://www.pygame.org/docs/ref/rect.html
# Rect((left, top), (width, height)) -> Rect

Left = int
Top = int
Position = tuple[Left, Top]

Width = int
Height = int
Size = tuple[Width, Height]
