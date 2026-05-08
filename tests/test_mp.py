import mediapipe as mp
print(dir(mp))
try:
    print("Has solutions?", hasattr(mp, 'solutions'))
    import mediapipe.python.solutions as solutions
    print("Imported solutions directly!")
except Exception as e:
    print(repr(e))
