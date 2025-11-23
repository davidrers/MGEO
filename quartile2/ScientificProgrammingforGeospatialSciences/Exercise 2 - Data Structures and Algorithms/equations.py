import math

def calculate_schawarzschild_radius(mass_kg):

    G = 6.67e-11  # Gravitational constant
    c = 299792458    # Speed of light in m/s

    return (2 * G * mass_kg) / (c ** 2)

def solve_equation(x):

    if x <= -1:
        raise ValueError("x must be greater than -1.")
    
    num = math.exp(x) * math.sin(x) + math.sqrt(x**2 + 1)
    den = math.log(x + 1)
    
    return num / den