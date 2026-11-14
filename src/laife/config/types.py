"""Type aliases."""

# World pixels. A rectangle is a Position (its top-left corner) and a Size;
# y grows South. A player's position is its centre when drawn.

Left = int
Top = int
Position = tuple[Left, Top]

Width = int
Height = int
Size = tuple[Width, Height]
