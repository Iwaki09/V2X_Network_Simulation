from .scene_parser import Scene

def shape_to_xml(shape_info, material_id):
    """Converts a single shape (building or vehicle) to a Mitsuba XML string."""
    shape_type = "cube"
    center = shape_info['position']
    size = shape_info['size']
    
    # Mitsuba's cube is centered at (0,0,0) by default and has a size of 2x2x2.
    # We need to use transformations to place and scale it correctly.
    # 1. Translate to the desired center position.
    # 2. Scale to match the desired size (size is diameter, so we use half-size for scaling).
    transform_xml = f"""
        <transform name="to_world">
            <translate x="{center[0]}" y="{center[1]}" z="{center[2] + size[2]/2}"/>
            <scale x="{size[0]/2}" y="{size[1]/2}" z="{size[2]/2}"/>
        </transform>
    """

    return f"""
    <shape type="{shape_type}" id="{shape_info['id']}">
        {transform_xml}
        <ref id="{material_id}"/>
    </shape>
    """

def material_to_xml(material_id, material_info):
    """Converts a single material to a Mitsuba XML string."""
    mat_type = material_info.get("type", "dielectric")
    if mat_type == "dielectric":
        return f"""
    <bsdf type="dielectric" id="{material_id}">
        <float name="int_ior" value="{material_info.get('int_ior', 1.5)}"/>
        <float name="ext_ior" value="{material_info.get('ext_ior', 1.0)}"/>
    </bsdf>
    """
    elif mat_type == "conductor":
        return f"""
    <bsdf type="conductor" id="{material_id}">
        <string name="material" value="{material_info.get('material', 'Au')}"/>
    </bsdf>
    """
    return ""

def scene_to_mitsuba_xml(scene: Scene) -> str:
    """
    Converts a Scene object into a Mitsuba 3 XML scene description.

    Args:
        scene: The Scene object loaded from JSON.

    Returns:
        A string containing the full XML scene description.
    """
    xml_parts = ['<scene version="3.0.0">']

    # Integrator (we use a simple path tracer)
    xml_parts.append('<integrator type="path"/>')

    # Materials
    for mat_id, mat_info in scene.materials.items():
        xml_parts.append(material_to_xml(mat_id, mat_info))

    # Shapes (Buildings and Vehicles)
    for building in scene.buildings:
        xml_parts.append(shape_to_xml(building, building['material']))
    for vehicle in scene.vehicles:
        xml_parts.append(shape_to_xml(vehicle, vehicle['material']))

    # Floor
    xml_parts.append(f'''
    <shape type="rectangle">
        <transform name="to_world">
            <translate x="{scene.world_size[0]/2}" y="{scene.world_size[1]/2}" z="0"/>
            <scale x="{scene.world_size[0]/2}" y="{scene.world_size[1]/2}" z="1"/>
        </transform>
        <bsdf type="diffuse"/>
    </shape>
    ''')

    xml_parts.append('</scene>')

    return "\n".join(xml_parts)


