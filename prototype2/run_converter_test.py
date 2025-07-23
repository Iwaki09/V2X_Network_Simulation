import os
from src.scene_parser import load_scene
from src.mitsuba_converter import scene_to_mitsuba_xml

def main():
    """
    Loads a scene, converts it to Mitsuba XML, and saves the output.
    """
    print("--- Testing Mitsuba XML Conversion ---")
    
    # Paths are relative to the project root where this script is run
    scene_file = 'scene.json'
    output_file = 'generated_scene.xml'

    print(f"Loading scene from: {scene_file}")
    scene = load_scene(scene_file)
    
    print("Converting scene to Mitsuba XML...")
    mitsuba_xml_content = scene_to_mitsuba_xml(scene)

    with open(output_file, 'w') as f:
        f.write(mitsuba_xml_content)

    print(f"Successfully converted scene and saved to: {output_file}")
    print("You can now inspect the XML file.")

if __name__ == "__main__":
    main()
